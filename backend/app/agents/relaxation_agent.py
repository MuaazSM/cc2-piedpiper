"""
Constraint Relaxation Agent (Agent 3) — Infeasibility diagnosis and resolution.

This agent activates when the OR solver can't assign all shipments —
either full infeasibility (no valid plan exists) or partial infeasibility
(some shipments left unassigned). Its job is to figure out WHY the
solver failed and suggest the smallest changes that would fix it.

Think of it as the "troubleshooter" — it doesn't just say "infeasible",
it says "relax SH-0003's delivery window by 45 minutes and add one
medium truck to make this work."

Four categories of blocking constraints it detects:
1. Time window conflicts — shipments that should consolidate but windows don't overlap
2. Capacity bottlenecks — shipments too heavy/large for available vehicles
3. Fleet gaps — not enough trucks, or missing vehicle types
4. Compatibility blocks — conflicting special handling on same-lane shipments

Architecture: pure Python constraint analysis + optional Gemini narrative.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from backend.app.data_loader.synthetic_generator import get_distance


# Suggestion builders — each creates a structured suggestion dict

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
    The frontend can render these as actionable cards with accept/reject buttons.

    Args:
        suggestion_type: RELAX_WINDOW, SPLIT_SHIPMENT, ADD_VEHICLE, RESOLVE_COMPATIBILITY
        priority: HIGH (do this first), MEDIUM, LOW (nice to have)
        message: Human-readable explanation of the fix
        affected_shipments: Which shipments this suggestion applies to
        details: Extra structured data (e.g. minutes to relax, kg to split)
    """
    return {
        "type": suggestion_type,
        "priority": priority,
        "message": message,
        "affected_shipments": affected_shipments or [],
        "details": details or {},
    }


# Time window conflict detection

