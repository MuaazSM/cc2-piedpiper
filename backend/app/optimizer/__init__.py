"""
Optimizer Package — OR-Tools MIP solver + heuristic fallback.

This is the clean public API for the optimization engine. All external
code (LangGraph tool nodes, API routes, tests) should import from here.

Public API:
-----------

    from backend.app.optimizer import solve, compute_metrics, compute_baseline_metrics

    # Run the solver (auto-selects MIP vs heuristic based on instance size)
    result = solve(shipments, vehicles, compatibility_graph)
    # Returns: {
    #   "assigned": [{"vehicle_id": "V1", "shipment_ids": ["S1","S2"], "utilization_pct": 85.0, ...}],
    #   "unassigned": [...],
    #   "is_infeasible": False,
    #   "plan_metrics": {"total_trucks": 5, "avg_utilization": 82.3, ...},
    #   "solver_used": "MIP" | "HEURISTIC",
    #   "solver_status": "OPTIMAL" | "FEASIBLE" | "HEURISTIC_COMPLETE",
    # }

    # Compute full before/after metrics
    metrics = compute_metrics(result["assigned"], shipments, vehicles)
    # Returns: {
    #   "before": {"total_trips": 20, "total_cost": 160000, "total_carbon_kg": 4800, ...},
    #   "after": {"total_trips": 8, "total_cost": 64000, "total_carbon_kg": 2100, ...},
    #   "savings": {"trip_reduction_pct": 60.0, "cost_saving_pct": 60.0, "carbon_saving_pct": 56.3, ...},
    #   "fleet": {"trucks_used": 8, "trucks_available": 10, ...},
    #   "per_truck": [{"vehicle_id": "V1", "shipment_count": 3, "utilization_pct": 88.5, ...}],
    # }

    # Compute baseline only (no consolidation reference point)
    baseline = compute_baseline_metrics(shipments, vehicles)

Function signatures:
-------------------

solve(
    shipments: List[Dict],     # Shipment dicts with shipment_id, weight, volume, etc.
    vehicles: List[Dict],      # Vehicle dicts with vehicle_id, capacity_weight, etc.
    compatibility_graph: Optional[nx.Graph] = None,  # From ML model
    alpha: float = 0.1,        # Utilization bonus weight in objective
    time_limit_seconds: int = 30,  # MIP solver timeout
) -> Dict

compute_metrics(
    assignments: List[Dict],   # From solve() result["assigned"]
    shipments: List[Dict],
    vehicles: List[Dict],
) -> Dict

compute_baseline_metrics(
    shipments: List[Dict],
    vehicles: List[Dict],
) -> Dict
"""

from backend.app.agents.tools.optimization_tool import run_optimization as solve
from backend.app.optimizer.metrics import compute_full_metrics as compute_metrics
from backend.app.optimizer.baseline import compute_baseline as compute_baseline_metrics

__all__ = [
    "solve",
    "compute_metrics",
    "compute_baseline_metrics",
]