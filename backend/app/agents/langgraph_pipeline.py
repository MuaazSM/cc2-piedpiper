"""
LangGraph State Graph — The formal pipeline engine for Lorri.

Implements the Observe → Reason → Decide → Act → Learn framework
as a LangGraph StateGraph with typed state, tool nodes, agent nodes,
and conditional edges.

This replaces orchestrator.py as the primary pipeline engine.

Pipeline flow:
    validation_node (Observe)
        → [invalid] → END
        → [valid] → compatibility_node (Reason)
            → guardrail_node (Decide)
                → [violated] → compatibility_node (re-Reason)
                → [clear] → solver_node (Act)
                    → [infeasible, retries left] → relaxation_node → solver_node
                    → [infeasible, retries exhausted] → END
                    → [feasible] → simulation_node
                        → insight_node
                            → scenario_rec_node
                                → metrics_node (Learn)
                                    → END

Each node reads from and writes to AgentState — a TypedDict that
carries all data through the pipeline. Nodes only modify the fields
they own, keeping the state clean and traceable.
"""

import time
from typing import TypedDict, List, Dict, Optional, Any, Annotated
from langgraph.graph import StateGraph, END

from backend.app.agents.validation_agent import run_validation
from backend.app.agents.insight_agent import run_insight_analysis
from backend.app.agents.relaxation_agent import run_relaxation_analysis
from backend.app.agents.scenario_agent import run_scenario_analysis
from backend.app.agents.guardrail import run_guardrail
from backend.app.agents.tools.compatibility_scoring_tool import score_shipment_pairs
from backend.app.agents.tools.scenario_simulation_tool import run_all_scenarios
from backend.app.agents.tools.shipment_data_tool import fetch_shipment_data
from backend.app.agents.tools.optimization_tool import run_optimization
from backend.app.agents.tools.outcome_logging_tool import log_outcome, trigger_retraining
from backend.app.optimizer.metrics import compute_full_metrics

# ---------------------------------------------------------------------------
# AgentState — the typed state that flows through the entire graph
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    """
    Central state object passed between all nodes in the graph.

    Every node reads what it needs and writes its output to specific fields.
    No node modifies another node's output — this keeps the data flow
    clean and makes debugging straightforward.

    Fields:
        shipments: raw shipment dicts loaded from the database
        vehicles: raw vehicle dicts loaded from the database
        config: pipeline configuration (run_llm, run_simulation, weights)

        validation_report: output of the Validation Agent (Observe)
        compatibility_scores: ML model output + graph stats (Reason)
        guardrail_result: policy check output (Decide)
        consolidation_plan: solver output with assignments (Act)
        constraint_violations: accumulated violations from guardrail + relaxation
        relaxation: relaxation agent's diagnosis and suggestions
        scenario_results: raw output from 4 simulation scenarios
        scenario_analysis: Agent 4's recommendations and trade-offs
        insights: Agent 2's lane insights, risk flags, narrative
        metrics: before/after operational metrics (Learn)

        retry_count: how many times the solver has been retried after infeasibility
        step_timings: list of {step, status, duration_ms} for pipeline metadata
        error: set if the pipeline terminates early due to a critical failure
    """
    # --- Inputs ---
    shipments: List[Dict]
    vehicles: List[Dict]
    config: Dict

    # --- Observe phase ---
    validation_report: Optional[Dict]

    # --- Reason phase ---
    compatibility_scores: Optional[Dict]

    # --- Decide phase ---
    guardrail_result: Optional[Dict]

    # --- Act phase ---
    consolidation_plan: Optional[Dict]
    constraint_violations: Optional[List[Dict]]
    relaxation: Optional[Dict]

    # --- Simulation + Insights ---
    scenario_results: Optional[List[Dict]]
    scenario_analysis: Optional[Dict]
    insights: Optional[Dict]

    # --- Learn phase ---
    metrics: Optional[Dict]

    # --- Pipeline control ---
    retry_count: int
    step_timings: List[Dict]
    error: Optional[str]


# ---------------------------------------------------------------------------
# Helper: timing wrapper
# ---------------------------------------------------------------------------