def detect_time_window_conflicts(
    unassigned: List[Dict],
    all_shipments: List[Dict],
    vehicles: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """
    Find shipment pairs on the same lane that SHOULD consolidate but
    can't because their time windows don't overlap.

    For each unassigned shipment, we look at other shipments on the same
    origin→destination lane and check if their pickup/delivery windows
    are compatible. If not, we calculate exactly how many minutes of
    relaxation would fix it.

    Returns:
        Tuple of (blocking_constraints, suggestions)
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

        # Parse this shipment's time windows
        pickup = _parse_time(shipment.get("pickup_time"))
        delivery = _parse_time(shipment.get("delivery_time"))
        if not pickup or not delivery:
            continue

        # Check against other shipments on the same lane
        lane_shipments = lanes.get(lane_key, [])
        for other in lane_shipments:
            other_id = other.get("shipment_id", "")
            if other_id == sid:
                continue

            other_pickup = _parse_time(other.get("pickup_time"))
            other_delivery = _parse_time(other.get("delivery_time"))
            if not other_pickup or not other_delivery:
                continue

            # Check if windows overlap: two windows overlap if
            # one starts before the other ends AND vice versa
            windows_overlap = (pickup <= other_delivery) and (other_pickup <= delivery)

            if not windows_overlap:
                # Calculate the gap in minutes — this is how much we need to relax
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

                # Only suggest relaxation if the gap is reasonable (under 4 hours).
                # Beyond that, they're probably different delivery cycles entirely.
                if gap_minutes <= 240:
                    # Suggest relaxing the tighter shipment's window
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

    # Deduplicate: we might flag the same pair from both sides
    seen_pairs = set()
    unique_constraints = []
    for c in constraints:
        pair_key = tuple(sorted(c["shipment_ids"]))
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            unique_constraints.append(c)

    seen_suggestion_pairs = set()
    unique_suggestions = []
    for s in suggestions:
        pair_key = tuple(sorted(s["affected_shipments"]))
        if pair_key not in seen_suggestion_pairs:
            seen_suggestion_pairs.add(pair_key)
            unique_suggestions.append(s)

    return unique_constraints, unique_suggestions


# Capacity bottleneck detection

def detect_capacity_bottlenecks(
    unassigned: List[Dict],
    vehicles: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """
    Find shipments that can't be assigned because they exceed the
    capacity of every available vehicle.

    For oversized shipments, suggests splitting them into smaller pieces
    that can fit on existing trucks. Calculates the optimal split count
    based on the largest available vehicle.

    Returns:
        Tuple of (blocking_constraints, suggestions)
    """
    constraints = []
    suggestions = []

    # Find the largest vehicle capacities in the fleet
    max_weight = max((v.get("capacity_weight", 0) for v in vehicles), default=0)
    max_volume = max((v.get("capacity_volume", 0) for v in vehicles), default=0)

    for shipment in unassigned:
        sid = shipment.get("shipment_id", "UNKNOWN")
        weight = shipment.get("weight", 0)
        volume = shipment.get("volume", 0)

        # --- Weight exceeds all vehicles ---
        if weight > max_weight:
            # Calculate how many pieces we need to split into
            split_count = -(-int(weight) // int(max_weight))  # Ceiling division
            split_weight = round(weight / split_count, 1)

            constraints.append({
                "type": "WEIGHT_EXCEEDS_FLEET",
                "shipment_ids": [sid],
                "message": (
                    f"{sid} weighs {weight}kg but the largest vehicle can only "
                    f"carry {max_weight}kg."
                ),
            })

            suggestions.append(_suggestion(
                "SPLIT_SHIPMENT",
                "HIGH",
                (
                    f"Split {sid} ({weight}kg) into {split_count} shipments of "
                    f"~{split_weight}kg each to fit within vehicle capacity ({max_weight}kg max)."
                ),
                affected_shipments=[sid],
                details={
                    "current_weight": weight,
                    "max_vehicle_weight": max_weight,
                    "suggested_splits": split_count,
                    "split_weight": split_weight,
                },
            ))

        # --- Volume exceeds all vehicles ---
        if volume > max_volume:
            split_count = -(-int(volume * 100) // int(max_volume * 100))  # Ceiling division with precision
            split_volume = round(volume / split_count, 2)

            constraints.append({
                "type": "VOLUME_EXCEEDS_FLEET",
                "shipment_ids": [sid],
                "message": (
                    f"{sid} is {volume}m³ but the largest vehicle can only "
                    f"fit {max_volume}m³."
                ),
            })

            suggestions.append(_suggestion(
                "SPLIT_SHIPMENT",
                "HIGH",
                (
                    f"Split {sid} ({volume}m³) into {split_count} shipments of "
                    f"~{split_volume}m³ each to fit within vehicle capacity ({max_volume}m³ max)."
                ),
                affected_shipments=[sid],
                details={
                    "current_volume": volume,
                    "max_vehicle_volume": max_volume,
                    "suggested_splits": split_count,
                    "split_volume": split_volume,
                },
            ))

    return constraints, suggestions


# Fleet gap detection

def detect_fleet_gaps(
    all_shipments: List[Dict],
    unassigned: List[Dict],
    vehicles: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """
    Check if the fleet is simply too small to handle the shipment volume,
    or if specific vehicle types are missing.

    Computes a rough estimate of how many additional trucks are needed
    based on total weight vs total fleet capacity. Also checks for
    missing vehicle types (e.g. refrigerated shipments but no reefer trucks).

    Returns:
        Tuple of (blocking_constraints, suggestions)
    """
    constraints = []
    suggestions = []

    # --- Total capacity check ---
    total_shipment_weight = sum(s.get("weight", 0) for s in all_shipments)
    total_fleet_weight = sum(v.get("capacity_weight", 0) for v in vehicles)
    avg_vehicle_weight = total_fleet_weight / len(vehicles) if vehicles else 0

    if total_shipment_weight > total_fleet_weight:
        # Estimate how many more trucks are needed
        weight_deficit = total_shipment_weight - total_fleet_weight
        additional_trucks = -(-int(weight_deficit) // int(avg_vehicle_weight)) if avg_vehicle_weight > 0 else 1

        constraints.append({
            "type": "FLEET_CAPACITY_INSUFFICIENT",
            "shipment_ids": [s.get("shipment_id") for s in unassigned],
            "message": (
                f"Total shipment weight ({total_shipment_weight:.0f}kg) exceeds "
                f"total fleet capacity ({total_fleet_weight:.0f}kg)."
            ),
        })

        suggestions.append(_suggestion(
            "ADD_VEHICLE",
            "HIGH",
            (
                f"Add approximately {additional_trucks} medium truck(s) "
                f"(~{avg_vehicle_weight:.0f}kg capacity each) to handle the "
                f"{weight_deficit:.0f}kg capacity deficit."
            ),
            affected_shipments=[s.get("shipment_id") for s in unassigned],
            details={
                "weight_deficit_kg": round(weight_deficit, 1),
                "additional_trucks_needed": additional_trucks,
                "avg_truck_capacity_kg": round(avg_vehicle_weight, 1),
            },
        ))

    # --- Missing vehicle type check ---
    fleet_types = set(v.get("vehicle_type", "") for v in vehicles)

    # Check for refrigerated shipments without reefer trucks
    reefer_shipments = [
        s for s in all_shipments
        if s.get("special_handling") == "refrigerated"
    ]
    if reefer_shipments and "refrigerated" not in fleet_types:
        reefer_ids = [s.get("shipment_id") for s in reefer_shipments]
        constraints.append({
            "type": "MISSING_VEHICLE_TYPE",
            "shipment_ids": reefer_ids,
            "message": (
                f"{len(reefer_shipments)} shipment(s) require refrigerated handling "
                f"but no refrigerated vehicles are in the fleet."
            ),
        })

        suggestions.append(_suggestion(
            "ADD_VEHICLE",
            "HIGH",
            (
                f"Add at least 1 refrigerated vehicle to handle {len(reefer_shipments)} "
                f"refrigerated shipment(s): {', '.join(reefer_ids[:5])}"
                f"{'...' if len(reefer_ids) > 5 else ''}."
            ),
            affected_shipments=reefer_ids,
            details={
                "missing_type": "refrigerated",
                "affected_count": len(reefer_shipments),
            },
        ))

    # --- Shipment-to-vehicle ratio check ---
    # If there are way more unassigned shipments than vehicles,
    # the fleet is simply undersized
    if len(unassigned) > len(vehicles) and total_shipment_weight <= total_fleet_weight:
        # Capacity exists but routing/timing makes it impossible to use efficiently
        suggestions.append(_suggestion(
            "ADD_VEHICLE",
            "MEDIUM",
            (
                f"{len(unassigned)} shipments couldn't be assigned despite sufficient "
                f"total fleet capacity. This suggests time window or routing conflicts. "
                f"Adding {max(1, len(unassigned) // 3)} more vehicle(s) could provide "
                f"the flexibility needed."
            ),
            affected_shipments=[s.get("shipment_id") for s in unassigned],
            details={
                "unassigned_count": len(unassigned),
                "fleet_size": len(vehicles),
                "suggested_additional": max(1, len(unassigned) // 3),
            },
        ))

    return constraints, suggestions


# Compatibility conflict detection

def detect_compatibility_conflicts(
    unassigned: List[Dict],
    all_shipments: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """
    Find shipments that can't be consolidated because their special
    handling requirements conflict.

    Common conflicts in Indian freight:
    - Hazardous + fragile (vibration/temperature risk)
    - Hazardous + refrigerated (chemical contamination risk)
    - Oversized takes up too much space for co-loading

    Returns:
        Tuple of (blocking_constraints, suggestions)
    """
    constraints = []
    suggestions = []

    # Define which special handling types conflict with each other.
    # These pairs should never share a truck.
    CONFLICT_PAIRS = {
        ("hazardous", "fragile"),
        ("hazardous", "refrigerated"),
        ("hazardous", "oversized"),
    }

    # Group shipments by lane to check conflicts within same-lane groups
    lanes = {}
    for s in all_shipments:
        lane = f"{s.get('origin', '')}→{s.get('destination', '')}"
        if lane not in lanes:
            lanes[lane] = []
        lanes[lane].append(s)

    unassigned_ids = set(s.get("shipment_id") for s in unassigned)

    for lane_key, lane_shipments in lanes.items():
        # Only check lanes that have at least one unassigned shipment
        lane_unassigned = [s for s in lane_shipments if s.get("shipment_id") in unassigned_ids]
        if not lane_unassigned:
            continue

        # Check every pair in this lane for handling conflicts
        for i, s1 in enumerate(lane_shipments):
            for s2 in lane_shipments[i + 1:]:
                h1 = s1.get("special_handling")
                h2 = s2.get("special_handling")

                if not h1 or not h2:
                    continue

                # Check if this pair conflicts
                pair = tuple(sorted([h1, h2]))
                if pair in CONFLICT_PAIRS or (pair[0] == pair[1] == "hazardous"):
                    s1_id = s1.get("shipment_id", "?")
                    s2_id = s2.get("shipment_id", "?")

                    # Only flag if at least one of the pair is unassigned
                    if s1_id in unassigned_ids or s2_id in unassigned_ids:
                        constraints.append({
                            "type": "HANDLING_CONFLICT",
                            "shipment_ids": [s1_id, s2_id],
                            "lane": lane_key,
                            "message": (
                                f"{s1_id} ({h1}) and {s2_id} ({h2}) are on the same lane "
                                f"({lane_key}) but cannot share a vehicle due to "
                                f"conflicting handling requirements."
                            ),
                        })

                        suggestions.append(_suggestion(
                            "RESOLVE_COMPATIBILITY",
                            "MEDIUM",
                            (
                                f"Assign {s1_id} ({h1}) and {s2_id} ({h2}) to separate "
                                f"vehicles on the {lane_key} lane, or reclassify handling "
                                f"if the conflict is overly conservative."
                            ),
                            affected_shipments=[s1_id, s2_id],
                            details={
                                "handling_1": h1,
                                "handling_2": h2,
                                "lane": lane_key,
                            },
                        ))

    return constraints, suggestions


# Time parsing helper

def _parse_time(value) -> Optional[datetime]:
    """
    Safely parse a datetime value that could be a string, datetime, or None.
    Returns None on any failure so callers don't need try/except everywhere.
    """
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


# LLM-powered summary (optional, uses Gemini via LangChain)

def generate_llm_summary(relaxation_report: Dict) -> Optional[str]:
    """
    Use Gemini to write a natural language explanation of why the plan
    is infeasible and what the user should do about it.

    This turns a list of technical constraint violations into a clear
    action plan that a logistics manager can follow. The tone should
    be helpful and solution-oriented, not just a list of problems.

    Returns None if no API key is set or the LLM call fails.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY", "")
    if not google_api_key:
        return None

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.3,
        )

        prompt = f"""You are a logistics optimization advisor helping a freight manager fix an infeasible consolidation plan.

The optimizer could not assign all shipments to vehicles. Below is the analysis of what went wrong and suggested fixes.

Write a clear, actionable summary (4-6 sentences) that:
1. Explains the root cause(s) of infeasibility in plain language
2. Prioritizes the most impactful fix(es) — what should they do FIRST
3. Gives a realistic expectation of what will improve after the fix

Feasibility Status: {"Fully infeasible" if not relaxation_report.get("is_feasible") else "Partially infeasible"}
Unassigned Shipments: {len(relaxation_report.get("unassigned_shipments", []))}

Blocking Constraints:
{json.dumps(relaxation_report.get("blocking_constraints", [])[:8], indent=2, default=str)}

Suggested Fixes:
{json.dumps(relaxation_report.get("suggestions", [])[:8], indent=2, default=str)}

Write the summary now. Be specific — use shipment IDs and numbers.
Start with the most important action item."""

        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content

    except Exception as e:
        print(f"[Relaxation Agent] LLM summary generation failed: {e}")
        return None


