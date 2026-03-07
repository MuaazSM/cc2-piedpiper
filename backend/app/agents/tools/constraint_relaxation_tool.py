"""
Constraint Relaxation Tool — Diagnoses solver infeasibility.

Pure Python constraint analysis that identifies WHY the solver failed
and suggests the smallest changes to make it feasible. No LLM calls —
this is deterministic rule-based analysis.

Four categories of blocking constraints:
1. Time window conflicts — shipments on same lane with non-overlapping windows
2. Capacity bottlenecks — shipments too heavy/large for any vehicle
3. Fleet gaps — not enough trucks or missing vehicle types
4. Compatibility conflicts — special handling types that can't share trucks

The LLM narrative layer lives in relaxation_agent.py — it takes
this tool's structured output and writes a human-readable summary.
"""

from datetime import datetime
from typing import List, Dict, Optional, Tuple
from backend.app.data_loader.synthetic_generator import get_distance


# ---------------------------------------------------------------------------
# Special handling conflict definitions
# ---------------------------------------------------------------------------

HANDLING_CONFLICTS = {
    frozenset({"hazardous", "fragile"}),
    frozenset({"hazardous", "refrigerated"}),
    frozenset({"hazardous", "oversized"}),
}


# ---------------------------------------------------------------------------
# Suggestion builder
# ---------------------------------------------------------------------------

def _suggestion(
    suggestion_type: str,
    priority: str,
    message: str,
    affected_shipments: Optional[List[str]] = None,
    details: Optional[Dict] = None,
) -> Dict:
    """
    Build a single relaxation suggestion.

    Each suggestion tells the user exactly what to change and why.
    The frontend can render these as actionable cards.
    """
    return {
        "type": suggestion_type,
        "priority": priority,
        "message": message,
        "affected_shipments": affected_shipments or [],
        "details": details or {},
    }


# ---------------------------------------------------------------------------
# Time parsing helper
# ---------------------------------------------------------------------------