def _timed_step(name: str, func, state: AgentState) -> tuple:
    """
    Run a pipeline step function and record its timing.
    Returns (result_dict, timing_dict) so the caller can update state.
    """
    start = time.time()
    try:
        result = func(state)
        duration = (time.time() - start) * 1000
        timing = {"step": name, "status": "completed", "duration_ms": round(duration, 1), "error": None}
        return result, timing
    except Exception as e:
        duration = (time.time() - start) * 1000
        timing = {"step": name, "status": "failed", "duration_ms": round(duration, 1), "error": str(e)}
        return None, timing


# ---------------------------------------------------------------------------
# Node functions — each takes AgentState, returns partial state update
# ---------------------------------------------------------------------------

def shipment_data_node(state: AgentState) -> dict:
    """
    OBSERVE PHASE (Step 0) — Fetch shipment and vehicle data from the database.

    This is the very first node in the pipeline. It loads all data
    from the DB into AgentState so every downstream node has something
    to work with.

    If the DB is empty (no shipments or no vehicles), it sets an error
    message which triggers the conditional edge to skip to END.
    """
    start = time.time()

    try:
        # If data was already provided (e.g. during testing or direct invocation),
        # skip the DB fetch and use what's already in state.
        if state["shipments"] and state["vehicles"]:
            duration = (time.time() - start) * 1000
            timing = {"step": "Shipment Data Tool", "status": "completed", "duration_ms": round(duration, 1), "error": None}
            print(f"[Shipment Data Tool] Using pre-loaded data: {len(state['shipments'])} shipments, {len(state['vehicles'])} vehicles")
            return {
                "step_timings": state["step_timings"] + [timing],
            }

        shipments, vehicles = fetch_shipment_data()

        # Check for empty data — no point running the pipeline on nothing
        if not shipments:
            duration = (time.time() - start) * 1000
            timing = {"step": "Shipment Data Tool", "status": "completed", "duration_ms": round(duration, 1), "error": None}
            return {
                "shipments": [],
                "vehicles": vehicles,
                "error": "No shipments found. Upload shipments first via POST /shipments or POST /dev/seed.",
                "step_timings": state["step_timings"] + [timing],
            }

        if not vehicles:
            duration = (time.time() - start) * 1000
            timing = {"step": "Shipment Data Tool", "status": "completed", "duration_ms": round(duration, 1), "error": None}
            return {
                "shipments": shipments,
                "vehicles": [],
                "error": "No vehicles found. Seed vehicle fleet first via POST /dev/seed.",
                "step_timings": state["step_timings"] + [timing],
            }

        duration = (time.time() - start) * 1000
        timing = {"step": "Shipment Data Tool", "status": "completed", "duration_ms": round(duration, 1), "error": None}

        print(f"[Shipment Data Tool] Loaded {len(shipments)} shipments and {len(vehicles)} vehicles")

        return {
            "shipments": shipments,
            "vehicles": vehicles,
            "step_timings": state["step_timings"] + [timing],
        }

    except Exception as e:
        duration = (time.time() - start) * 1000
        timing = {"step": "Shipment Data Tool", "status": "failed", "duration_ms": round(duration, 1), "error": str(e)}
        return {
            "shipments": [],
            "vehicles": [],
            "error": f"Failed to load data from database: {str(e)}",
            "step_timings": state["step_timings"] + [timing],
        }

def validation_node(state: AgentState) -> dict:
    """
    OBSERVE PHASE — Validate input data quality.

    Runs the Validation Agent against all shipments and vehicles.
    If critical errors are found, sets the error field which triggers
    the conditional edge to END.
    """
    start = time.time()

    report = run_validation(state["shipments"], state["vehicles"])

    duration = (time.time() - start) * 1000
    timing = {"step": "Validation Agent", "status": "completed", "duration_ms": round(duration, 1), "error": None}

    update = {
        "validation_report": report,
        "step_timings": state["step_timings"] + [timing],
    }

    # If validation failed, set error so the router sends us to END
    if not report.get("is_valid", False):
        update["error"] = "Validation failed: critical errors found in input data."

    return update