# Main entry point

def run_relaxation_analysis(
    all_shipments: List[Dict],
    unassigned_shipments: List[Dict],
    vehicles: List[Dict],
    is_fully_infeasible: bool = False,
) -> Dict:
    """
    Full constraint relaxation pipeline: detect blocking constraints,
    generate fix suggestions, and optionally write an LLM summary.

    This is what the /optimize endpoint calls when the solver reports
    unassigned shipments or full infeasibility.

    Args:
        all_shipments: Every shipment in the input set
        unassigned_shipments: Shipments the solver couldn't assign
        vehicles: All vehicles in the fleet
        is_fully_infeasible: True if the solver found no valid plan at all

    Returns:
        Dict with is_feasible, unassigned_shipments, blocking_constraints,
        suggestions (sorted by priority), and optionally llm_summary.
    """
    all_constraints = []
    all_suggestions = []

    # --- Detect time window conflicts ---
    # These are the most common cause of infeasibility in freight consolidation.
    # Shipments on the same lane that can't share a truck due to timing.
    tw_constraints, tw_suggestions = detect_time_window_conflicts(
        unassigned_shipments, all_shipments, vehicles
    )
    all_constraints.extend(tw_constraints)
    all_suggestions.extend(tw_suggestions)

    # --- Detect capacity bottlenecks ---
    # Shipments that are physically too large for any vehicle.
    cap_constraints, cap_suggestions = detect_capacity_bottlenecks(
        unassigned_shipments, vehicles
    )
    all_constraints.extend(cap_constraints)
    all_suggestions.extend(cap_suggestions)

    # --- Detect fleet gaps ---
    # Not enough trucks overall, or missing specialized vehicle types.
    fleet_constraints, fleet_suggestions = detect_fleet_gaps(
        all_shipments, unassigned_shipments, vehicles
    )
    all_constraints.extend(fleet_constraints)
    all_suggestions.extend(fleet_suggestions)

    # --- Detect compatibility conflicts ---
    # Special handling requirements that prevent co-loading.
    compat_constraints, compat_suggestions = detect_compatibility_conflicts(
        unassigned_shipments, all_shipments
    )
    all_constraints.extend(compat_constraints)
    all_suggestions.extend(compat_suggestions)

    # Sort suggestions by priority so the most impactful fixes come first.
    # HIGH → MEDIUM → LOW ordering.
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    all_suggestions.sort(key=lambda s: priority_order.get(s["priority"], 99))

    # Build the report
    report = {
        "is_feasible": len(unassigned_shipments) == 0,
        "is_fully_infeasible": is_fully_infeasible,
        "unassigned_shipments": [s.get("shipment_id") for s in unassigned_shipments],
        "unassigned_count": len(unassigned_shipments),
        "total_shipments": len(all_shipments),
        "blocking_constraints": all_constraints,
        "suggestions": all_suggestions,
        "summary_counts": {
            "time_window_conflicts": len(tw_constraints),
            "capacity_bottlenecks": len(cap_constraints),
            "fleet_gaps": len(fleet_constraints),
            "compatibility_conflicts": len(compat_constraints),
            "total_suggestions": len(all_suggestions),
        },
    }

    # Generate LLM summary if we have blocking issues to explain
    if all_constraints or all_suggestions:
        report["llm_summary"] = generate_llm_summary(report)
    else:
        report["llm_summary"] = None

    return report