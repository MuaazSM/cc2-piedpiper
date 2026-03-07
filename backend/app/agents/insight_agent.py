"""
Insight Agent (Agent 2) — Post-optimization explainability layer.

This agent runs AFTER the OR solver and translates raw optimization
output into human-readable insights that a logistics manager can
actually act on. Think of it as the "narrator" of the optimization.

Architecture (same hybrid pattern as Agent 1):
- Pure Python computes structured metrics and rule-based observations
  (utilization buckets, risk flags, lane-level consolidation stats).
- Gemini (via LangChain) takes those structured insights and writes
  a natural language narrative for the dashboard's agent insights panel.
- Falls back gracefully without API key — structured insights still work.

Three categories of output:
- Lane insights: per-assignment consolidation commentary
- Risk flags: SLA risk, capacity risk, missed consolidation opportunities
- Recommendations: actionable suggestions to improve the plan
"""

import os
import json
from typing import List, Dict, Optional
from backend.app.data_loader.synthetic_generator import get_distance
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Utilization thresholds
# These thresholds define what "good" and "bad" utilization looks like.
# Based on industry norms: <50% is wasteful, 50-75% is okay, >75% is solid.
UTILIZATION_EXCELLENT = 85.0   # Green zone — trucks are well-packed
UTILIZATION_GOOD = 75.0        # Acceptable — room for minor improvement
UTILIZATION_FAIR = 50.0        # Yellow zone — significant wasted capacity
# Below FAIR = red zone — truck is mostly empty, missed consolidation


# Helper: classify utilization into a human-readable bucket

def classify_utilization(pct: float) -> str:
    """
    Translate a utilization percentage into a plain English label.
    Makes it easy for the frontend to color-code and for the LLM
    to reference in its narrative.
    """
    if pct >= UTILIZATION_EXCELLENT:
        return "excellent"
    elif pct >= UTILIZATION_GOOD:
        return "good"
    elif pct >= UTILIZATION_FAIR:
        return "fair"
    else:
        return "poor"


# Plan-level summary computation

def compute_plan_summary(plan: Dict, assignments: List[Dict], vehicles: List[Dict]) -> Dict:
    """
    Generate high-level summary metrics for the entire consolidation plan.

    Takes the raw plan data and assignments, computes derived metrics
    that aren't stored in the DB but are useful for the dashboard:
    - Utilization distribution (how many trucks in each bucket)
    - Trip reduction narrative
    - Fleet usage ratio

    Args:
        plan: Plan dict with total_trucks, trips_baseline, avg_utilization, etc.
        assignments: List of assignment dicts with vehicle_id, shipment_ids, utilization_pct
        vehicles: List of vehicle dicts for fleet context

    Returns:
        Dict with computed summary fields
    """
    # If no assignments exist yet (draft plan), return a minimal summary
    if not assignments:
        return {
            "status": "draft",
            "message": "No assignments to analyze yet. Run the optimizer to generate a plan.",
            "total_shipments_assigned": 0,
            "trucks_used": 0,
            "trucks_available": len(vehicles),
            "avg_utilization": 0.0,
            "utilization_rating": "N/A",
            "trips_saved": 0,
            "trips_saved_pct": 0.0,
        }

    # Count total shipments across all assignments
    total_assigned = 0
    for a in assignments:
        # shipment_ids is a JSON string — parse it to count
        try:
            sids = json.loads(a.get("shipment_ids", "[]"))
            total_assigned += len(sids)
        except (json.JSONDecodeError, TypeError):
            pass

    # Compute utilization distribution across trucks
    utilization_buckets = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
    for a in assignments:
        pct = a.get("utilization_pct", 0) or 0
        bucket = classify_utilization(pct)
        utilization_buckets[bucket] += 1

    # Trip reduction: baseline is 1 trip per shipment (no consolidation)
    trips_baseline = plan.get("trips_baseline", total_assigned)
    trucks_used = plan.get("total_trucks", len(assignments))
    trips_saved = trips_baseline - trucks_used
    trips_saved_pct = (trips_saved / trips_baseline * 100) if trips_baseline > 0 else 0

    avg_util = plan.get("avg_utilization", 0) or 0

    return {
        "status": "analyzed",
        "total_shipments_assigned": total_assigned,
        "trucks_used": trucks_used,
        "trucks_available": len(vehicles),
        "fleet_usage_pct": round((trucks_used / len(vehicles)) * 100, 1) if vehicles else 0,
        "avg_utilization": round(avg_util, 1),
        "utilization_rating": classify_utilization(avg_util),
        "utilization_distribution": utilization_buckets,
        "trips_baseline": trips_baseline,
        "trips_saved": trips_saved,
        "trips_saved_pct": round(trips_saved_pct, 1),
        "cost_saving_pct": plan.get("cost_saving_pct", 0),
        "carbon_saving_pct": plan.get("carbon_saving_pct", 0),
    }