def compatibility_node(state: AgentState) -> dict:
    """
    REASON PHASE — Score shipment pairs and build compatibility graph.

    Thin wrapper around the Compatibility Scoring Tool. The tool handles
    model lifecycle, pair scoring, rule-based filtering, and graph
    construction. This node just calls it and writes results to AgentState.

    Non-fatal: if the tool fails, the solver can still run without
    compatibility constraints (just less optimal).
    """
    start = time.time()

    try:
        result = score_shipment_pairs(
            shipments=state["shipments"],
            vehicles=state["vehicles"],
            threshold=0.6,
        )

        compatibility = {
            "stats": result["stats"],
            "edges": result["edges"],
            "graph_object": result["graph_object"],
            "model_info": result["model_info"],
        }

        status = "completed"
        error = None

    except Exception as e:
        # ML failure is non-fatal — solver can run without pair constraints
        compatibility = {
            "stats": {},
            "edges": [],
            "graph_object": None,
            "model_info": {"status": "failed", "error": str(e)},
        }
        status = "failed"
        error = str(e)
        print(f"[Compatibility Node] Failed: {e}")

    duration = (time.time() - start) * 1000
    timing = {"step": "ML Compatibility Model", "status": status, "duration_ms": round(duration, 1), "error": error}

    return {
        "compatibility_scores": compatibility,
        "step_timings": state["step_timings"] + [timing],
    }


def guardrail_node(state: AgentState) -> dict:
    """
    DECIDE PHASE — Check compatibility graph against operational policies.

    Runs the Policy Guardrail Tool to catch dangerous pairings that
    the ML model might have approved (hazmat + food, HIGH + LOW priority).

    If CRITICAL violations are found, the edges are removed and the
    filtered graph is stored for the solver. The conditional edge after
    this node decides whether to re-run Reason or proceed to Act.
    """
    start = time.time()

    edges = []
    if state.get("compatibility_scores"):
        edges = state["compatibility_scores"].get("edges", [])

    guardrail_result = run_guardrail(edges, state["shipments"])

    # If critical violations were found, update the compatibility edges
    # with the filtered (clean) set
    if guardrail_result["critical_count"] > 0 and state.get("compatibility_scores"):
        state["compatibility_scores"]["edges"] = guardrail_result["filtered_edges"]

    # Accumulate violations across retries
    existing_violations = state.get("constraint_violations") or []
    new_violations = existing_violations + guardrail_result.get("violations", [])

    duration = (time.time() - start) * 1000
    timing = {"step": "Policy Guardrail", "status": "completed", "duration_ms": round(duration, 1), "error": None}

    return {
        "guardrail_result": guardrail_result,
        "constraint_violations": new_violations,
        "step_timings": state["step_timings"] + [timing],
    }


def solver_node(state: AgentState) -> dict:
    """
    ACT PHASE — Run the OR-Tools solver to build the consolidation plan.

    Thin wrapper around the Optimization Tool. The tool decides whether
    to use MIP (<=50 shipments) or heuristic (>50 shipments), runs the
    solver with the compatibility graph as constraints, and returns
    vehicle-to-shipment assignments.
    """
    start = time.time()

    try:
        # Extract the compatibility graph from the Reason phase.
        # If compatibility scoring failed, graph_object will be None
        # and the solver will treat all pairs as compatible.
        graph_object = None
        compat = state.get("compatibility_scores")
        if compat:
            graph_object = compat.get("graph_object")

        result = run_optimization(
            shipments=state["shipments"],
            vehicles=state["vehicles"],
            compatibility_graph=graph_object,
        )

        # Build the plan dict for AgentState
        plan = {
            "status": "INFEASIBLE" if result["is_infeasible"] else "OPTIMIZED",
            "assigned": result["assigned"],
            "unassigned": result["unassigned"],
            "is_infeasible": result["is_infeasible"],
            "total_trucks": result["plan_metrics"]["total_trucks"],
            "trips_baseline": result["plan_metrics"]["trips_baseline"],
            "avg_utilization": result["plan_metrics"]["avg_utilization"],
            "cost_saving_pct": result["plan_metrics"]["cost_saving_pct"],
            "carbon_saving_pct": result["plan_metrics"]["carbon_saving_pct"],
            "solver_used": result.get("solver_used", "UNKNOWN"),
            "solver_status": result.get("solver_status", "UNKNOWN"),
        }

        status = "completed"
        error = None

    except Exception as e:
        plan = {
            "status": "FAILED",
            "assigned": [],
            "unassigned": state["shipments"],
            "is_infeasible": True,
            "total_trucks": 0,
            "trips_baseline": len(state["shipments"]),
            "avg_utilization": 0.0,
            "cost_saving_pct": 0.0,
            "carbon_saving_pct": 0.0,
            "solver_used": "NONE",
            "solver_status": f"Error: {str(e)}",
        }
        status = "failed"
        error = str(e)
        print(f"[Solver Node] Failed: {e}")

    duration = (time.time() - start) * 1000
    timing = {"step": "OR Solver", "status": status, "duration_ms": round(duration, 1), "error": error}

    return {
        "consolidation_plan": plan,
        "step_timings": state["step_timings"] + [timing],
    }


