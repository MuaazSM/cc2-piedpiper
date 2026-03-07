"""
Baseline Metrics — Computes the "no consolidation" reference point.

The baseline represents what happens with zero optimization: every
shipment gets its own truck. All savings metrics (cost %, carbon %,
trip reduction %) are measured against this baseline.

This module provides a clean, reusable baseline computation that
both the MIP solver and heuristic can reference. It also powers
the "before" side of the before/after dashboard comparison.
"""

from typing import List, Dict


def compute_baseline(
    shipments: List[Dict],
    vehicles: List[Dict],
) -> Dict:
    """
    Compute the baseline scenario: 1 shipment per truck, no consolidation.

    Assigns each shipment to the cheapest vehicle that can carry it,
    then sums up the total cost, trips, and estimated carbon emissions.

    Args:
        shipments: List of shipment dicts
        vehicles: List of vehicle dicts sorted by operating_cost internally

    Returns:
        Dict with baseline metrics:
        - total_trips: one trip per shipment
        - total_cost: sum of operating costs for each trip
        - total_carbon_kg: estimated CO2 based on distance × emission factor
        - avg_utilization: average truck utilization (typically very low)
        - cost_per_shipment: average cost per shipment
    """
    if not shipments or not vehicles:
        return {
            "total_trips": len(shipments),
            "total_cost": 0.0,
            "total_carbon_kg": 0.0,
            "avg_utilization": 0.0,
            "cost_per_shipment": 0.0,
        }

    from backend.app.data_loader.synthetic_generator import get_distance

    # Sort vehicles by cost ascending — assign cheapest feasible truck to each shipment
    sorted_vehicles = sorted(vehicles, key=lambda v: v.get("operating_cost", 0))

    total_cost = 0.0
    total_carbon = 0.0
    utilizations = []

    # Carbon emission factor: kg CO2 per km for a typical truck
    # Based on average Indian freight truck emissions (~0.1 kg CO2 per ton-km)
    EMISSION_FACTOR_KG_PER_KM = 0.8  # Roughly 0.8 kg CO2 per km for a loaded truck

    for shipment in shipments:
        weight = shipment.get("weight", 0)
        volume = shipment.get("volume", 0)
        origin = shipment.get("origin", "")
        destination = shipment.get("destination", "")

        # Find the cheapest vehicle that can carry this shipment
        assigned_vehicle = None
        for v in sorted_vehicles:
            if v.get("capacity_weight", 0) >= weight and v.get("capacity_volume", 0) >= volume:
                assigned_vehicle = v
                break

        if assigned_vehicle:
            total_cost += assigned_vehicle.get("operating_cost", 0)

            # Compute utilization for this single-shipment trip
            cap_w = assigned_vehicle.get("capacity_weight", 1)
            cap_v = assigned_vehicle.get("capacity_volume", 1)
            util = max(
                (weight / cap_w) * 100 if cap_w > 0 else 0,
                (volume / cap_v) * 100 if cap_v > 0 else 0,
            )
            utilizations.append(util)
        else:
            # No vehicle can carry this shipment — use the largest truck's cost as estimate
            total_cost += sorted_vehicles[-1].get("operating_cost", 0)
            utilizations.append(0)

        # Estimate carbon: distance × emission factor
        if origin and destination:
            distance = get_distance(origin, destination)
            total_carbon += distance * EMISSION_FACTOR_KG_PER_KM

    avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0

    return {
        "total_trips": len(shipments),
        "total_cost": round(total_cost, 2),
        "total_carbon_kg": round(total_carbon, 2),
        "avg_utilization": round(avg_utilization, 1),
        "cost_per_shipment": round(total_cost / len(shipments), 2) if shipments else 0,
    }