# Lane-level insights (per assignment)


def compute_lane_insights(assignments: List[Dict], shipments_lookup: Dict) -> List[Dict]:
    """
    Generate per-assignment insights that explain what happened on each truck.

    For each assignment, we figure out:
    - Which lane(s) the truck is serving
    - How many shipments are consolidated
    - Whether utilization is good or needs attention
    - Approximate distance covered

    Args:
        assignments: List of assignment dicts
        shipments_lookup: Dict mapping shipment_id → shipment dict for quick lookups

    Returns:
        List of lane insight dicts, one per assignment
    """
    if not assignments:
        return []

    insights = []
    for a in assignments:
        vehicle_id = a.get("vehicle_id", "UNKNOWN")
        utilization = a.get("utilization_pct", 0) or 0
        detour_km = a.get("route_detour_km", 0) or 0

        # Parse the shipment IDs assigned to this truck
        try:
            shipment_ids = json.loads(a.get("shipment_ids", "[]"))
        except (json.JSONDecodeError, TypeError):
            shipment_ids = []

        # Figure out the unique origin-destination pairs on this truck
        # to describe the lane(s) being served
        lanes = set()
        origins = set()
        destinations = set()
        total_weight = 0
        total_volume = 0
        priorities = []

        for sid in shipment_ids:
            shipment = shipments_lookup.get(sid, {})
            origin = shipment.get("origin", "?")
            dest = shipment.get("destination", "?")
            origins.add(origin)
            destinations.add(dest)
            lanes.add(f"{origin}→{dest}")
            total_weight += shipment.get("weight", 0)
            total_volume += shipment.get("volume", 0)
            priorities.append(shipment.get("priority", "MEDIUM"))

        # Build a human-readable lane description
        if len(lanes) == 1:
            lane_desc = list(lanes)[0]
        elif len(lanes) <= 3:
            lane_desc = ", ".join(lanes)
        else:
            lane_desc = f"{len(lanes)} mixed lanes from {', '.join(origins)}"

        # Compute approximate total distance for this truck's route
        total_distance = 0
        for sid in shipment_ids:
            shipment = shipments_lookup.get(sid, {})
            o = shipment.get("origin", "")
            d = shipment.get("destination", "")
            if o and d:
                total_distance += get_distance(o, d)

        # Build the insight for this assignment
        insight = {
            "vehicle_id": vehicle_id,
            "shipment_count": len(shipment_ids),
            "lane_description": lane_desc,
            "utilization_pct": round(utilization, 1),
            "utilization_rating": classify_utilization(utilization),
            "total_weight_kg": round(total_weight, 1),
            "total_volume_m3": round(total_volume, 2),
            "route_distance_km": total_distance,
            "detour_km": round(detour_km, 1),
            "has_high_priority": "HIGH" in priorities,
            # Generate a one-line summary for this truck
            "summary": _build_lane_summary(
                vehicle_id, lane_desc, len(shipment_ids), utilization, total_distance
            ),
        }
        insights.append(insight)

    return insights