def relaxation_node(state: AgentState) -> dict:
    """
    ACT PHASE (retry) — Diagnose infeasibility and suggest constraint relaxations.

    Triggered when the solver can't assign all shipments. Analyzes
    WHY and suggests the smallest changes to make it feasible.
    Increments retry_count so the conditional edge knows how many
    attempts have been made.
    """
    start = time.time()

    plan = state.get("consolidation_plan", {})
    unassigned = plan.get("unassigned", [])
    is_infeasible = plan.get("is_infeasible", False)

    relaxation_report = run_relaxation_analysis(
        all_shipments=state["shipments"],
        unassigned_shipments=unassigned,
        vehicles=state["vehicles"],
        is_fully_infeasible=is_infeasible,
    )

    duration = (time.time() - start) * 1000
    timing = {"step": "Relaxation Agent", "status": "completed", "duration_ms": round(duration, 1), "error": None}

    return {
        "relaxation": relaxation_report,
        "retry_count": state["retry_count"] + 1,
        "step_timings": state["step_timings"] + [timing],
    }


def simulation_node(state: AgentState) -> dict:
    """
    SIMULATION — Run all 4 scenario simulations using the actual solver.

    Each scenario modifies the inputs (time windows, fleet size, demand)
    and re-runs the optimizer to produce real metrics. Results feed
    into the Scenario Recommendation Agent for comparison.
    """
    start = time.time()

    # Check if simulation is enabled in config
    if not state["config"].get("run_simulation", True):
        timing = {"step": "Simulation Engine", "status": "skipped", "duration_ms": 0,
                  "error": "Skipped by config"}
        return {
            "scenario_results": None,
            "step_timings": state["step_timings"] + [timing],
        }

    try:
        # Get the compatibility graph from the Reason phase
        graph_object = None
        compat = state.get("compatibility_scores")
        if compat:
            graph_object = compat.get("graph_object")

        # Run all 4 scenarios with the actual solver
        scenarios = run_all_scenarios(
            shipments=state["shipments"],
            vehicles=state["vehicles"],
            compatibility_graph=graph_object,
        )

        status = "completed"
        error = None

    except Exception as e:
        scenarios = []
        status = "failed"
        error = str(e)
        print(f"[Simulation Node] Failed: {e}")

    duration = (time.time() - start) * 1000
    timing = {"step": "Simulation Engine", "status": status,
              "duration_ms": round(duration, 1), "error": error}

    return {
        "scenario_results": scenarios,
        "step_timings": state["step_timings"] + [timing],
    }


def insight_node(state: AgentState) -> dict:
    """
    INSIGHT — Generate human-readable explanations of the plan.

    Reads the solver output and produces lane-level insights, risk
    flags, and recommendations. Optionally writes an LLM narrative.
    """
    start = time.time()

    plan = state.get("consolidation_plan", {})
    assignments = plan.get("assigned", [])

    insights = run_insight_analysis(
        plan=plan,
        assignments=assignments,
        shipments=state["shipments"],
        vehicles=state["vehicles"],
    )

    duration = (time.time() - start) * 1000
    timing = {"step": "Insight Agent", "status": "completed", "duration_ms": round(duration, 1), "error": None}

    return {
        "insights": insights,
        "step_timings": state["step_timings"] + [timing],
    }


