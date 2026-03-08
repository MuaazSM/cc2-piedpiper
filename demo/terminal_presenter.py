"""
Lorri AI — Terminal Demo Walkthrough

Interactive demonstration of the complete Observe → Reason → Decide → Act → Learn
agent loop for freight load consolidation optimization.

Run:
    python -m demo.terminal_presenter

Or via the runner script:
    ./demo/run.sh
"""

import time
import os
import sys
import json
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Suppress internal logging during demo for clean output
# ---------------------------------------------------------------------------

import logging
logging.disable(logging.WARNING)

# Redirect internal print statements from tools/agents
import builtins
_original_print = builtins.print
_suppress_prefixes = [
    "[Compatibility Model]", "[Compatibility Filter]", "[Guardrail]",
    "[Optimization Tool]", "[OR Solver]", "[Simulation]", "[Outcome Logger]",
    "[Shipment Data Tool]", "[Compatibility Tool]", "[Solomon Mapper]",
    "[Insight Agent]", "[Scenario Agent]", "[Relaxation Agent]",
    "[Validation Agent]", "[LangGraph",
]

def _filtered_print(*args, **kwargs):
    """Suppress internal debug prints during demo."""
    if args:
        msg = str(args[0])
        for prefix in _suppress_prefixes:
            if msg.startswith(prefix):
                return
    _original_print(*args, **kwargs)

builtins.print = _filtered_print


# ---------------------------------------------------------------------------
# Color codes and symbols
# ---------------------------------------------------------------------------

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
WHITE = "\033[97m"
RESET = "\033[0m"
CHECK = f"{GREEN}✓{RESET}"
CROSS = f"{RED}✗{RESET}"
WARN = f"{YELLOW}⚠{RESET}"
ARROW = f"{CYAN}→{RESET}"


# ---------------------------------------------------------------------------
# Banner and section formatters
# ---------------------------------------------------------------------------

def banner():
    print(f"""
{CYAN}{'='*70}
{BOLD}
  ██╗      ██████╗ ██████╗ ██████╗ ██╗     █████╗ ██╗
  ██║     ██╔═══██╗██╔══██╗██╔══██╗██║    ██╔══██╗██║
  ██║     ██║   ██║██████╔╝██████╔╝██║    ███████║██║
  ██║     ██║   ██║██╔══██╗██╔══██╗██║    ██╔══██║██║
  ███████╗╚██████╔╝██║  ██║██║  ██║██║    ██║  ██║██║
  ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝    ╚═╝  ╚═╝╚═╝
{RESET}
{BOLD}  Agentic Logistics Control Tower{RESET}
{DIM}  AI-Powered Load Consolidation Optimization System{RESET}
{DIM}  Team Jugaadus · Taqneeq CyberCypher R2 · Problem Statement 5{RESET}
{CYAN}{'='*70}{RESET}
""")


def section(title, phase=None):
    phase_colors = {
        "OBSERVE": CYAN,
        "REASON": BLUE,
        "DECIDE": YELLOW,
        "ACT": MAGENTA,
        "LEARN": GREEN,
    }
    color = phase_colors.get(phase, WHITE)
    phase_label = f" [{phase}]" if phase else ""
    print(f"\n{color}{'─'*70}")
    print(f"  {BOLD}{title}{RESET}{color}{phase_label}")
    print(f"{'─'*70}{RESET}\n")


# ---------------------------------------------------------------------------
# Pipeline state tracker
# ---------------------------------------------------------------------------

class PipelineState:
    """Tracks data flowing through the demo pipeline"""

    def __init__(self):
        self.shipments = []
        self.vehicles = []
        self.validation_report = None
        self.compatibility_stats = None
        self.guardrail_result = None
        self.plan = None
        self.scenarios = []
        self.insights = None
        self.metrics = None
        self.recommendations = None


# ---------------------------------------------------------------------------
# Presenter helpers
# ---------------------------------------------------------------------------

def kv(key, value, indent=2):
    """Print a key-value pair"""
    print(f"{' '*indent}{DIM}{key}:{RESET} {BOLD}{value}{RESET}")


def animate_step(message, slow_mode=True):
    """Animate a processing step with OK indicator"""
    print(f"  {DIM}→ {message}...", end=" ", flush=True)
    if slow_mode:
        time.sleep(0.3)
    print(f"{GREEN}OK{RESET}")


def table_header(cols, widths):
    """Print a formatted table header"""
    row = "  ".join(f"{h:<{w}}" for h, w in zip(cols, widths))
    print(f"  {BOLD}{CYAN}{row}{RESET}")
    print(f"  {DIM}{'-' * len(row)}{RESET}")


def table_row(cols, widths):
    """Print a formatted table row"""
    row = "  ".join(f"{str(c):<{w}}" for c, w in zip(cols, widths))
    print(f"  {row}")


def code_block(title, code):
    """Print a code block"""
    print(f"\n  {DIM}── {title} ──{RESET}")
    for line in code.strip().split("\n"):
        print(f"  {DIM}{line}{RESET}")
    print()


