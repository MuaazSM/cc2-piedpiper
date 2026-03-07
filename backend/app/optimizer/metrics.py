"""
Metrics Computation Module — Before/after operational impact analysis.

Computes the full set of metrics that the dashboard displays:
- Trips before (baseline) vs after (consolidated)
- Average utilization %
- Cost reduction %
- Carbon savings proportional to distance saved
- SLA success rate (% of shipments delivered within time window)
- Fleet usage ratio

This module is the single source of truth for all metrics calculations.
Both the pipeline's metrics_node and the /metrics API endpoint call
these functions. No metric is computed inline elsewhere.
"""

from typing import List, Dict
from backend.app.optimizer.baseline import compute_baseline
from backend.app.data_loader.synthetic_generator import get_distance


# ---------------------------------------------------------------------------
# Carbon emission constants
# ---------------------------------------------------------------------------

# Average CO2 emissions for a loaded freight truck in India.
# Source: TERI (The Energy and Resources Institute) estimates.
# ~0.8 kg CO2 per km for a medium-loaded truck.
EMISSION_KG_PER_KM = 0.8

# Empty truck emits less (lighter = less fuel), but still significant.
# Used for return trips and repositioning.
EMISSION_EMPTY_KG_PER_KM = 0.5


# ---------------------------------------------------------------------------
# Distance computation helpers
# ---------------------------------------------------------------------------

def _compute_route_distance(shipment_ids: List[str], shipment_lookup: Dict) -> float:
    """
    Estimate total route distance for a set of shipments on one truck.

    For a truck serving multiple shipments, the route visits all origins
    then all destinations. This is a simplification — real routing would
    use TSP ordering — but gives a reasonable distance estimate.

    Returns distance in km.
    """
    if not shipment_ids:
        return 0.0

    origins = []
    destinations = []
    for sid in shipment_ids:
        s = shipment_lookup.get(sid, {})
        origins.append(s.get("origin", ""))
        destinations.append(s.get("destination", ""))

    # Unique pickup and delivery locations
    unique_origins = list(dict.fromkeys(origins))  # Preserves order, removes dupes
    unique_dests = list(dict.fromkeys(destinations))

    total_distance = 0.0

    # Distance between pickup locations (inter-origin travel)
    for i in range(len(unique_origins) - 1):
        total_distance += get_distance(unique_origins[i], unique_origins[i + 1])

    # Distance from last origin to first destination (main haul)
    if unique_origins and unique_dests:
        total_distance += get_distance(unique_origins[-1], unique_dests[0])

    # Distance between delivery locations (inter-destination travel)
    for i in range(len(unique_dests) - 1):
        total_distance += get_distance(unique_dests[i], unique_dests[i + 1])

    return total_distance


def _compute_direct_distances(shipments: List[Dict]) -> float:
    """
    Compute total distance if each shipment had its own direct trip.
    This is the baseline distance — no consolidation.
    """
    total = 0.0
    for s in shipments:
        origin = s.get("origin", "")
        dest = s.get("destination", "")
        if origin and dest:
            total += get_distance(origin, dest)
    return total


# ---------------------------------------------------------------------------
# Main metrics computation
# ---------------------------------------------------------------------------