def scenario_rec_node(state: AgentState) -> dict:
    """
    SCENARIO RECOMMENDATION — Compare scenarios and recommend best per objective.

    Reads the 4 scenario results and produces ranked recommendations
    for cost, SLA, carbon, and balanced objectives.
    """
    start = time.time()

    scenarios = state.get("scenario_results")
    if not scenarios:
        timing = {"step": "Scenario Agent", "status": "skipped", "duration_ms": 0,
                  "error": "No scenario results to analyze"}
        return {
            "scenario_analysis": None,
            "step_timings": state["step_timings"] + [timing],
        }

    config = state.get("config", {})
    analysis = run_scenario_analysis(
        scenarios=scenarios,
        cost_weight=config.get("cost_weight", 0.40),
        sla_weight=config.get("sla_weight", 0.35),
        carbon_weight=config.get("carbon_weight", 0.25),
    )

    duration = (time.time() - start) * 1000
    timing = {"step": "Scenario Agent", "status": "completed", "duration_ms": round(duration, 1), "error": None}

    return {
        "scenario_analysis": analysis,
        "step_timings": state["step_timings"] + [timing],
    }


def metrics_node(state: AgentState) -> dict:
    """
    LEARN PHASE — Compute comprehensive before/after metrics.

    Uses the full metrics module to calculate distance-based carbon
    savings, per-truck breakdowns, and fleet usage stats. These feed
    the dashboard's impact summary cards and comparison charts.
    """
    start = time.time()

    try:
        plan = state.get("consolidation_plan", {})
        assignments = plan.get("assigned", [])

        metrics = compute_full_metrics(
            assignments=assignments,
            shipments=state["shipments"],
            vehicles=state["vehicles"],
        )

        status = "completed"
        error = None

    except Exception as e:
        metrics = {
            "error": str(e),
            "before": {}, "after": {}, "savings": {},
            "fleet": {}, "per_truck": [],
        }
        status = "failed"
        error = str(e)
        print(f"[Metrics Node] Failed: {e}")

    duration = (time.time() - start) * 1000
    timing = {"step": "Metrics Engine", "status": status,
              "duration_ms": round(duration, 1), "error": error}

    return {
        "metrics": metrics,
        "step_timings": state["step_timings"] + [timing],
    }


def outcome_logging_node(state: AgentState) -> dict:
    """
    LEARN PHASE — Log the complete optimization outcome to the database.

    Persists everything: plan, violations, scenarios, metrics, pipeline
    timings. Also checks if the compatibility model should be retrained
    based on the number of accumulated outcomes.

    This is the final node before END — it captures the full picture
    of what happened during this optimization run for historical
    tracking and model improvement.
    """
    start = time.time()

    try:
        # Build a response-like dict from state for the logger.
        # The logger expects the same shape as the API response.
        pipeline_result = {
            "plan": state.get("consolidation_plan", {}),
            "metrics": state.get("metrics", {}),
            "scenarios": state.get("scenario_results"),
            "guardrail": state.get("guardrail_result", {}),
            "compatibility": state.get("compatibility_scores", {}),
            "pipeline_metadata": {
                "steps": state.get("step_timings", []),
                "total_duration_ms": sum(
                    s.get("duration_ms", 0) for s in state.get("step_timings", [])
                ),
                "retry_count": state.get("retry_count", 0),
                "config": state.get("config", {}),
            },
        }

        # Log the outcome to the database
        log_result = log_outcome(pipeline_result)

        # Check if retraining is due
        if log_result.get("should_retrain", False):
            retrain_result = trigger_retraining()
        else:
            retrain_result = None

        status = "completed"
        error = None

    except Exception as e:
        log_result = {"outcome_id": None, "error": str(e)}
        retrain_result = None
        status = "failed"
        error = str(e)
        print(f"[Outcome Logging Node] Failed: {e}")

    duration = (time.time() - start) * 1000
    timing = {"step": "Outcome Logger", "status": status,
              "duration_ms": round(duration, 1), "error": error}

    return {
        "step_timings": state["step_timings"] + [timing],
    }


# ---------------------------------------------------------------------------
# Conditional edge functions — control the graph routing
# ---------------------------------------------------------------------------

def after_data_load(state: AgentState) -> str:
    """
    Route after Shipment Data Tool.
    If data loading failed or DB is empty (error is set), go to END.
    Otherwise proceed to validation.
    """
    if state.get("error"):
        return "end"
    return "validation_node"

def after_validation(state: AgentState) -> str:
    """
    Route after Validation Node.
    If validation failed (error is set), go to END.
    Otherwise proceed to the Reason phase (compatibility scoring).
    """
    if state.get("error"):
        return "end"
    return "compatibility_node"