def _parse_time(value) -> Optional[datetime]:
    """Safely parse a datetime from string or return as-is."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Time window conflict detection
# ---------------------------------------------------------------------------

def detect_time_window_conflicts(
    unassigned: List[Dict],
    all_shipments: List[Dict],
    vehicles: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """
    Find shipment pairs on the same lane that SHOULD consolidate but
    can't because their time windows don't overlap.

    Calculates exactly how many minutes of relaxation would fix each
    conflict, so the user knows the minimum change needed.
    """
    constraints = []
    suggestions = []

    # Group all shipments by lane for efficient comparison
    lanes = {}
    for s in all_shipments:
        lane_key = f"{s.get('origin', '')}→{s.get('destination', '')}"
        if lane_key not in lanes:
            lanes[lane_key] = []
        lanes[lane_key].append(s)

    for shipment in unassigned:
        sid = shipment.get("shipment_id", "UNKNOWN")
        origin = shipment.get("origin", "")
        destination = shipment.get("destination", "")
        lane_key = f"{origin}→{destination}"

        pickup = _parse_time(shipment.get("pickup_time"))
        delivery = _parse_time(shipment.get("delivery_time"))
        if not pickup or not delivery:
            continue

        lane_shipments = lanes.get(lane_key, [])
        for other in lane_shipments:
            other_id = other.get("shipment_id", "")
            if other_id == sid:
                continue

            other_pickup = _parse_time(other.get("pickup_time"))
            other_delivery = _parse_time(other.get("delivery_time"))
            if not other_pickup or not other_delivery:
                continue

            windows_overlap = (pickup <= other_delivery) and (other_pickup <= delivery)

            if not windows_overlap:
                if pickup > other_delivery:
                    gap_minutes = (pickup - other_delivery).total_seconds() / 60
                else:
                    gap_minutes = (other_pickup - delivery).total_seconds() / 60

                gap_minutes = abs(round(gap_minutes))

                constraints.append({
                    "type": "TIME_WINDOW_CONFLICT",
                    "shipment_ids": [sid, other_id],
                    "lane": lane_key,
                    "gap_minutes": gap_minutes,
                    "message": (
                        f"{sid} and {other_id} are on the same lane ({lane_key}) "
                        f"but their time windows are {gap_minutes} minutes apart."
                    ),
                })

                # Only suggest relaxation for reasonable gaps (under 4 hours)
                if gap_minutes <= 240:
                    relax_target = sid if delivery < other_delivery else other_id
                    suggestions.append(_suggestion(
                        "RELAX_WINDOW",
                        "HIGH" if gap_minutes <= 60 else "MEDIUM",
                        (
                            f"Relax {relax_target}'s delivery window by ~{gap_minutes} minutes "
                            f"to enable consolidation with {other_id if relax_target == sid else sid} "
                            f"on the {lane_key} lane."
                        ),
                        affected_shipments=[sid, other_id],
                        details={
                            "relax_shipment": relax_target,
                            "relax_minutes": gap_minutes,
                            "lane": lane_key,
                        },
                    ))

    # Deduplicate pairs
    seen_pairs = set()
    unique_constraints = []
    for c in constraints:
        pair_key = tuple(sorted(c["shipment_ids"]))
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            unique_constraints.append(c)

    seen_suggestions = set()
    unique_suggestions = []
    for s in suggestions:
        pair_key = tuple(sorted(s["affected_shipments"]))
        if pair_key not in seen_suggestions:
            seen_suggestions.add(pair_key)
            unique_suggestions.append(s)

    return unique_constraints, unique_suggestions


# ---------------------------------------------------------------------------
# Capacity bottleneck detection
# ---------------------------------------------------------------------------

def detect_capacity_bottlenecks(
    unassigned: List[Dict],
    vehicles: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """
    Find shipments that exceed the capacity of every available vehicle.
    Suggests splitting into smaller pieces that can fit.
    """
    constraints = []
    suggestions = []

    max_weight = max((v.get("capacity_weight", 0) for v in vehicles), default=0)
    max_volume = max((v.get("capacity_volume", 0) for v in vehicles), default=0)

    for shipment in unassigned:
        sid = shipment.get("shipment_id", "UNKNOWN")
        weight = shipment.get("weight", 0)
        volume = shipment.get("volume", 0)

        if weight > max_weight:
            split_count = -(-int(weight) // int(max_weight))
            split_weight = round(weight / split_count, 1)

            constraints.append({
                "type": "WEIGHT_EXCEEDS_FLEET",
                "shipment_ids": [sid],
                "message": f"{sid} weighs {weight}kg but the largest vehicle can only carry {max_weight}kg.",
            })

            suggestions.append(_suggestion(
                "SPLIT_SHIPMENT", "HIGH",
                f"Split {sid} ({weight}kg) into {split_count} shipments of ~{split_weight}kg each "
                f"to fit within vehicle capacity ({max_weight}kg max).",
                affected_shipments=[sid],
                details={"current_weight": weight, "max_vehicle_weight": max_weight,
                         "suggested_splits": split_count, "split_weight": split_weight},
            ))

        if volume > max_volume:
            split_count = -(-int(volume * 100) // int(max_volume * 100))
            split_volume = round(volume / split_count, 2)

            constraints.append({
                "type": "VOLUME_EXCEEDS_FLEET",
                "shipment_ids": [sid],
                "message": f"{sid} is {volume}m³ but the largest vehicle can only fit {max_volume}m³.",
            })

            suggestions.append(_suggestion(
                "SPLIT_SHIPMENT", "HIGH",
                f"Split {sid} ({volume}m³) into {split_count} shipments of ~{split_volume}m³ each "
                f"to fit within vehicle capacity ({max_volume}m³ max).",
                affected_shipments=[sid],
                details={"current_volume": volume, "max_vehicle_volume": max_volume,
                         "suggested_splits": split_count, "split_volume": split_volume},
            ))

    return constraints, suggestions


# ---------------------------------------------------------------------------
# Fleet gap detection
# ---------------------------------------------------------------------------

def detect_fleet_gaps(
    all_shipments: List[Dict],
    unassigned: List[Dict],
    vehicles: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """
    Check if the fleet is too small or missing required vehicle types.
    """
    constraints = []
    suggestions = []

    total_shipment_weight = sum(s.get("weight", 0) for s in all_shipments)
    total_fleet_weight = sum(v.get("capacity_weight", 0) for v in vehicles)
    avg_vehicle_weight = total_fleet_weight / len(vehicles) if vehicles else 0

    # Total capacity insufficient
    if total_shipment_weight > total_fleet_weight:
        weight_deficit = total_shipment_weight - total_fleet_weight
        additional_trucks = -(-int(weight_deficit) // int(avg_vehicle_weight)) if avg_vehicle_weight > 0 else 1

        constraints.append({
            "type": "FLEET_CAPACITY_INSUFFICIENT",
            "shipment_ids": [s.get("shipment_id") for s in unassigned],
            "message": f"Total shipment weight ({total_shipment_weight:.0f}kg) exceeds "
                       f"total fleet capacity ({total_fleet_weight:.0f}kg).",
        })

        suggestions.append(_suggestion(
            "ADD_VEHICLE", "HIGH",
            f"Add approximately {additional_trucks} medium truck(s) (~{avg_vehicle_weight:.0f}kg capacity each) "
            f"to handle the {weight_deficit:.0f}kg capacity deficit.",
            affected_shipments=[s.get("shipment_id") for s in unassigned],
            details={"weight_deficit_kg": round(weight_deficit, 1),
                     "additional_trucks_needed": additional_trucks,
                     "avg_truck_capacity_kg": round(avg_vehicle_weight, 1)},
        ))

    # Missing refrigerated vehicles
    fleet_types = set(v.get("vehicle_type", "") for v in vehicles)
    reefer_shipments = [s for s in all_shipments if s.get("special_handling") == "refrigerated"]

    if reefer_shipments and "refrigerated" not in fleet_types:
        reefer_ids = [s.get("shipment_id") for s in reefer_shipments]

        constraints.append({
            "type": "MISSING_VEHICLE_TYPE",
            "shipment_ids": reefer_ids,
            "message": f"{len(reefer_shipments)} shipment(s) require refrigerated handling "
                       f"but no refrigerated vehicles are in the fleet.",
        })

        suggestions.append(_suggestion(
            "ADD_VEHICLE", "HIGH",
            f"Add at least 1 refrigerated vehicle to handle {len(reefer_shipments)} "
            f"refrigerated shipment(s): {', '.join(reefer_ids[:5])}"
            f"{'...' if len(reefer_ids) > 5 else ''}.",
            affected_shipments=reefer_ids,
            details={"missing_type": "refrigerated", "affected_count": len(reefer_shipments)},
        ))

    # Routing/timing conflicts despite sufficient capacity
    if len(unassigned) > len(vehicles) and total_shipment_weight <= total_fleet_weight:
        suggestions.append(_suggestion(
            "ADD_VEHICLE", "MEDIUM",
            f"{len(unassigned)} shipments couldn't be assigned despite sufficient total fleet capacity. "
            f"This suggests time window or routing conflicts. Adding {max(1, len(unassigned) // 3)} more "
            f"vehicle(s) could provide the flexibility needed.",
            affected_shipments=[s.get("shipment_id") for s in unassigned],
            details={"unassigned_count": len(unassigned), "fleet_size": len(vehicles),
                     "suggested_additional": max(1, len(unassigned) // 3)},
        ))

    return constraints, suggestions


# ---------------------------------------------------------------------------
# Compatibility conflict detection
# ---------------------------------------------------------------------------

def detect_compatibility_conflicts(
    unassigned: List[Dict],
    all_shipments: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """
    Find shipments that can't be consolidated due to handling conflicts.
    """
    constraints = []
    suggestions = []

    lanes = {}
    for s in all_shipments:
        lane = f"{s.get('origin', '')}→{s.get('destination', '')}"
        if lane not in lanes:
            lanes[lane] = []
        lanes[lane].append(s)

    unassigned_ids = set(s.get("shipment_id") for s in unassigned)

    for lane_key, lane_shipments in lanes.items():
        lane_unassigned = [s for s in lane_shipments if s.get("shipment_id") in unassigned_ids]
        if not lane_unassigned:
            continue

        for i, s1 in enumerate(lane_shipments):
            for s2 in lane_shipments[i + 1:]:
                h1 = s1.get("special_handling") or "none"
                h2 = s2.get("special_handling") or "none"

                if not h1 or not h2 or h1 == "none" or h2 == "none":
                    continue

                pair = frozenset({h1, h2})
                if pair in HANDLING_CONFLICTS:
                    s1_id = s1.get("shipment_id", "?")
                    s2_id = s2.get("shipment_id", "?")

                    if s1_id in unassigned_ids or s2_id in unassigned_ids:
                        constraints.append({
                            "type": "HANDLING_CONFLICT",
                            "shipment_ids": [s1_id, s2_id],
                            "lane": lane_key,
                            "message": f"{s1_id} ({h1}) and {s2_id} ({h2}) are on the same lane "
                                       f"({lane_key}) but cannot share a vehicle.",
                        })

                        suggestions.append(_suggestion(
                            "RESOLVE_COMPATIBILITY", "MEDIUM",
                            f"Assign {s1_id} ({h1}) and {s2_id} ({h2}) to separate vehicles "
                            f"on the {lane_key} lane.",
                            affected_shipments=[s1_id, s2_id],
                            details={"handling_1": h1, "handling_2": h2, "lane": lane_key},
                        ))

    return constraints, suggestions


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def analyze_constraints(
    all_shipments: List[Dict],
    unassigned_shipments: List[Dict],
    vehicles: List[Dict],
    is_fully_infeasible: bool = False,
) -> Dict:
    """
    Run all constraint analysis checks and return structured results.

    This is the main function called by the relaxation agent.
    It detects all types of blocking constraints and generates
    prioritized fix suggestions.

    Args:
        all_shipments: Every shipment in the input set
        unassigned_shipments: Shipments the solver couldn't assign
        vehicles: All vehicles in the fleet
        is_fully_infeasible: True if the solver found no valid plan at all

    Returns:
        Dict with is_feasible, blocking_constraints, suggestions
        (sorted by priority), and summary counts per category.
    """
    all_constraints = []
    all_suggestions = []

    # Detect each category of constraint violation
    tw_c, tw_s = detect_time_window_conflicts(unassigned_shipments, all_shipments, vehicles)
    all_constraints.extend(tw_c)
    all_suggestions.extend(tw_s)

    cap_c, cap_s = detect_capacity_bottlenecks(unassigned_shipments, vehicles)
    all_constraints.extend(cap_c)
    all_suggestions.extend(cap_s)

    fleet_c, fleet_s = detect_fleet_gaps(all_shipments, unassigned_shipments, vehicles)
    all_constraints.extend(fleet_c)
    all_suggestions.extend(fleet_s)

    compat_c, compat_s = detect_compatibility_conflicts(unassigned_shipments, all_shipments)
    all_constraints.extend(compat_c)
    all_suggestions.extend(compat_s)

    # Sort suggestions by priority: HIGH first
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    all_suggestions.sort(key=lambda s: priority_order.get(s["priority"], 99))

    return {
        "is_feasible": len(unassigned_shipments) == 0,
        "is_fully_infeasible": is_fully_infeasible,
        "unassigned_shipments": [s.get("shipment_id") for s in unassigned_shipments],
        "unassigned_count": len(unassigned_shipments),
        "total_shipments": len(all_shipments),
        "blocking_constraints": all_constraints,
        "suggestions": all_suggestions,
        "summary_counts": {
            "time_window_conflicts": len(tw_c),
            "capacity_bottlenecks": len(cap_c),
            "fleet_gaps": len(fleet_c),
            "compatibility_conflicts": len(compat_c),
            "total_suggestions": len(all_suggestions),
        },
    }