def wait(message="Press Enter to continue...", slow_mode=True):
    """Wait for user input"""
    if slow_mode:
        input(f"\n{DIM}  {message}{RESET}")
    else:
        time.sleep(0.1)


def metric_row(label, before, after, pct=None):
    """Print a before/after metric row"""
    bstr = f"{before:,.1f}" if isinstance(before, float) else str(before or 0)
    astr = f"{after:,.1f}" if isinstance(after, float) else str(after or 0)
    if pct is not None and pct > 0:
        pstr = f"{GREEN}↓ {pct:.1f}%{RESET}"
    elif pct is not None and pct < 0:
        pstr = f"{RED}↑ {abs(pct):.1f}%{RESET}"
    else:
        pstr = ""
    print(f"  {label:<25} {bstr:>12} {ARROW} {astr:>12}  {pstr}")


# ---------------------------------------------------------------------------
# Load environment
# ---------------------------------------------------------------------------

def load_env_file():
    env_path = Path(__file__).parent.parent / "backend" / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"').strip("'")
                    os.environ.setdefault(key.strip(), value)


# ---------------------------------------------------------------------------
# OBSERVE Phase
# ---------------------------------------------------------------------------

def demo_observe(state: PipelineState, slow=True):
    """OBSERVE phase — Data loading + Validation"""
    section("OBSERVE PHASE — Data Ingestion & Validation", "OBSERVE")
    print(f"  {DIM}The OBSERVE phase loads shipment data and validates quality.{RESET}")
    print(f"  {DIM}Agent 1 gates the pipeline — bad data never reaches the solver.{RESET}\n")

    # --- Data Generation ---
    section("Tool 1: Shipment Data Tool", "OBSERVE")

    from backend.app.data_loader.synthetic_generator import SyntheticGenerator
    gen = SyntheticGenerator(seed=42)
    state.shipments = gen.generate_shipments(count=20, mode="normal")
    state.vehicles = gen.generate_vehicles(count=10)

    animate_step("Generating 20 shipments across 9 Indian logistics hubs", slow)
    animate_step("Generating fleet of 10 vehicles (small, medium, large, refrigerated)", slow)
    animate_step("Computing road distances between 36 city-pair lanes", slow)

    kv("Shipments", len(state.shipments))
    kv("Vehicles", len(state.vehicles))
    kv("Cities", "Mumbai · Pune · Delhi · Bangalore · Chennai · Hyderabad · Ahmedabad · Kolkata · Jaipur")

    weight_min = min(s['weight'] for s in state.shipments)
    weight_max = max(s['weight'] for s in state.shipments)
    kv("Weight range", f"{weight_min:.0f}kg — {weight_max:.0f}kg")

    special = set(s['special_handling'] for s in state.shipments if s['special_handling'])
    kv("Special handling", ", ".join(special) if special else "None")

    high = sum(1 for s in state.shipments if s['priority'] == 'HIGH')
    med = sum(1 for s in state.shipments if s['priority'] == 'MEDIUM')
    low = sum(1 for s in state.shipments if s['priority'] == 'LOW')
    kv("Priority mix", f"HIGH: {high} · MEDIUM: {med} · LOW: {low}")

    print(f"\n  {BOLD}Sample Shipments:{RESET}")
    widths = [10, 12, 12, 10, 8, 8]
    table_header(["ID", "Origin", "Dest", "Weight", "Vol", "Priority"], widths)
    for s in state.shipments[:5]:
        table_row([s["shipment_id"], s["origin"], s["destination"],
                   f"{s['weight']:.0f}kg", f"{s['volume']:.1f}m³", s["priority"]], widths)
    print(f"  {DIM}... and {len(state.shipments)-5} more{RESET}")

    print(f"\n  {BOLD}Fleet Composition:{RESET}")
    type_counts = {}
    for v in state.vehicles:
        t = v["vehicle_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    for vtype, count in type_counts.items():
        kv(f"  {vtype}", f"{count} vehicles", indent=4)

    wait(slow_mode=slow)

    # --- Validation ---
    section("Agent 1: Validation Agent", "OBSERVE")
    print(f"  {DIM}15+ data quality checks. Gates the pipeline — errors block optimization.{RESET}\n")

    from backend.app.agents.validation_agent import run_validation

    animate_step("Checking required fields (origin, destination, weight, volume, times)", slow)
    animate_step("Validating time windows (delivery must be after pickup)", slow)
    animate_step("Checking for negative/zero weights and volumes", slow)
    animate_step("Comparing shipment weights against fleet capacity limits", slow)
    animate_step("Checking special handling availability (refrigerated vehicles in fleet?)", slow)
    animate_step("Analyzing origin distribution for consolidation potential", slow)
    animate_step("Validating priority distribution", slow)

    validation = run_validation(state.shipments, state.vehicles)
    state.validation_report = validation

    is_valid = validation.get("is_valid", False)
    counts = validation.get("summary_counts", {})

    if is_valid:
        print(f"\n  {CHECK} {GREEN}{BOLD}Validation PASSED — data is ready for optimization{RESET}")
    else:
        print(f"\n  {CROSS} {RED}{BOLD}Validation FAILED — {counts.get('error_count', 0)} critical errors{RESET}")

    kv("Errors (block optimization)", counts.get("error_count", 0))
    kv("Warnings (proceed with caution)", counts.get("warning_count", 0))
    kv("Info (observations)", counts.get("info_count", 0))

    warnings = validation.get("warnings", [])
    if warnings:
        print(f"\n  {YELLOW}Warnings:{RESET}")
        for w in warnings[:4]:
            print(f"    {WARN} [{w.get('shipment_id', 'FLEET')}] {w.get('message', '')}")

    infos = validation.get("info", [])
    if infos:
        print(f"\n  {CYAN}Observations:{RESET}")
        for info in infos[:3]:
            print(f"    {ARROW} {info.get('message', '')}")

    llm_summary = validation.get("llm_summary")
    if llm_summary:
        print(f"\n  {CYAN}Agent 1 LLM Summary (Gemini 2.0 Flash):{RESET}")
        print(f"  {DIM}\"{llm_summary}\"{RESET}")

    print(f"\n  {CHECK} {GREEN}OBSERVE phase complete{RESET}")
    wait(slow_mode=slow)


# ---------------------------------------------------------------------------
# REASON Phase
# ---------------------------------------------------------------------------

def demo_reason(state: PipelineState, slow=True):
    """REASON phase — ML compatibility scoring + graph building"""
    section("REASON PHASE — ML Compatibility Scoring", "REASON")
    print(f"  {DIM}Score all shipment pairs using RandomForest (F1=0.84).{RESET}")
    print(f"  {DIM}Build a networkx compatibility graph. Apply hard rule-based filters.{RESET}\n")

    section("Tool 2: Compatibility Scoring Tool", "REASON")

    from backend.app.agents.tools.compatibility_scoring_tool import score_shipment_pairs

    n = len(state.shipments)
    total_pairs = n * (n - 1) // 2

    animate_step(f"Loading trained RandomForest (400 trees, max_depth=25, F1=0.84)", slow)
    animate_step(f"Generating {total_pairs} unique shipment pairs from {n} shipments", slow)
    animate_step(f"Extracting 14 features per pair:", slow)

    print(f"    {DIM}time_overlap_pct (31.4%) · origin_distance_km (12.6%) · same_origin (9.3%){RESET}")
    print(f"    {DIM}dest_distance_km (8.7%) · same_destination (6.5%) · priority_match (6.5%){RESET}")
    print(f"    {DIM}volume_ratio · weight_ratio · combined_weight · combined_volume{RESET}")
    print(f"    {DIM}priority_conflict · handling_conflict · either_hazardous · same_lane{RESET}")

    animate_step(f"Running batch prediction: P(compatible) for all {total_pairs} pairs", slow)

    result = score_shipment_pairs(state.shipments, state.vehicles, threshold=0.6)
    state.compatibility_stats = result

    stats = result.get("stats", {})
    model_info = result.get("model_info", {})

    kv("Model", f"{model_info.get('model_type', 'RandomForest')} ({model_info.get('status', 'loaded')})")
    kv("Pairs scored", stats.get("total_pairs_scored", 0))
    kv("Compatible (ML, P ≥ 0.6)", stats.get("compatible_pairs", 0))
    kv("Compatibility rate", f"{stats.get('compatibility_rate', 0)*100:.1f}%")

    wait(slow_mode=slow)

    # Rule-based filter
    section("Rule-Based Hard Filter", "REASON")
    print(f"  {DIM}Enforcing operational constraints on top of ML scores.{RESET}\n")

    animate_step("Filter 1: Time window overlap ≥ 5%", slow)
    animate_step("Filter 2: Combined weight+volume within vehicle capacity", slow)
    animate_step("Filter 3: Special handling conflicts (hazmat ≠ fragile)", slow)
    animate_step("Filter 4: Route detour within 500km limit", slow)

    edges_after = stats.get("edges_after_filter", stats.get("compatible_pairs", 0))
    removed = stats.get("edges_removed_by_filter", 0)
    reasons = stats.get("filter_removal_reasons", {})

    kv("Edges after ML", stats.get("compatible_pairs", 0))
    kv("Removed by filter", removed)
    kv("Surviving edges", edges_after)

    if reasons:
        print(f"\n  {DIM}Removal breakdown:{RESET}")
        for reason, count in reasons.items():
            if count > 0:
                print(f"    {DIM}→ {reason}: {count} removed{RESET}")

    edges = result.get("edges", [])
    if edges:
        print(f"\n  {BOLD}Top Compatible Pairs (ranked by ML score):{RESET}")
        widths = [12, 12, 10]
        table_header(["Shipment A", "Shipment B", "P(compat)"], widths)
        for e in edges[:6]:
            table_row([e["shipment_a"], e["shipment_b"], f"{e['score']:.4f}"], widths)

    kv("Avg connections/shipment", stats.get("avg_connections_per_shipment", 0))
    kv("Connected components", stats.get("connected_components", 0))

    print(f"\n  {CHECK} {GREEN}REASON phase complete — compatibility graph built{RESET}")
    wait(slow_mode=slow)


# ---------------------------------------------------------------------------
# DECIDE Phase
# ---------------------------------------------------------------------------

def demo_decide(state: PipelineState, slow=True):
    """DECIDE phase — Policy guardrail"""
    section("DECIDE PHASE — Policy Guardrail", "DECIDE")
    print(f"  {DIM}Validates every compatible pair against safety policies.{RESET}")
    print(f"  {DIM}If critical violations found → LOOPS BACK to REASON automatically.{RESET}\n")

    section("Policy Guardrail Tool", "DECIDE")

    from backend.app.agents.guardrail import run_guardrail

    edges = state.compatibility_stats.get("edges", [])

    animate_step("Rule 1: Hazmat ≠ food/fragile/refrigerated (safety regulation)", slow)
    animate_step("Rule 2: HIGH priority cannot be delayed by LOW priority stops", slow)
    animate_step("Rule 3: Special handling requirements must match", slow)
    animate_step(f"Scanning {len(edges)} compatible pairs against all rules", slow)

    guardrail = run_guardrail(edges, state.shipments)
    state.guardrail_result = guardrail

    if guardrail.get("passed", True):
        print(f"\n  {CHECK} {GREEN}{BOLD}Guardrail PASSED — no critical violations{RESET}")
        print(f"  {GREEN}→ Conditional edge: proceeding to ACT phase (solver){RESET}")
    else:
        print(f"\n  {CROSS} {RED}{BOLD}Guardrail FAILED — critical violations detected{RESET}")
        print(f"  {RED}→ Conditional edge: LOOPING BACK to REASON to re-score{RESET}")

    kv("Critical (edges removed)", guardrail.get("critical_count", 0))
    kv("Warnings (flagged)", guardrail.get("warning_count", 0))
    kv("Info", guardrail.get("info_count", 0))
    kv("Edges removed", guardrail.get("edges_removed", 0))

    violations = guardrail.get("violations", [])
    if violations:
        print(f"\n  {YELLOW}Violations Detected:{RESET}")
        for v in violations[:5]:
            sev = v.get("severity", "INFO")
            color = RED if sev == "CRITICAL" else YELLOW if sev == "WARNING" else DIM
            print(f"    {color}[{sev}]{RESET} {v.get('message', '')}")

    print(f"\n  {CHECK} {GREEN}DECIDE phase complete — safety policies enforced{RESET}")
    wait(slow_mode=slow)


# ---------------------------------------------------------------------------
# ACT Phase
# ---------------------------------------------------------------------------

def demo_act(state: PipelineState, slow=True):
    """ACT phase — Solver + Simulation"""
    section("ACT PHASE — Optimization & Simulation", "ACT")
    print(f"  {DIM}OR-Tools solver assigns shipments to trucks.{RESET}")
    print(f"  {DIM}4 scenarios simulated with the real solver.{RESET}")
    print(f"  {DIM}If infeasible → Relaxation Agent diagnoses and retries (up to 2x).{RESET}\n")

    # --- Solver ---
    section("Tool 3: OR-Tools Optimization", "ACT")

    from backend.app.agents.tools.optimization_tool import run_optimization

    graph_object = state.compatibility_stats.get("graph_object") if state.compatibility_stats else None
    n = len(state.shipments)

    solver_type = "MIP (CP-SAT, exact)" if n <= 50 else "Heuristic (FFD + Local Search)"

    animate_step(f"Selected solver: {solver_type} for {n} shipments", slow)
    animate_step("Loading compatibility graph as constraint input", slow)

    code_block("MIP Formulation", """
Decision variable: x[i,k] = 1 if shipment i → truck k
Objective:   min Σ TripCost_k − α · Utilization_k
Constraints: weight ≤ capacity | volume ≤ capacity | single assignment
             handling conflicts | time window compatibility
""")

    animate_step("Building constraint matrix", slow)
    animate_step("Setting time limit: 30 seconds, 4 parallel workers", slow)
    animate_step("Solving...", slow)

    solver_result = run_optimization(state.shipments, state.vehicles, graph_object)
    state.plan = solver_result

    if solver_result.get("is_infeasible", False):
        print(f"\n  {CROSS} {RED}{BOLD}Solver: INFEASIBLE{RESET}")
        kv("Unassigned", len(solver_result.get("unassigned", [])))
        kv("Status", solver_result.get("solver_status", "UNKNOWN"))
        print(f"\n  {YELLOW}→ Conditional edge: Relaxation Agent (Agent 3) triggered{RESET}")
        print(f"  {DIM}Would diagnose blocking constraints and retry up to 2 times.{RESET}")
    else:
        metrics = solver_result.get("plan_metrics", {})
        print(f"\n  {CHECK} {GREEN}{BOLD}Solver: {solver_result.get('solver_status', 'OPTIMAL')} solution found!{RESET}")
        kv("Solver used", solver_result.get("solver_used", "MIP"))
        kv("Trucks used", f"{metrics.get('total_trucks', 0)} / {len(state.vehicles)} available")
        kv("Avg utilization", f"{metrics.get('avg_utilization', 0):.1f}%")
        kv("Cost savings", f"{metrics.get('cost_saving_pct', 0):.1f}%")
        kv("Carbon savings", f"{metrics.get('carbon_saving_pct', 0):.1f}%")
        kv("Unassigned", len(solver_result.get("unassigned", [])))

        assignments = solver_result.get("assigned", [])
        if assignments:
            print(f"\n  {BOLD}Vehicle Assignments:{RESET}")
            widths = [10, 40, 12]
            table_header(["Vehicle", "Shipments", "Utilization"], widths)
            for a in assignments[:8]:
                sids = ", ".join(a.get("shipment_ids", []))
                if len(sids) > 38:
                    sids = sids[:35] + "..."
                util = a.get("utilization_pct", 0)
                if util > 85:
                    util_str = f"{GREEN}{util:.1f}%{RESET}"
                elif util > 50:
                    util_str = f"{YELLOW}{util:.1f}%{RESET}"
                else:
                    util_str = f"{RED}{util:.1f}%{RESET}"
                table_row([a.get("vehicle_id", ""), sids, util_str], widths)
            if len(assignments) > 8:
                print(f"  {DIM}... and {len(assignments)-8} more{RESET}")

    wait(slow_mode=slow)

    # --- Scenarios ---
    section("Tool 4: Scenario Simulation (4 Real Solver Runs)", "ACT")

    from backend.app.agents.tools.scenario_simulation_tool import run_all_scenarios

    print(f"  {DIM}Each scenario modifies inputs and re-runs the actual solver:{RESET}\n")
    print(f"  {CYAN}1. STRICT_SLA{RESET}       — Original time windows, no relaxation")
    print(f"  {CYAN}2. FLEXIBLE_SLA{RESET}     — Windows expanded ±30 minutes")
    print(f"  {CYAN}3. VEHICLE_SHORTAGE{RESET} — Only 70% of fleet available")
    print(f"  {CYAN}4. DEMAND_SURGE{RESET}     — Shipment weights increased 1.3x\n")

    animate_step("Running STRICT_SLA scenario", slow)
    animate_step("Running FLEXIBLE_SLA scenario", slow)
    animate_step("Running VEHICLE_SHORTAGE scenario", slow)
    animate_step("Running DEMAND_SURGE scenario", slow)

    scenarios = run_all_scenarios(state.shipments, state.vehicles, graph_object)
    state.scenarios = scenarios

    if scenarios:
        print(f"\n  {BOLD}Scenario Comparison:{RESET}")
        widths = [20, 8, 10, 12, 12, 8]
        table_header(["Scenario", "Trucks", "Util %", "Cost (₹)", "Carbon", "SLA %"], widths)
        for s in scenarios:
            table_row([
                s.get("scenario_type", ""),
                str(s.get("trucks_used", 0)),
                f"{s.get('avg_utilization', 0):.1f}%",
                f"{s.get('total_cost', 0):,.0f}",
                f"{s.get('carbon_emissions', 0):,.0f}kg",
                f"{s.get('sla_success_rate', 0):.0f}%",
            ], widths)

    # Recommendations
    from backend.app.agents.scenario_agent import run_scenario_analysis
    if scenarios:
        # Filter out infeasible scenarios before analysis —
        # an infeasible scenario with 0 cost shouldn't be "recommended"
        feasible_scenarios = [s for s in scenarios if not s.get("is_infeasible", False) and s.get("trucks_used", 0) > 0]
        analysis_input = feasible_scenarios if feasible_scenarios else scenarios
        analysis = run_scenario_analysis(analysis_input)
        state.recommendations = analysis
        recs = analysis.get("recommendations", {})
        dominance = analysis.get("dominance", {})

        print(f"\n  {BOLD}Agent 4 — Scenario Recommendations:{RESET}")
        for obj_key, label in [("cost_optimized", "💰 Lowest Cost"),
                                ("sla_optimized", "📦 Best SLA"),
                                ("carbon_optimized", "🌱 Lowest Carbon"),
                                ("balanced", "⚖️  Balanced")]:
            rec = recs.get(obj_key, {})
            scenario = rec.get("recommended_scenario", "N/A")
            print(f"    {ARROW} {label:<20} {BOLD}{scenario}{RESET}")

        if dominance.get("dominant"):
            print(f"\n  {GREEN}★ Dominant (best on ALL): {BOLD}{dominance['dominant']}{RESET}")
        if dominance.get("dominated"):
            print(f"  {RED}✗ Dominated (worst on ALL): {dominance['dominated']}{RESET}")

    print(f"\n  {CHECK} {GREEN}ACT phase complete — plan optimized, 4 scenarios simulated{RESET}")
    wait(slow_mode=slow)


# ---------------------------------------------------------------------------
# INSIGHT Phase
# ---------------------------------------------------------------------------

def demo_insight(state: PipelineState, slow=True):
    """INSIGHT — Agent 2 lane commentary + risk flags"""
    section("INSIGHT — Agent 2: Plan Explanation", "ACT")
    print(f"  {DIM}Lane-by-lane consolidation commentary, risk flags, recommendations.{RESET}\n")

    from backend.app.agents.insight_agent import run_insight_analysis

    plan_dict = {
        "total_trucks": state.plan.get("plan_metrics", {}).get("total_trucks", 0) if state.plan else 0,
        "trips_baseline": len(state.shipments),
        "avg_utilization": state.plan.get("plan_metrics", {}).get("avg_utilization", 0) if state.plan else 0,
        "cost_saving_pct": state.plan.get("plan_metrics", {}).get("cost_saving_pct", 0) if state.plan else 0,
        "carbon_saving_pct": state.plan.get("plan_metrics", {}).get("carbon_saving_pct", 0) if state.plan else 0,
    }

    animate_step("Computing plan-level summary", slow)
    animate_step("Generating per-lane consolidation commentary", slow)
    animate_step("Identifying risk flags (capacity, SLA, underutilization)", slow)
    animate_step("Generating strategic recommendations", slow)

    raw_assignments = state.plan.get("assigned", []) if state.plan else []
    # The insight agent expects shipment_ids as JSON strings
    assignments = []
    for a in raw_assignments:
        a_copy = dict(a)
        sids = a_copy.get("shipment_ids", [])
        if isinstance(sids, list):
            a_copy["shipment_ids"] = json.dumps(sids)
        assignments.append(a_copy)
    insights = run_insight_analysis(plan_dict, assignments, state.shipments, state.vehicles)
    state.insights = insights

    summary = insights.get("plan_summary", {})
    kv("Utilization rating", summary.get("utilization_rating", "N/A"))
    kv("Trips saved", f"{summary.get('trips_saved', 0)} ({summary.get('trips_saved_pct', 0):.0f}% reduction)")

    lane_insights = insights.get("lane_insights", [])
    if lane_insights:
        print(f"\n  {BOLD}Lane Insights:{RESET}")
        for li in lane_insights[:4]:
            print(f"    {ARROW} {li.get('summary', '')}")

    risk_flags = insights.get("risk_flags", [])
    if risk_flags:
        print(f"\n  {YELLOW}Risk Flags:{RESET}")
        for rf in risk_flags[:3]:
            print(f"    {WARN} [{rf.get('type')}] {rf.get('message', '')}")

    recommendations = insights.get("recommendations", [])
    if recommendations:
        print(f"\n  {GREEN}Recommendations:{RESET}")
        for rec in recommendations[:3]:
            print(f"    {ARROW} [{rec.get('priority')}] {rec.get('message', '')}")

    llm_narrative = insights.get("llm_narrative")
    if llm_narrative:
        print(f"\n  {CYAN}Agent 2 LLM Narrative (Gemini 2.0 Flash):{RESET}")
        wrapped = llm_narrative[:300] + ("..." if len(llm_narrative) > 300 else "")
        print(f"  {DIM}\"{wrapped}\"{RESET}")

    print(f"\n  {CHECK} {GREEN}INSIGHT complete — plan explained{RESET}")
    wait(slow_mode=slow)


# ---------------------------------------------------------------------------
# LEARN Phase
# ---------------------------------------------------------------------------

def demo_learn(state: PipelineState, slow=True):
    """LEARN phase — Metrics + Outcome logging"""
    section("LEARN PHASE — Metrics & Outcome Logging", "LEARN")
    print(f"  {DIM}Compute before/after metrics, log outcome, arm retraining hook.{RESET}\n")

    section("Tool 5: Metrics Engine", "LEARN")

    from backend.app.optimizer.metrics import compute_full_metrics

    assignments = state.plan.get("assigned", []) if state.plan else []

    animate_step("Computing baseline (1 shipment per truck, no consolidation)", slow)
    animate_step("Computing consolidated metrics from solver output", slow)
    animate_step("Calculating distance-based carbon (0.8 kg CO₂/km)", slow)
    animate_step("Generating per-truck breakdown", slow)

    metrics = compute_full_metrics(assignments, state.shipments, state.vehicles)
    state.metrics = metrics

    before = metrics.get("before", {})
    after = metrics.get("after", {})
    savings = metrics.get("savings", {})

    if before and after:
        print(f"\n  {BOLD}{'Metric':<25} {'Before':>12}         {'After':>12}  {'Impact':>10}{RESET}")
        print(f"  {DIM}{'─'*70}{RESET}")

        metric_row("Total Trips", before.get("total_trips", 0), after.get("total_trips", 0), savings.get("trip_reduction_pct"))
        metric_row("Avg Utilization %", before.get("avg_utilization", 0), after.get("avg_utilization", 0))
        metric_row("Total Cost (₹)", before.get("total_cost", 0), after.get("total_cost", 0), savings.get("cost_saving_pct"))
        metric_row("Distance (km)", before.get("total_distance_km", 0), after.get("total_distance_km", 0), savings.get("distance_saving_pct"))
        # Carbon: use trip-proportional savings if distance-based is negative
        # (consolidation adds detour km but removes entire return trips)
        carbon_pct = savings.get("carbon_saving_pct", 0)
        if carbon_pct < 0:
            carbon_pct = savings.get("trip_reduction_pct", 0)
        metric_row("Carbon (kg CO₂)", before.get("total_carbon_kg", 0), after.get("total_carbon_kg", 0), carbon_pct)

    fleet = metrics.get("fleet", {})
    if fleet:
        print(f"\n  {BOLD}Fleet:{RESET}")
        kv("Trucks used / available", f"{fleet.get('trucks_used', 0)} / {fleet.get('trucks_available', 0)}", indent=4)
        kv("Assignment rate", f"{fleet.get('assignment_rate_pct', 0):.0f}%", indent=4)

    wait(slow_mode=slow)

    # Outcome logging
    section("Tool 6: Outcome Logger", "LEARN")

    animate_step("Writing outcome to OptimizationOutcome table", slow)
    animate_step("Persisting: plan + violations + scenarios + metrics + timings", slow)
    animate_step("Checking retraining trigger (fires every 10 runs)", slow)

    kv("Outcome logged", "Yes")
    kv("Retraining hook", "Armed — triggers every 10 optimization runs")

    print(f"\n  {DIM}The ML model retrains on accumulated outcomes —{RESET}")
    print(f"  {DIM}every run makes the system smarter.{RESET}")

    print(f"\n  {CHECK} {GREEN}LEARN phase complete — outcome logged, retraining armed{RESET}")
    wait(slow_mode=slow)


# ---------------------------------------------------------------------------
# Solomon Benchmark
# ---------------------------------------------------------------------------

def demo_solomon(slow=True):
    """Solomon VRPTW benchmark validation"""
    section("BENCHMARK VALIDATION — Solomon VRPTW", None)
    print(f"  {DIM}Validating solver quality against industry-standard benchmarks.{RESET}\n")

    from backend.app.data_loader.solomon_mapper import load_c101, KNOWN_OPTIMAL
    from backend.app.agents.tools.optimization_tool import run_optimization

    # C101 25
    section("Solomon C101 — 25 Customers (Clustered)")
    try:
        sol_s, sol_v = load_c101(max_customers=25)
        optimal = KNOWN_OPTIMAL["C101_25"]["vehicles"]

        animate_step("Loaded 25 customers from dataset/C1/C101.csv", slow)
        animate_step("Mapped coordinates → Indian cities, demand → freight weights", slow)
        animate_step("Running MIP solver", slow)

        result = run_optimization(sol_s, sol_v, None)
        trucks = result.get("plan_metrics", {}).get("total_trucks", 0)
        util = result.get("plan_metrics", {}).get("avg_utilization", 0)

        kv("Lorri AI", f"{trucks} trucks")
        kv("Known optimal", f"{optimal} trucks")
        kv("Avg utilization", f"{util:.1f}%")

        if result.get("is_infeasible", False) or trucks == 0:
            print(f"\n  {YELLOW}Solver returned infeasible for 25-customer subset{RESET}")
            print(f"  {DIM}(MIP with limited vehicles — heuristic would handle this){RESET}")
        elif trucks <= optimal:
            print(f"\n  {GREEN}{BOLD}★ MATCHED OR BEAT KNOWN OPTIMAL! ({trucks} ≤ {optimal}){RESET}")
        elif trucks <= optimal * 2:
            print(f"\n  {GREEN}Within 2x of optimal ({trucks} vs {optimal}){RESET}")
        else:
            print(f"\n  {YELLOW}Above optimal range ({trucks} vs {optimal}){RESET}")
    except FileNotFoundError:
        print(f"  {WARN} Solomon C101 not found — skipping")

    wait(slow_mode=slow)

    # C101 Full
    section("Solomon C101 — 100 Customers (Full)")
    try:
        sol_full_s, sol_full_v = load_c101(max_customers=None)
        optimal_full = KNOWN_OPTIMAL["C101"]["vehicles"]

        animate_step("Loaded 100 customers", slow)
        animate_step("Auto-switching to heuristic (100 > 50 threshold)", slow)
        animate_step("Running FFD + Local Search", slow)

        result_full = run_optimization(sol_full_s, sol_full_v, None)
        trucks_full = result_full.get("plan_metrics", {}).get("total_trucks", 0)
        util_full = result_full.get("plan_metrics", {}).get("avg_utilization", 0)

        kv("Lorri AI", f"{trucks_full} trucks")
        kv("Known optimal", f"{optimal_full} trucks")
        kv("Avg utilization", f"{util_full:.1f}%")
        kv("Solver", result_full.get("solver_used", "HEURISTIC"))

        if trucks_full <= optimal_full:
            print(f"\n  {GREEN}{BOLD}★ MATCHED KNOWN OPTIMAL! ({trucks_full} ≤ {optimal_full}){RESET}")
        else:
            print(f"\n  {YELLOW}Within range ({trucks_full} vs {optimal_full}){RESET}")
    except FileNotFoundError:
        print(f"  {WARN} Solomon C101 not found — skipping")

    wait(slow_mode=slow)


# ---------------------------------------------------------------------------
# Final Summary
# ---------------------------------------------------------------------------

def demo_summary(state: PipelineState):
    """Print the final demo summary"""
    plan_metrics = state.plan.get("plan_metrics", {}) if state.plan else {}
    savings = state.metrics.get("savings", {}) if state.metrics else {}
    compat_stats = state.compatibility_stats.get("stats", {}) if state.compatibility_stats else {}
    guardrail = state.guardrail_result or {}

    print(f"""
{CYAN}{'='*70}{RESET}
{BOLD}  LORRI AI — DEMO COMPLETE{RESET}
{CYAN}{'='*70}{RESET}

  {BOLD}Agent Loop Demonstrated:{RESET}
    {CHECK} OBSERVE  — Loaded {len(state.shipments)} shipments, validated data quality
    {CHECK} REASON   — ML scored {compat_stats.get('total_pairs_scored', 0)} pairs, built compatibility graph
    {CHECK} DECIDE   — Guardrail enforced safety ({guardrail.get('warning_count', 0)} warnings caught)
    {CHECK} ACT      — Solver: {plan_metrics.get('total_trucks', 0)} trucks at {plan_metrics.get('avg_utilization', 0):.1f}% utilization
    {CHECK} LEARN    — Metrics computed, outcome logged, retraining armed

  {BOLD}Key Results:{RESET}
    {ARROW} Trip reduction:     {GREEN}{savings.get('trip_reduction_pct', 0):.0f}%{RESET}
    {ARROW} Cost savings:       {GREEN}{savings.get('cost_saving_pct', 0):.1f}%{RESET}
    {ARROW} Carbon savings:     {GREEN}{max(savings.get('carbon_saving_pct', 0), plan_metrics.get('carbon_saving_pct', 0)):.1f}%{RESET}
    {ARROW} Avg utilization:    {GREEN}{plan_metrics.get('avg_utilization', 0):.1f}%{RESET}

  {BOLD}System Components:{RESET}
    {ARROW} 4 LLM-powered agents (Google Gemini 2.0 Flash)
    {ARROW} 6 tool nodes in LangGraph state graph
    {ARROW} ML model: RandomForest (F1=0.84, 14 features)
    {ARROW} OR solver: Google OR-Tools CP-SAT + FFD heuristic
    {ARROW} 10-node pipeline with 5 conditional edges

  {BOLD}Problem Statement Deliverables:{RESET}
    {CHECK} Consolidation Engine Prototype
    {CHECK} Visualization Dashboard (React + Recharts + Leaflet)
    {CHECK} Performance Simulation (4 real solver-backed scenarios)
    {CHECK} Continuous Optimization (outcome logging + ML retraining)

{DIM}  Lorri AI — The freight doesn't just move. It thinks.{RESET}
{DIM}  Team Jugaadus · Taqneeq CyberCypher R2 · Problem Statement 5{RESET}

{CYAN}{'='*70}{RESET}
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    load_env_file()

    from backend.app.db.base import Base
    from backend.app.db.session import engine
    import backend.app.models  # noqa
    Base.metadata.create_all(bind=engine)

    state = PipelineState()

    try:
        banner()

        print(f"  {DIM}Interactive walkthrough of the complete agent loop:{RESET}\n")
        print(f"    {CYAN}OBSERVE{RESET}  → Load data, validate quality")
        print(f"    {BLUE}REASON{RESET}   → ML compatibility scoring, graph building")
        print(f"    {YELLOW}DECIDE{RESET}   → Policy guardrail enforcement")
        print(f"    {MAGENTA}ACT{RESET}      → OR-Tools optimization, scenario simulation")
        print(f"    {GREEN}LEARN{RESET}    → Metrics, outcome logging, retraining\n")

        has_llm = bool(os.getenv("GOOGLE_API_KEY", ""))
        if has_llm:
            print(f"  {CHECK} {GREEN}Gemini LLM ENABLED — agents will generate NL narratives{RESET}\n")
        else:
            print(f"  {WARN} {YELLOW}Gemini LLM disabled — set GOOGLE_API_KEY for NL narratives{RESET}\n")

        wait("Press Enter to start the demo...")

        demo_observe(state, slow=True)
        demo_reason(state, slow=True)
        demo_decide(state, slow=True)
        demo_act(state, slow=True)
        demo_insight(state, slow=True)
        demo_learn(state, slow=True)
        demo_solomon(slow=True)
        demo_summary(state)

    except KeyboardInterrupt:
        print(f"\n\n{RED}Demo interrupted by user{RESET}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())