def _build_lane_summary(
    vehicle_id: str, lane_desc: str, shipment_count: int,
    utilization: float, distance_km: int
) -> str:
    """
    Build a one-line human-readable summary for a single truck assignment.
    These are the kind of sentences that show up in the dashboard's
    assignment cards.
    """
    rating = classify_utilization(utilization)

    if shipment_count == 1:
        return (
            f"{vehicle_id}: Single shipment on {lane_desc} — "
            f"{utilization:.0f}% utilized. Consider consolidating with nearby lanes."
        )
    else:
        return (
            f"{vehicle_id}: {shipment_count} shipments consolidated on {lane_desc} — "
            f"{utilization:.0f}% utilization ({rating}), ~{distance_km}km total route."
        )


# Risk flags
def compute_risk_flags(
    assignments: List[Dict],
    shipments_lookup: Dict,
    plan_summary: Dict,
) -> List[Dict]:
    """
    Identify risks in the current plan that the logistics manager should know about.

    Checks for:
    - SLA risk: tight time windows with multi-stop routes
    - Capacity risk: trucks loaded above 90% (no buffer for last-minute adds)
    - Underutilization: trucks below 50% (wasted trips)
    - Single-shipment trucks: missed consolidation opportunities
    - High-priority shipments on mixed-priority trucks

    Returns a list of risk flag dicts with severity and description.
    """
    if not assignments:
        return []

    flags = []

    for a in assignments:
        vehicle_id = a.get("vehicle_id", "UNKNOWN")
        utilization = a.get("utilization_pct", 0) or 0
        detour_km = a.get("route_detour_km", 0) or 0

        try:
            shipment_ids = json.loads(a.get("shipment_ids", "[]"))
        except (json.JSONDecodeError, TypeError):
            shipment_ids = []

        # Capacity risk: truck is very full, no room for error 
        if utilization > 90:
            flags.append({
                "severity": "WARNING",
                "vehicle_id": vehicle_id,
                "type": "CAPACITY_RISK",
                "message": (
                    f"{vehicle_id} is at {utilization:.0f}% capacity. "
                    f"Very little buffer — any weight discrepancy could cause overload."
                ),
            })

        # Underutilization: truck is mostly empty 
        if utilization < UTILIZATION_FAIR and len(shipment_ids) > 0:
            flags.append({
                "severity": "WARNING",
                "vehicle_id": vehicle_id,
                "type": "UNDERUTILIZED",
                "message": (
                    f"{vehicle_id} is only {utilization:.0f}% utilized with "
                    f"{len(shipment_ids)} shipment(s). Consider merging with another route."
                ),
            })

        # Single shipment: missed consolidation 
        if len(shipment_ids) == 1:
            flags.append({
                "severity": "INFO",
                "vehicle_id": vehicle_id,
                "type": "SINGLE_SHIPMENT",
                "message": (
                    f"{vehicle_id} carries only 1 shipment. "
                    f"If time windows allow, this could be consolidated with a nearby lane."
                ),
            })

        # SLA risk: high-priority shipments on multi-stop routes 
        priorities = [
            shipments_lookup.get(sid, {}).get("priority", "MEDIUM")
            for sid in shipment_ids
        ]
        has_high = "HIGH" in priorities
        has_low = "LOW" in priorities

        if has_high and len(shipment_ids) > 2 and detour_km > 50:
            flags.append({
                "severity": "WARNING",
                "vehicle_id": vehicle_id,
                "type": "SLA_RISK",
                "message": (
                    f"{vehicle_id} has HIGH priority shipment(s) on a {len(shipment_ids)}-stop "
                    f"route with {detour_km:.0f}km detour. Delivery delays possible."
                ),
            })

        # Mixed priority risk: HIGH and LOW on same truck 
        if has_high and has_low:
            flags.append({
                "severity": "INFO",
                "vehicle_id": vehicle_id,
                "type": "MIXED_PRIORITY",
                "message": (
                    f"{vehicle_id} mixes HIGH and LOW priority shipments. "
                    f"LOW priority stops may delay HIGH priority deliveries."
                ),
            })

    return flags