def after_guardrail(state: AgentState) -> str:
    """
    Route after Policy Guardrail.
    If CRITICAL violations were found AND this is the first pass,
    go back to compatibility_node to re-score with filtered edges.
    Otherwise proceed to the solver.

    We only loop back once — if the guardrail still finds violations
    after re-scoring, we proceed anyway with the filtered edges.
    """
    guardrail = state.get("guardrail_result", {})
    critical = guardrail.get("critical_count", 0)

    # Only loop back on first pass (retry_count == 0 means first attempt)
    if critical > 0 and state["retry_count"] == 0:
        return "compatibility_node"

    return "solver_node"


def after_solver(state: AgentState) -> str:
    """
    Route after OR Solver.
    Three possible outcomes:
    1. Feasible → proceed to simulation
    2. Infeasible + retries left → go to relaxation agent
    3. Infeasible + retries exhausted → go to insight (skip simulation) then end

    Max retries: 2 (3 total solver attempts including the first)
    """
    plan = state.get("consolidation_plan", {})
    is_infeasible = plan.get("is_infeasible", False)
    has_unassigned = len(plan.get("unassigned", [])) > 0

    if is_infeasible or has_unassigned:
        # Check if we have retries left
        if state["retry_count"] < 2:
            return "relaxation_node"
        else:
            # Retries exhausted — go to insight to explain the partial result
            return "insight_node"

    # Feasible — proceed to simulation
    return "simulation_node"


def after_simulation(state: AgentState) -> str:
    """Always proceed to insight node after simulation."""
    return "insight_node"


def after_insight(state: AgentState) -> str:
    """
    After insight, go to scenario recommendation if we have scenarios.
    Otherwise skip to metrics.
    """
    if state.get("scenario_results"):
        return "scenario_rec_node"
    return "metrics_node"


def after_scenario_rec(state: AgentState) -> str:
    """Always proceed to metrics after scenario recommendation."""
    return "metrics_node"


def after_relaxation(state: AgentState) -> str:
    """After relaxation analysis, retry the solver."""
    return "solver_node"


