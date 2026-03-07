"""
Optimization Tool — LangGraph tool node for the Act phase.

Wraps the OR-Tools MIP solver and the heuristic fallback. Decides which
solver to use based on instance size, runs it, and packages the results
for AgentState.

Decision logic:
- ≤50 shipments → OR-Tools CP-SAT (exact MIP solution)
- >50 shipments → First-Fit Decreasing + Local Search (fast heuristic)
- OR-Tools not installed → always use heuristic

The tool reads the compatibility graph from the Reason phase and passes
it to the solver as a constraint — only compatible pairs can share a truck.
"""

from typing import List, Dict, Optional
import networkx as nx


# Threshold for switching from MIP to heuristic.
# MIP is exact but slow on large instances. 50 is a reasonable cutoff
# where CP-SAT typically solves within the time limit.
MIP_THRESHOLD = 50


def run_optimization(
    shipments: List[Dict],
    vehicles: List[Dict],
    compatibility_graph: Optional[nx.Graph] = None,
    alpha: float = 0.1,
    time_limit_seconds: int = 30,
) -> Dict:
    """
    Run the appropriate solver and return the consolidation plan.

    This is the main function called by the LangGraph pipeline node.
    It picks MIP vs heuristic, runs it, and returns a consistent
    output format regardless of which solver was used.

    Args:
        shipments: List of shipment dicts from AgentState
        vehicles: List of vehicle dicts from AgentState
        compatibility_graph: networkx Graph from the Reason phase
        alpha: Utilization bonus weight in MIP objective
        time_limit_seconds: Max solver runtime for MIP

    Returns:
        Dict with:
        - assigned: list of assignment dicts (vehicle_id, shipment_ids, utilization_pct)
        - unassigned: list of shipment dicts that couldn't be placed
        - is_infeasible: True if no valid plan found
        - plan_metrics: summary stats (total_trucks, avg_utilization, savings %)
        - solver_used: "MIP" or "HEURISTIC"
        - solver_status: solver-specific status string
    """
    n = len(shipments)

    if n == 0:
        return {
            "assigned": [],
            "unassigned": [],
            "is_infeasible": False,
            "plan_metrics": {
                "total_trucks": 0, "trips_baseline": 0,
                "avg_utilization": 0.0, "cost_saving_pct": 0.0, "carbon_saving_pct": 0.0,
            },
            "solver_used": "NONE",
            "solver_status": "No shipments to optimize",
        }

    # Decide which solver to use
    use_mip = n <= MIP_THRESHOLD

    # Check if OR-Tools is available
    if use_mip:
        try:
            from backend.app.optimizer.solver import ORTOOLS_AVAILABLE
            if not ORTOOLS_AVAILABLE:
                use_mip = False
                print(f"[Optimization Tool] OR-Tools not available, falling back to heuristic")
        except ImportError:
            use_mip = False

    if use_mip:
        print(f"[Optimization Tool] Using MIP solver for {n} shipments "
              f"({len(vehicles)} vehicles, {time_limit_seconds}s limit)")

        from backend.app.optimizer.solver import solve_mip
        result = solve_mip(
            shipments=shipments,
            vehicles=vehicles,
            compatibility_graph=compatibility_graph,
            alpha=alpha,
            time_limit_seconds=time_limit_seconds,
        )
        result["solver_used"] = "MIP"

    else:
        print(f"[Optimization Tool] Using heuristic for {n} shipments "
              f"({len(vehicles)} vehicles)")

        from backend.app.optimizer.heuristic import first_fit_decreasing
        result = first_fit_decreasing(
            shipments=shipments,
            vehicles=vehicles,
            compatibility_graph=compatibility_graph,
        )
        result["solver_used"] = "HEURISTIC"
        result["solver_status"] = "HEURISTIC_COMPLETE"

    # Log summary
    n_assigned = len(result.get("assigned", []))
    n_unassigned = len(result.get("unassigned", []))
    metrics = result.get("plan_metrics", {})
    print(f"[Optimization Tool] Result: {n_assigned} trucks used, "
          f"{n_unassigned} unassigned, "
          f"{metrics.get('avg_utilization', 0):.1f}% avg utilization, "
          f"{metrics.get('cost_saving_pct', 0):.1f}% cost savings")

    return result