# Recommendations

def compute_recommendations(
    plan_summary: Dict,
    lane_insights: List[Dict],
    risk_flags: List[Dict],
) -> List[Dict]:
    """
    Generate actionable recommendations based on the plan analysis.

    These are higher-level suggestions that go beyond individual truck
    flags — they look at patterns across the whole plan and suggest
    strategic improvements.
    """
    if plan_summary.get("status") == "draft":
        return []

    recommendations = []

    # Recommendation: overall utilization improvement 
    avg_util = plan_summary.get("avg_utilization", 0)
    if avg_util < UTILIZATION_GOOD:
        recommendations.append({
            "type": "UTILIZATION",
            "priority": "HIGH",
            "message": (
                f"Average utilization is {avg_util:.0f}% — below the {UTILIZATION_GOOD:.0f}% target. "
                f"Consider relaxing time windows (Flexible SLA scenario) to allow "
                f"more shipments per truck."
            ),
        })

    # Recommendation: too many single-shipment trucks 
    single_count = sum(1 for f in risk_flags if f["type"] == "SINGLE_SHIPMENT")
    total_trucks = plan_summary.get("trucks_used", 0)
    if total_trucks > 0 and single_count / total_trucks > 0.3:
        recommendations.append({
            "type": "CONSOLIDATION",
            "priority": "HIGH",
            "message": (
                f"{single_count} out of {total_trucks} trucks carry only 1 shipment "
                f"({single_count/total_trucks*100:.0f}%). This suggests limited "
                f"consolidation opportunity — check if shipment origins/destinations "
                f"are too scattered or time windows too tight."
            ),
        })

    # Recommendation: fleet sizing 
    fleet_usage = plan_summary.get("fleet_usage_pct", 0)
    if fleet_usage > 90:
        recommendations.append({
            "type": "FLEET_SIZE",
            "priority": "MEDIUM",
            "message": (
                f"Using {fleet_usage:.0f}% of the fleet. Near-full fleet usage means "
                f"no buffer for demand spikes. Consider adding vehicles or running "
                f"the Vehicle Shortage scenario to understand the impact."
            ),
        })
    elif fleet_usage < 40:
        recommendations.append({
            "type": "FLEET_SIZE",
            "priority": "LOW",
            "message": (
                f"Only using {fleet_usage:.0f}% of the fleet. The fleet may be "
                f"oversized for current demand. Could reduce operating costs by "
                f"downsizing or reallocating idle vehicles."
            ),
        })

    # Recommendation: high SLA risk count 
    sla_risks = sum(1 for f in risk_flags if f["type"] == "SLA_RISK")
    if sla_risks >= 3:
        recommendations.append({
            "type": "SLA",
            "priority": "HIGH",
            "message": (
                f"{sla_risks} trucks have SLA risk flags. Consider separating "
                f"HIGH priority shipments into dedicated vehicles or reducing "
                f"the number of stops on those routes."
            ),
        })

    # Recommendation: good plan acknowledgment 
    # If everything looks solid, say so — positive feedback matters too.
    if avg_util >= UTILIZATION_GOOD and single_count == 0 and sla_risks == 0:
        recommendations.append({
            "type": "POSITIVE",
            "priority": "LOW",
            "message": (
                f"Plan looks strong — {avg_util:.0f}% average utilization with "
                f"no major risk flags. Good candidate for execution."
            ),
        })

    return recommendations


# LLM-powered narrative (optional, uses Gemini via LangChain)