# ---------------------------------------------------------------------------
# Build the LangGraph StateGraph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """
    Construct and compile the full LangGraph state graph.

    Node sequence:
    shipment_data_node -> validation_node -> compatibility_node ->
    guardrail_node -> solver_node -> simulation_node -> insight_node ->
    scenario_rec_node -> metrics_node

    With conditional edges for:
    - Empty DB -> END
    - Validation failure -> END
    - Guardrail violations -> re-run compatibility
    - Solver infeasibility -> relaxation -> retry solver
    - Retries exhausted -> insight -> END

    Returns:
        Compiled StateGraph ready for invocation
    """
    graph = StateGraph(AgentState)

    # --- Register all nodes ---
    graph.add_node("shipment_data_node", shipment_data_node)
    graph.add_node("validation_node", validation_node)
    graph.add_node("compatibility_node", compatibility_node)
    graph.add_node("guardrail_node", guardrail_node)
    graph.add_node("solver_node", solver_node)
    graph.add_node("relaxation_node", relaxation_node)
    graph.add_node("simulation_node", simulation_node)
    graph.add_node("insight_node", insight_node)
    graph.add_node("scenario_rec_node", scenario_rec_node)
    graph.add_node("metrics_node", metrics_node)
    graph.add_node("outcome_logging_node", outcome_logging_node)

    # --- Set the entry point: data loading comes first ---
    graph.set_entry_point("shipment_data_node")

    # --- Wire conditional edges ---

    # After data load: end if empty DB, else validate
    graph.add_conditional_edges("shipment_data_node", after_data_load, {
        "end": END,
        "validation_node": "validation_node",
    })

    # After validation: end if invalid, else proceed to compatibility
    graph.add_conditional_edges("validation_node", after_validation, {
        "end": END,
        "compatibility_node": "compatibility_node",
    })

    # After compatibility: always go to guardrail
    graph.add_edge("compatibility_node", "guardrail_node")

    # After guardrail: loop back to compatibility if violations, else solver
    graph.add_conditional_edges("guardrail_node", after_guardrail, {
        "compatibility_node": "compatibility_node",
        "solver_node": "solver_node",
    })

    # After solver: simulation if feasible, relaxation if infeasible, insight if retries exhausted
    graph.add_conditional_edges("solver_node", after_solver, {
        "simulation_node": "simulation_node",
        "relaxation_node": "relaxation_node",
        "insight_node": "insight_node",
    })

    # After relaxation: retry the solver
    graph.add_edge("relaxation_node", "solver_node")

    # After simulation: proceed to insight
    graph.add_edge("simulation_node", "insight_node")

    # After insight: scenario rec if we have scenarios, else metrics
    graph.add_conditional_edges("insight_node", after_insight, {
        "scenario_rec_node": "scenario_rec_node",
        "metrics_node": "metrics_node",
    })

    # After scenario rec: always proceed to metrics
    graph.add_edge("scenario_rec_node", "metrics_node")

    # After metrics: go to outcome logging
    graph.add_edge("metrics_node", "outcome_logging_node")

    # After outcome logging: end
    graph.add_edge("outcome_logging_node", END)

    compiled = graph.compile()
    return compiled


# ---------------------------------------------------------------------------
# Main entry point — replaces orchestrator.run_pipeline()
# ---------------------------------------------------------------------------

# Re-compile the graph with the new data loading node
pipeline = build_graph()


# ---------------------------------------------------------------------------
# Graph diagram export
# ---------------------------------------------------------------------------

def export_graph_diagram(
    output_dir: str = "data",
    filename: str = "langgraph_flow",
) -> Dict[str, str]:
    """
    Export the LangGraph state graph as a Mermaid diagram.

    Calls LangGraph's built-in .get_graph().draw_mermaid() to produce
    a Mermaid-formatted flowchart string. Saves it to a .mermaid file
    that can be:
    - Pasted into GitHub README (renders natively)
    - Opened in https://mermaid.live for editing
    - Embedded in presentation slides
    - Converted to PNG via mermaid-cli (mmdc)

    Args:
        output_dir: Directory to save the output files
        filename: Base filename (without extension)

    Returns:
        Dict with file paths and the raw mermaid string
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    # Get the mermaid diagram from LangGraph's built-in export
    mermaid_str = pipeline.get_graph().draw_mermaid()

    # Save the raw mermaid file
    mermaid_path = os.path.join(output_dir, f"{filename}.mermaid")
    with open(mermaid_path, "w") as f:
        f.write(mermaid_str)

    print(f"[LangGraph Export] Mermaid diagram saved to {mermaid_path}")

    # Try to generate PNG using draw_mermaid_png if available.
    # This requires the 'mermaid' extra or an API call — falls back
    # gracefully if not available.
    png_path = None
    try:
        png_bytes = pipeline.get_graph().draw_mermaid_png()
        png_path = os.path.join(output_dir, f"{filename}.png")
        with open(png_path, "wb") as f:
            f.write(png_bytes)
        print(f"[LangGraph Export] PNG diagram saved to {png_path}")
    except Exception as e:
        print(f"[LangGraph Export] PNG export skipped: {e}")
        print(f"[LangGraph Export] To generate PNG manually, paste the .mermaid file into https://mermaid.live")

    return {
        "mermaid_path": mermaid_path,
        "png_path": png_path,
        "mermaid_string": mermaid_str,
    }


