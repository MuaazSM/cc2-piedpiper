"""
OR-Tools MIP Solver — Core optimization engine for load consolidation.

Formulates the shipment-to-vehicle assignment as a Mixed Integer Program:
- Decision variable: x[i,k] = 1 if shipment i is assigned to truck k
- Objective: minimize Σ TripCost_k · y_k − α · Utilization_k
  where y_k = 1 if truck k is used (has any shipments)
- Constraints:
  1. Weight capacity per truck
  2. Volume capacity per truck
  3. Each shipment assigned exactly once
  4. Compatibility: only compatible pairs can share a truck

Uses Google OR-Tools CP-SAT solver which handles binary integer programs
efficiently. For instances >50 shipments, the optimization tool falls
back to the heuristic in heuristic.py instead of calling this solver.

This module provides the core formulation. Rajkumar can enhance it with:
- Time window feasibility constraints
- Route detour limits
- Multi-objective weighting
- Warm-starting from heuristic solutions
"""

from typing import List, Dict, Optional
import networkx as nx
from backend.app.optimizer.baseline import compute_baseline

# Try importing OR-Tools — if not installed, the tool will fall back to heuristic
try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    print("[OR Solver] OR-Tools not installed. Will use heuristic fallback.")


def solve_mip(
    shipments: List[Dict],
    vehicles: List[Dict],
    compatibility_graph: Optional[nx.Graph] = None,
    alpha: float = 0.1,
    time_limit_seconds: int = 30,
) -> Dict:
    """
    Solve the load consolidation problem using OR-Tools CP-SAT.

    Args:
        shipments: List of shipment dicts with shipment_id, weight, volume
        vehicles: List of vehicle dicts with vehicle_id, capacity_weight,
                  capacity_volume, operating_cost
        compatibility_graph: networkx Graph where edges = compatible pairs.
                            If None, all pairs are considered compatible.
        alpha: Weight for utilization bonus in objective (higher = favor fuller trucks)
        time_limit_seconds: Max solver runtime before returning best found solution

    Returns:
        Dict with assigned, unassigned, is_infeasible, plan_metrics,
        and solver_status
    """
    if not ORTOOLS_AVAILABLE:
        return {
            "assigned": [],
            "unassigned": shipments,
            "is_infeasible": True,
            "plan_metrics": _empty_metrics(shipments),
            "solver_status": "OR-Tools not installed",
        }

    n_shipments = len(shipments)
    n_vehicles = len(vehicles)

    if n_shipments == 0 or n_vehicles == 0:
        return {
            "assigned": [],
            "unassigned": shipments,
            "is_infeasible": True,
            "plan_metrics": _empty_metrics(shipments),
            "solver_status": "Empty input",
        }

    model = cp_model.CpModel()

    #  Decision variables 

    # x[i][k] = 1 if shipment i is assigned to vehicle k
    x = {}
    for i in range(n_shipments):
        for k in range(n_vehicles):
            x[i, k] = model.NewBoolVar(f"x_{i}_{k}")

    # y[k] = 1 if vehicle k is used (has at least one shipment)
    y = {}
    for k in range(n_vehicles):
        y[k] = model.NewBoolVar(f"y_{k}")

    #  Constraints 

    # Constraint 1: Each shipment assigned to exactly one vehicle
    for i in range(n_shipments):
        model.Add(sum(x[i, k] for k in range(n_vehicles)) == 1)

    # Constraint 2: Weight capacity per vehicle
    for k in range(n_vehicles):
        cap_w = int(vehicles[k].get("capacity_weight", 0))
        model.Add(
            sum(
                int(shipments[i].get("weight", 0)) * x[i, k]
                for i in range(n_shipments)
            ) <= cap_w
        )

    # Constraint 3: Volume capacity per vehicle
    # Scale volume to integers (multiply by 100) since CP-SAT needs integers
    for k in range(n_vehicles):
        cap_v = int(vehicles[k].get("capacity_volume", 0) * 100)
        model.Add(
            sum(
                int(shipments[i].get("volume", 0) * 100) * x[i, k]
                for i in range(n_shipments)
            ) <= cap_v
        )



    # Constraint 4: Link y[k] to x[i,k] — y[k] = 1 if any shipment assigned to k
    for k in range(n_vehicles):
        # If any x[i,k] = 1, then y[k] must be 1
        model.Add(sum(x[i, k] for i in range(n_shipments)) >= 1).OnlyEnforceIf(y[k])
        model.Add(sum(x[i, k] for i in range(n_shipments)) == 0).OnlyEnforceIf(y[k].Not())

    # Constraint 5: Compatibility — CONFLICTING pairs cannot share a vehicle.
    #
    # IMPORTANT: The compatibility graph represents RECOMMENDED pairings,
    # not REQUIRED restrictions. The absence of an edge does NOT mean
    # two shipments can't share a truck — it just means the ML model
    # didn't flag them as strong consolidation candidates.
    #
    # We only add constraints for pairs that are EXPLICITLY incompatible:
    # - Handling conflicts (hazardous + fragile, etc.)
    # - Zero time window overlap
    #
    # This is a key distinction: the graph is a POSITIVE signal (these
    # pairs are good candidates), not a NEGATIVE constraint (these pairs
    # are forbidden). The solver is free to put any non-conflicting
    # shipments on the same truck if capacity allows.
    from datetime import datetime as dt_class

    def _parse(val):
        if val is None:
            return None
        if isinstance(val, dt_class):
            return val
        if isinstance(val, str):
            try:
                return dt_class.fromisoformat(val)
            except ValueError:
                return None
        return None

    for i in range(n_shipments):
        for j in range(i + 1, n_shipments):
            sid_i = shipments[i].get("shipment_id", "")
            sid_j = shipments[j].get("shipment_id", "")

            # Check 1: Explicit handling conflicts
            h_i = shipments[i].get("special_handling") or "none"
            h_j = shipments[j].get("special_handling") or "none"

            is_handling_conflict = False
            if h_i != "none" and h_j != "none":
                conflict_pairs = {
                    frozenset({"hazardous", "fragile"}),
                    frozenset({"hazardous", "refrigerated"}),
                    frozenset({"hazardous", "oversized"}),
                }
                if frozenset({h_i, h_j}) in conflict_pairs:
                    is_handling_conflict = True

            # Check 2: Time window overlap
            # If time windows don't overlap, they physically can't share a truck
            has_time_conflict = False
            pt_i = _parse(shipments[i].get("pickup_time"))
            dt_i = _parse(shipments[i].get("delivery_time"))
            pt_j = _parse(shipments[j].get("pickup_time"))
            dt_j = _parse(shipments[j].get("delivery_time"))

            if all([pt_i, dt_i, pt_j, dt_j]):
                # Two shipments can share a truck only if their time windows overlap.
                # Check if the latest pickup is before the earliest delivery.
                latest_pickup = max(pt_i, pt_j)
                earliest_delivery = min(dt_i, dt_j)
                if latest_pickup >= earliest_delivery:
                    # No overlap — they can't share a truck
                    has_time_conflict = True

            # Apply constraint if either conflict exists
            if is_handling_conflict or has_time_conflict:
                for k in range(n_vehicles):
                    model.Add(x[i, k] + x[j, k] <= 1)

    #  Objective 
    # Minimize: Σ operating_cost_k · y_k − α · Σ (weight_i · x[i,k]) / capacity_k
    # The first term minimizes cost, the second rewards higher utilization.
    # We scale everything to integers for CP-SAT.

    COST_SCALE = 100  # Scale costs to avoid floating point
    UTIL_SCALE = 100

    objective_terms = []

    # Cost term: penalize using a truck
    for k in range(n_vehicles):
        cost = int(vehicles[k].get("operating_cost", 0) * COST_SCALE)
        objective_terms.append(cost * y[k])

    # Utilization bonus: reward loading trucks fuller (negative = bonus)
    alpha_scaled = int(alpha * UTIL_SCALE)
    for k in range(n_vehicles):
        cap_w = vehicles[k].get("capacity_weight", 1)
        for i in range(n_shipments):
            weight = shipments[i].get("weight", 0)
            # Utilization contribution: weight / capacity, scaled to integer
            util_contrib = int((weight / cap_w) * UTIL_SCALE) if cap_w > 0 else 0
            objective_terms.append(-alpha_scaled * util_contrib * x[i, k])

    model.Minimize(sum(objective_terms))

    #  Solve 
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    # Use multiple workers for parallel search
    solver.parameters.num_workers = 4

    status = solver.Solve(model)

    #  Parse solution 
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return _parse_solution(
            solver, x, y, shipments, vehicles, status, compatibility_graph
        )
    else:
        # Infeasible or no solution found within time limit
        status_name = {
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.MODEL_INVALID: "MODEL_INVALID",
            cp_model.UNKNOWN: "TIMEOUT",
        }.get(status, "UNKNOWN")

        print(f"[OR Solver] No solution found. Status: {status_name}")

        return {
            "assigned": [],
            "unassigned": shipments,
            "is_infeasible": True,
            "plan_metrics": _empty_metrics(shipments),
            "solver_status": status_name,
        }