def generate_llm_narrative(
    plan_summary: Dict,
    lane_insights: List[Dict],
    risk_flags: List[Dict],
    recommendations: List[Dict],
) -> Optional[str]:
    """
    Use Gemini to write a natural language narrative that ties together
    all the structured insights into a cohesive story.

    This is what shows up in the "Agent Insights" panel on the dashboard.
    It reads like a mini logistics briefing — the kind of thing a
    planning manager would want to skim before approving a plan.

    Returns None if no API key is set or the LLM call fails.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY", "")
    if not google_api_key:
        return None

    try:

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.4,  # Slightly creative for readable narratives
        )

        # Build a context-rich prompt with all the structured data
        prompt = f"""You are a logistics optimization analyst explaining a freight consolidation plan.

        Write a clear, concise briefing (5-8 sentences) that a logistics manager would find useful.
        Use specific numbers from the data below. Write in a professional but approachable tone.

        Plan Summary:
        - Trucks used: {plan_summary.get('trucks_used', 'N/A')} out of {plan_summary.get('trucks_available', 'N/A')} available
        - Average utilization: {plan_summary.get('avg_utilization', 'N/A')}% ({plan_summary.get('utilization_rating', 'N/A')})
        - Trips saved: {plan_summary.get('trips_saved', 'N/A')} ({plan_summary.get('trips_saved_pct', 'N/A')}% reduction)
        - Cost savings: {plan_summary.get('cost_saving_pct', 'N/A')}%
        - Carbon savings: {plan_summary.get('carbon_saving_pct', 'N/A')}%
        - Utilization distribution: {plan_summary.get('utilization_distribution', 'N/A')}

        Top Lane Insights (first 5):
        {json.dumps(lane_insights[:5], indent=2, default=str)}

        Risk Flags:
        {json.dumps(risk_flags[:5], indent=2, default=str)}

        Recommendations:
        {json.dumps(recommendations, indent=2, default=str)}

        Write the briefing now. Include specific lane examples where relevant.
        For example: "The Mumbai-Pune lane consolidated 3 shipments at 88% utilization."
        End with the most important recommendation."""

        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content

    except Exception as e:
        print(f"[Insight Agent] LLM narrative generation failed: {e}")
        return None


# Main entry point

def run_insight_analysis(
    plan: Dict,
    assignments: List[Dict],
    shipments: List[Dict],
    vehicles: List[Dict],
) -> Dict:
    """
    Full insight pipeline: compute structured metrics + generate LLM narrative.

    This is what the /optimize endpoint calls after the solver finishes.
    Returns the complete insight report that the frontend renders in
    the agent insights panel.

    Args:
        plan: Plan dict with summary metrics
        assignments: List of assignment dicts from the solver
        shipments: List of all shipment dicts (for cross-referencing)
        vehicles: List of all vehicle dicts (for fleet context)

    Returns:
        Dict with plan_summary, lane_insights, risk_flags, recommendations,
        and optionally llm_narrative.
    """
    # Build a lookup dict for quick shipment access by ID
    shipments_lookup = {s["shipment_id"]: s for s in shipments}

    # Step 1: Compute plan-level summary
    plan_summary = compute_plan_summary(plan, assignments, vehicles)

    # Step 2: Generate per-lane insights
    lane_insights = compute_lane_insights(assignments, shipments_lookup)

    # Step 3: Identify risk flags
    risk_flags = compute_risk_flags(assignments, shipments_lookup, plan_summary)

    # Step 4: Generate recommendations based on everything above
    recommendations = compute_recommendations(plan_summary, lane_insights, risk_flags)

    # Step 5: Optional LLM narrative to tie it all together
    llm_narrative = generate_llm_narrative(
        plan_summary, lane_insights, risk_flags, recommendations
    )

    return {
        "plan_summary": plan_summary,
        "lane_insights": lane_insights,
        "risk_flags": risk_flags,
        "recommendations": recommendations,
        "llm_narrative": llm_narrative,
    }