def run_pipeline(
    shipments: List[Dict],
    vehicles: List[Dict],
    config: Optional[Dict] = None,
) -> Dict:
    """
    Run the full LangGraph pipeline.

    This is the function that the /optimize endpoint calls.
    Replaces orchestrator.run_pipeline() with a proper LangGraph execution.

    Args:
        shipments: List of shipment dicts from the database
        vehicles: List of vehicle dicts from the database
        config: Pipeline configuration overrides

    Returns:
        Unified response dict matching the API response shape
    """
    import os

    cfg = {
        "run_simulation": True,
        "run_llm": True,
        "cost_weight": 0.40,
        "sla_weight": 0.35,
        "carbon_weight": 0.25,
        **(config or {}),
    }

    # Suppress LLM calls if configured
    original_key = os.getenv("GOOGLE_API_KEY", "")
    if not cfg.get("run_llm", True):
        os.environ["GOOGLE_API_KEY"] = ""

    # Build the initial state.
    # Shipments and vehicles start empty — the shipment_data_node
    # will populate them from the database as the first step.
    # If shipments/vehicles were passed in directly (e.g. for testing),
    # use those instead and the data tool will be a no-op since the
    # after_data_load edge checks state["error"], not state["shipments"].
    initial_state = {
        "shipments": shipments if shipments else [],
        "vehicles": vehicles if vehicles else [],
        "config": cfg,
        "validation_report": None,
        "compatibility_scores": None,
        "guardrail_result": None,
        "consolidation_plan": None,
        "constraint_violations": [],
        "relaxation": None,
        "scenario_results": None,
        "scenario_analysis": None,
        "insights": None,
        "metrics": None,
        "retry_count": 0,
        "step_timings": [],
        "error": None,
    }

    # Execute the graph
    pipeline_start = time.time()

    try:
        final_state = pipeline.invoke(initial_state)
    except Exception as e:
        # If the graph itself crashes, return a structured error response
        print(f"[LangGraph Pipeline] Graph execution failed: {e}")
        if not cfg.get("run_llm", True):
            os.environ["GOOGLE_API_KEY"] = original_key
        return {
            "validation": None, "plan": None, "compatibility": None,
            "guardrail": None, "insights": None, "relaxation": None,
            "scenarios": None, "scenario_analysis": None, "metrics": None,
            "pipeline_metadata": {
                "steps": [], "total_duration_ms": 0, "retry_count": 0,
                "config": cfg, "error": str(e),
            },
        }

    total_duration = (time.time() - pipeline_start) * 1000

    # Restore API key
    if not cfg.get("run_llm", True):
        os.environ["GOOGLE_API_KEY"] = original_key

    # --- Build the API response from the final state ---
    # We need to strip non-serializable objects (like networkx Graph)
    # and reshape some fields for the frontend.

    # Clean up compatibility scores — remove the networkx graph object
    raw_compat = final_state.get("compatibility_scores")
    clean_compat = None
    if raw_compat:
        clean_compat = {
            "stats": raw_compat.get("stats", {}),
            "edges_sample": raw_compat.get("edges", [])[:20],
            "model_info": raw_compat.get("model_info", {}),
        }

    # Clean up guardrail — remove filtered_edges (large, not needed in response)
    raw_guardrail = final_state.get("guardrail_result")
    clean_guardrail = None
    if raw_guardrail:
        clean_guardrail = {
            "passed": raw_guardrail.get("passed"),
            "violations": raw_guardrail.get("violations", []),
            "critical_count": raw_guardrail.get("critical_count", 0),
            "warning_count": raw_guardrail.get("warning_count", 0),
            "info_count": raw_guardrail.get("info_count", 0),
            "edges_removed": raw_guardrail.get("edges_removed", 0),
        }

    # Clean up consolidation plan — remove internal fields
    raw_plan = final_state.get("consolidation_plan")
    clean_plan = None
    if raw_plan:
        clean_plan = {
            "status": raw_plan.get("status"),
            "assigned": raw_plan.get("assigned", []),
            "unassigned": [s.get("shipment_id", "") for s in raw_plan.get("unassigned", [])],
            "is_infeasible": raw_plan.get("is_infeasible", False),
            "total_trucks": raw_plan.get("total_trucks", 0),
            "trips_baseline": raw_plan.get("trips_baseline", 0),
            "avg_utilization": raw_plan.get("avg_utilization", 0),
            "cost_saving_pct": raw_plan.get("cost_saving_pct", 0),
            "carbon_saving_pct": raw_plan.get("carbon_saving_pct", 0),
        }

    return {
        "validation": final_state.get("validation_report"),
        "plan": clean_plan,
        "compatibility": clean_compat,
        "guardrail": clean_guardrail,
        "insights": final_state.get("insights"),
        "relaxation": final_state.get("relaxation"),
        "scenarios": final_state.get("scenario_results"),
        "scenario_analysis": final_state.get("scenario_analysis"),
        "metrics": final_state.get("metrics"),
        "pipeline_metadata": {
            "steps": final_state.get("step_timings", []),
            "total_duration_ms": round(total_duration, 1),
            "retry_count": final_state.get("retry_count", 0),
            "config": cfg,
        },
    }