def _parse_solution(
    solver,
    x: Dict,
    y: Dict,
    shipments: List[Dict],
    vehicles: List[Dict],
    status: int,
    compatibility_graph: Optional[nx.Graph],
) -> Dict:
    """
    Extract the assignment from the solved CP-SAT model.

    Reads the decision variable values, builds assignment dicts
    with utilization percentages, and computes plan-level metrics.
    """
    n_shipments = len(shipments)
    n_vehicles = len(vehicles)

    assigned = []
    assigned_shipment_ids = set()
    vehicle_lookup = {v["vehicle_id"]: v for v in vehicles}

    for k in range(n_vehicles):
        if not solver.Value(y[k]):
            continue  # Truck not used

        # Collect shipments assigned to this truck
        truck_shipments = []
        for i in range(n_shipments):
            if solver.Value(x[i, k]):
                truck_shipments.append(shipments[i])
                assigned_shipment_ids.add(shipments[i].get("shipment_id", ""))

        if not truck_shipments:
            continue

        vehicle = vehicles[k]
        cap_w = vehicle.get("capacity_weight", 1)
        cap_v = vehicle.get("capacity_volume", 1)
        total_w = sum(s.get("weight", 0) for s in truck_shipments)
        total_v = sum(s.get("volume", 0) for s in truck_shipments)

        # Utilization = binding constraint (whichever is tighter)
        util_w = (total_w / cap_w) * 100 if cap_w > 0 else 0
        util_v = (total_v / cap_v) * 100 if cap_v > 0 else 0
        utilization = max(util_w, util_v)

        # Estimate route detour based on unique origin-destination pairs
        from backend.app.data_loader.synthetic_generator import get_distance
        origins = set(s.get("origin", "") for s in truck_shipments)
        destinations = set(s.get("destination", "") for s in truck_shipments)
        detour = 0.0
        if len(origins) > 1 or len(destinations) > 1:
            # Rough detour: sum of inter-city distances for pickups + deliveries
            origin_list = list(origins)
            for idx in range(len(origin_list) - 1):
                detour += get_distance(origin_list[idx], origin_list[idx + 1])
            dest_list = list(destinations)
            for idx in range(len(dest_list) - 1):
                detour += get_distance(dest_list[idx], dest_list[idx + 1])

        assigned.append({
            "vehicle_id": vehicle["vehicle_id"],
            "shipment_ids": [s.get("shipment_id", "") for s in truck_shipments],
            "utilization_pct": round(utilization, 1),
            "route_detour_km": round(detour, 1),
        })

    # Find unassigned shipments
    unassigned = [
        s for s in shipments
        if s.get("shipment_id", "") not in assigned_shipment_ids
    ]

    # Compute plan metrics
    total_trucks = len(assigned)
    trips_baseline = len(shipments)
    utilizations = [a["utilization_pct"] for a in assigned]
    avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0

    # Compute savings against baseline
    from backend.app.optimizer.baseline import compute_baseline
    baseline = compute_baseline(shipments, vehicles)

    consolidated_cost = sum(
        vehicle_lookup.get(a["vehicle_id"], {}).get("operating_cost", 0)
        for a in assigned
    )
    cost_saving_pct = (
        (baseline["total_cost"] - consolidated_cost) / baseline["total_cost"] * 100
    ) if baseline["total_cost"] > 0 else 0

    carbon_saving_pct = (
        (baseline["total_trips"] - total_trucks) / baseline["total_trips"] * 100
    ) if baseline["total_trips"] > 0 else 0

    status_name = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"
    print(f"[OR Solver] Solution found ({status_name}): {total_trucks} trucks, "
          f"{avg_utilization:.1f}% avg utilization, {cost_saving_pct:.1f}% cost savings")

    return {
        "assigned": assigned,
        "unassigned": unassigned,
        "is_infeasible": False,
        "plan_metrics": {
            "total_trucks": total_trucks,
            "trips_baseline": trips_baseline,
            "avg_utilization": round(avg_utilization, 1),
            "cost_saving_pct": round(cost_saving_pct, 1),
            "carbon_saving_pct": round(carbon_saving_pct, 1),
        },
        "solver_status": status_name,
    }


def _empty_metrics(shipments: List[Dict]) -> Dict:
    """Return empty metrics when no solution exists."""
    return {
        "total_trucks": 0,
        "trips_baseline": len(shipments),
        "avg_utilization": 0.0,
        "cost_saving_pct": 0.0,
        "carbon_saving_pct": 0.0,
    }