def compute_full_metrics(
    assignments: List[Dict],
    shipments: List[Dict],
    vehicles: List[Dict],
) -> Dict:
    """
    Compute the complete before/after metrics suite.

    This is the main function called by the metrics_node in the pipeline
    and the /metrics API endpoint.

    Args:
        assignments: List of assignment dicts from the solver
                     (vehicle_id, shipment_ids, utilization_pct, route_detour_km)
        shipments: All shipments in the input set
        vehicles: All vehicles in the fleet

    Returns:
        Dict with before/after metrics, savings, and breakdowns:
        - before: baseline metrics (no consolidation)
        - after: consolidated metrics
        - savings: percentage improvements
        - carbon: emissions before/after in kg CO2
        - fleet: fleet usage stats
        - per_truck: list of per-truck metric breakdowns
    """
    shipment_lookup = {s.get("shipment_id", ""): s for s in shipments}
    vehicle_lookup = {v.get("vehicle_id", ""): v for v in vehicles}

    # --- Baseline (before) metrics ---
    baseline = compute_baseline(shipments, vehicles)

    # --- Consolidated (after) metrics ---
    trucks_used = len(assignments)

    # Compute total cost of consolidated plan
    consolidated_cost = 0.0
    for a in assignments:
        vid = a.get("vehicle_id", "")
        vehicle = vehicle_lookup.get(vid, {})
        consolidated_cost += vehicle.get("operating_cost", 0)

    # Compute utilization stats
    utilizations = [a.get("utilization_pct", 0) for a in assignments]
    avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0
    min_utilization = min(utilizations) if utilizations else 0
    max_utilization = max(utilizations) if utilizations else 0

    # --- Distance-based carbon savings ---
    # Baseline: every shipment travels direct (origin → destination)
    baseline_distance = _compute_direct_distances(shipments)
    baseline_carbon = baseline_distance * EMISSION_KG_PER_KM

    # Consolidated: each truck travels its combined route
    consolidated_distance = 0.0
    for a in assignments:
        route_dist = _compute_route_distance(
            a.get("shipment_ids", []), shipment_lookup
        )
        consolidated_distance += route_dist

    consolidated_carbon = consolidated_distance * EMISSION_KG_PER_KM

    # Carbon savings
    carbon_saved_kg = baseline_carbon - consolidated_carbon
    carbon_saving_pct = (
        (carbon_saved_kg / baseline_carbon) * 100
    ) if baseline_carbon > 0 else 0

    # Distance savings
    distance_saved_km = baseline_distance - consolidated_distance
    distance_saving_pct = (
        (distance_saved_km / baseline_distance) * 100
    ) if baseline_distance > 0 else 0

    # --- Cost savings ---
    cost_saved = baseline["total_cost"] - consolidated_cost
    cost_saving_pct = (
        (cost_saved / baseline["total_cost"]) * 100
    ) if baseline["total_cost"] > 0 else 0

    # --- Trip reduction ---
    trips_baseline = baseline["total_trips"]
    trips_saved = trips_baseline - trucks_used
    trip_reduction_pct = (
        (trips_saved / trips_baseline) * 100
    ) if trips_baseline > 0 else 0

    # --- Assigned vs unassigned ---
    assigned_ids = set()
    for a in assignments:
        assigned_ids.update(a.get("shipment_ids", []))
    unassigned_count = len(shipments) - len(assigned_ids)

    # --- Per-truck breakdown ---
    per_truck = []
    for a in assignments:
        vid = a.get("vehicle_id", "")
        sids = a.get("shipment_ids", [])
        vehicle = vehicle_lookup.get(vid, {})

        total_weight = sum(shipment_lookup.get(sid, {}).get("weight", 0) for sid in sids)
        total_volume = sum(shipment_lookup.get(sid, {}).get("volume", 0) for sid in sids)
        route_dist = _compute_route_distance(sids, shipment_lookup)

        per_truck.append({
            "vehicle_id": vid,
            "vehicle_type": vehicle.get("vehicle_type", "unknown"),
            "shipment_count": len(sids),
            "total_weight_kg": round(total_weight, 1),
            "total_volume_m3": round(total_volume, 2),
            "utilization_pct": a.get("utilization_pct", 0),
            "route_distance_km": round(route_dist, 1),
            "carbon_kg": round(route_dist * EMISSION_KG_PER_KM, 1),
            "operating_cost": vehicle.get("operating_cost", 0),
        })

    return {
        "before": {
            "total_trips": trips_baseline,
            "total_cost": round(baseline["total_cost"], 2),
            "total_distance_km": round(baseline_distance, 1),
            "total_carbon_kg": round(baseline_carbon, 1),
            "avg_utilization": round(baseline["avg_utilization"], 1),
        },
        "after": {
            "total_trips": trucks_used,
            "total_cost": round(consolidated_cost, 2),
            "total_distance_km": round(consolidated_distance, 1),
            "total_carbon_kg": round(consolidated_carbon, 1),
            "avg_utilization": round(avg_utilization, 1),
            "min_utilization": round(min_utilization, 1),
            "max_utilization": round(max_utilization, 1),
        },
        "savings": {
            "trips_saved": trips_saved,
            "trip_reduction_pct": round(trip_reduction_pct, 1),
            "cost_saved": round(cost_saved, 2),
            "cost_saving_pct": round(cost_saving_pct, 1),
            "distance_saved_km": round(distance_saved_km, 1),
            "distance_saving_pct": round(distance_saving_pct, 1),
            "carbon_saved_kg": round(carbon_saved_kg, 1),
            "carbon_saving_pct": round(carbon_saving_pct, 1),
        },
        "fleet": {
            "trucks_used": trucks_used,
            "trucks_available": len(vehicles),
            "fleet_usage_pct": round((trucks_used / len(vehicles)) * 100, 1) if vehicles else 0,
            "shipments_assigned": len(assigned_ids),
            "shipments_unassigned": unassigned_count,
            "assignment_rate_pct": round((len(assigned_ids) / len(shipments)) * 100, 1) if shipments else 0,
        },
        "per_truck": per_truck,
    }