"""
Scenario Recommendation Agent (Agent 4) — Multi-objective plan comparison.

This agent runs AFTER the simulation engine generates results for all
4 scenarios. It compares them across three objectives (cost, SLA, carbon)
and recommends the best scenario depending on what the user prioritizes.

Think of it as a logistics consultant that reads the simulation output
and says: "If cost is your priority, go with Flexible SLA — you save 22%
but drop SLA by 7%. If SLA matters most, stick with Strict SLA."

Four recommendation perspectives:
1. Cost-optimized — minimize total transportation cost
2. SLA-optimized — maximize on-time delivery rate
3. Carbon-optimized — minimize carbon emissions
4. Balanced — weighted combination (configurable weights via API)

Also performs:
- Pairwise trade-off analysis between scenarios
- Dominant/dominated scenario detection
- Scenario ranking per objective

Architecture: pure Python scoring + optional Gemini narrative.
"""

import os
import json
from typing import List, Dict, Optional


# Default objective weights for balanced recommendation
# These reflect typical Indian freight priorities:
# Cost is the primary driver, SLA is a close second (contractual penalties),
# and carbon is growing in importance but not yet the primary concern.
DEFAULT_WEIGHTS = {
    "cost": 0.40,
    "sla": 0.35,
    "carbon": 0.25,
}


# Normalization helpers

def _normalize_min_better(values: List[float]) -> List[float]:
    """
    Normalize a list of values where LOWER is better (cost, carbon).

    Maps the best (lowest) value to 1.0 and the worst (highest) to 0.0.
    If all values are the same, returns all 1.0s (no differentiation).

    This lets us compare metrics on different scales (rupees vs kg CO2)
    by converting everything to a 0-1 score.
    """
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    if max_val == min_val:
        return [1.0] * len(values)
    # Invert: lower raw value → higher normalized score
    return [round((max_val - v) / (max_val - min_val), 4) for v in values]


def _normalize_max_better(values: List[float]) -> List[float]:
    """
    Normalize a list of values where HIGHER is better (SLA success rate).

    Maps the best (highest) value to 1.0 and the worst (lowest) to 0.0.
    """
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    if max_val == min_val:
        return [1.0] * len(values)
    return [round((v - min_val) / (max_val - min_val), 4) for v in values]


# Scenario ranking per objective

def rank_scenarios(scenarios: List[Dict]) -> Dict:
    """
    Rank all scenarios independently on each objective.

    For each objective (cost, SLA, carbon), sorts the scenarios from
    best to worst and assigns a rank (1 = best). Also includes the
    raw value and normalized score (0-1) for comparison.

    Returns a dict keyed by objective, each containing a ranked list.
    """
    if not scenarios:
        return {"cost": [], "sla": [], "carbon": []}

    # Extract raw values for each objective
    costs = [s.get("total_cost", 0) or 0 for s in scenarios]
    slas = [s.get("sla_success_rate", 0) or 0 for s in scenarios]
    carbons = [s.get("carbon_emissions", 0) or 0 for s in scenarios]

    # Normalize: cost and carbon are lower-is-better, SLA is higher-is-better
    norm_costs = _normalize_min_better(costs)
    norm_slas = _normalize_max_better(slas)
    norm_carbons = _normalize_min_better(carbons)

    # Build ranked lists for each objective
    rankings = {}

    # Cost ranking — sort by raw cost ascending (cheapest first)
    cost_ranked = sorted(
        range(len(scenarios)),
        key=lambda i: costs[i]
    )
    rankings["cost"] = [
        {
            "rank": rank + 1,
            "scenario_type": scenarios[i].get("scenario_type", "UNKNOWN"),
            "value": costs[i],
            "normalized_score": norm_costs[i],
        }
        for rank, i in enumerate(cost_ranked)
    ]

    # SLA ranking — sort by SLA descending (highest success rate first)
    sla_ranked = sorted(
        range(len(scenarios)),
        key=lambda i: slas[i],
        reverse=True
    )
    rankings["sla"] = [
        {
            "rank": rank + 1,
            "scenario_type": scenarios[i].get("scenario_type", "UNKNOWN"),
            "value": slas[i],
            "normalized_score": norm_slas[i],
        }
        for rank, i in enumerate(sla_ranked)
    ]

    # Carbon ranking — sort by emissions ascending (cleanest first)
    carbon_ranked = sorted(
        range(len(scenarios)),
        key=lambda i: carbons[i]
    )
    rankings["carbon"] = [
        {
            "rank": rank + 1,
            "scenario_type": scenarios[i].get("scenario_type", "UNKNOWN"),
            "value": carbons[i],
            "normalized_score": norm_carbons[i],
        }
        for rank, i in enumerate(carbon_ranked)
    ]

    return rankings


# Per-objective recommendations

def generate_recommendations(scenarios: List[Dict], weights: Dict) -> Dict:
    """
    Pick the best scenario for each objective and explain the trade-offs.

    For each perspective (cost, SLA, carbon, balanced), identifies the
    winning scenario and quantifies what you gain and lose compared
    to the alternatives.

    Args:
        scenarios: List of scenario result dicts
        weights: Dict with cost/sla/carbon weights for balanced scoring

    Returns:
        Dict with cost_optimized, sla_optimized, carbon_optimized,
        and balanced recommendations.
    """
    if not scenarios:
        return {
            "cost_optimized": None,
            "sla_optimized": None,
            "carbon_optimized": None,
            "balanced": None,
        }

    # Extract raw values
    costs = [s.get("total_cost", 0) or 0 for s in scenarios]
    slas = [s.get("sla_success_rate", 0) or 0 for s in scenarios]
    carbons = [s.get("carbon_emissions", 0) or 0 for s in scenarios]

    # Normalize for balanced scoring
    norm_costs = _normalize_min_better(costs)
    norm_slas = _normalize_max_better(slas)
    norm_carbons = _normalize_min_better(carbons)

    # --- Cost-optimized: pick the cheapest scenario ---
    cost_best_idx = costs.index(min(costs))
    cost_rec = _build_recommendation(
        objective="cost",
        winner=scenarios[cost_best_idx],
        winner_idx=cost_best_idx,
        scenarios=scenarios,
        costs=costs,
        slas=slas,
        carbons=carbons,
    )

    # --- SLA-optimized: pick the highest SLA success rate ---
    sla_best_idx = slas.index(max(slas))
    sla_rec = _build_recommendation(
        objective="sla",
        winner=scenarios[sla_best_idx],
        winner_idx=sla_best_idx,
        scenarios=scenarios,
        costs=costs,
        slas=slas,
        carbons=carbons,
    )

    # --- Carbon-optimized: pick the lowest emissions ---
    carbon_best_idx = carbons.index(min(carbons))
    carbon_rec = _build_recommendation(
        objective="carbon",
        winner=scenarios[carbon_best_idx],
        winner_idx=carbon_best_idx,
        scenarios=scenarios,
        costs=costs,
        slas=slas,
        carbons=carbons,
    )

    # --- Balanced: weighted composite score ---
    # Each scenario gets a score from 0 to 1 based on the weighted
    # combination of its normalized cost, SLA, and carbon scores.
    balanced_scores = []
    for i in range(len(scenarios)):
        score = (
            weights.get("cost", 0.4) * norm_costs[i]
            + weights.get("sla", 0.35) * norm_slas[i]
            + weights.get("carbon", 0.25) * norm_carbons[i]
        )
        balanced_scores.append(round(score, 4))

    balanced_best_idx = balanced_scores.index(max(balanced_scores))
    balanced_rec = _build_recommendation(
        objective="balanced",
        winner=scenarios[balanced_best_idx],
        winner_idx=balanced_best_idx,
        scenarios=scenarios,
        costs=costs,
        slas=slas,
        carbons=carbons,
    )
    balanced_rec["composite_scores"] = {
        scenarios[i].get("scenario_type", "UNKNOWN"): balanced_scores[i]
        for i in range(len(scenarios))
    }
    balanced_rec["weights_used"] = weights

    return {
        "cost_optimized": cost_rec,
        "sla_optimized": sla_rec,
        "carbon_optimized": carbon_rec,
        "balanced": balanced_rec,
    }


def _build_recommendation(
    objective: str,
    winner: Dict,
    winner_idx: int,
    scenarios: List[Dict],
    costs: List[float],
    slas: List[float],
    carbons: List[float],
) -> Dict:
    """
    Build a detailed recommendation for a single objective.

    Includes the winning scenario, its metrics, and the trade-offs
    compared to the runner-up on the OTHER objectives. This is where
    we answer "what do I give up by optimizing for X?"
    """
    winner_type = winner.get("scenario_type", "UNKNOWN")

    # Calculate trade-offs: how does the winner compare on the metrics
    # it DIDN'T optimize for?
    trade_offs = []
    for i, s in enumerate(scenarios):
        if i == winner_idx:
            continue

        other_type = s.get("scenario_type", "UNKNOWN")

        # Cost difference
        cost_diff_pct = _pct_diff(costs[winner_idx], costs[i])
        sla_diff = round(slas[winner_idx] - slas[i], 1)
        carbon_diff_pct = _pct_diff(carbons[winner_idx], carbons[i])

        trade_offs.append({
            "vs_scenario": other_type,
            "cost_diff_pct": cost_diff_pct,
            "sla_diff_points": sla_diff,
            "carbon_diff_pct": carbon_diff_pct,
            "summary": _trade_off_summary(
                winner_type, other_type,
                cost_diff_pct, sla_diff, carbon_diff_pct
            ),
        })

    # Build the human-readable recommendation message
    message = _recommendation_message(
        objective, winner_type,
        costs[winner_idx], slas[winner_idx], carbons[winner_idx],
        trade_offs,
    )

    return {
        "recommended_scenario": winner_type,
        "objective": objective,
        "metrics": {
            "total_cost": costs[winner_idx],
            "sla_success_rate": slas[winner_idx],
            "carbon_emissions": carbons[winner_idx],
            "trucks_used": winner.get("trucks_used"),
            "avg_utilization": winner.get("avg_utilization"),
        },
        "trade_offs": trade_offs,
        "message": message,
    }


def _pct_diff(value_a: float, value_b: float) -> float:
    """
    Calculate percentage difference from value_b to value_a.
    Positive means value_a is higher, negative means value_a is lower.
    Returns 0.0 if value_b is zero to avoid division errors.
    """
    if value_b == 0:
        return 0.0
    return round(((value_a - value_b) / value_b) * 100, 1)


def _trade_off_summary(
    winner: str, other: str,
    cost_diff: float, sla_diff: float, carbon_diff: float,
) -> str:
    """
    Build a one-line trade-off summary comparing two scenarios.
    Highlights what you gain and lose by picking the winner over the other.
    """
    parts = []

    if cost_diff < -1:
        parts.append(f"{abs(cost_diff):.0f}% cheaper")
    elif cost_diff > 1:
        parts.append(f"{cost_diff:.0f}% more expensive")

    if sla_diff > 1:
        parts.append(f"{sla_diff:.0f}pp higher SLA")
    elif sla_diff < -1:
        parts.append(f"{abs(sla_diff):.0f}pp lower SLA")

    if carbon_diff < -1:
        parts.append(f"{abs(carbon_diff):.0f}% less emissions")
    elif carbon_diff > 1:
        parts.append(f"{carbon_diff:.0f}% more emissions")

    if not parts:
        return f"{winner} vs {other}: roughly equivalent on all metrics."

    return f"{winner} vs {other}: {', '.join(parts)}."


def _recommendation_message(
    objective: str, winner: str,
    cost: float, sla: float, carbon: float,
    trade_offs: List[Dict],
) -> str:
    """
    Build a full recommendation message for a single objective.
    This is the kind of sentence that goes in the dashboard's
    recommendation card.
    """
    objective_labels = {
        "cost": "minimizing transportation cost",
        "sla": "maximizing on-time delivery",
        "carbon": "minimizing carbon emissions",
        "balanced": "the best overall trade-off",
    }

    msg = (
        f"For {objective_labels.get(objective, objective)}, "
        f"{winner} is the recommended scenario "
        f"(₹{cost:,.0f} cost, {sla:.0f}% SLA, {carbon:,.0f}kg CO₂)."
    )

    # Add the most significant trade-off as context
    if trade_offs:
        # Pick the trade-off with the biggest cost difference for cost objective,
        # biggest SLA diff for SLA objective, etc.
        biggest = trade_offs[0]
        msg += f" Key trade-off: {biggest['summary']}"

    return msg


# Trade-off matrix

def build_trade_off_matrix(scenarios: List[Dict]) -> List[Dict]:
    """
    Build a pairwise comparison matrix between all scenarios.

    Each entry compares two scenarios and shows the percentage difference
    on cost, SLA (in percentage points), and carbon. This powers the
    scenario comparison table in the frontend.
    """
    matrix = []

    for i, s1 in enumerate(scenarios):
        for j, s2 in enumerate(scenarios):
            if i >= j:
                continue

            s1_type = s1.get("scenario_type", "UNKNOWN")
            s2_type = s2.get("scenario_type", "UNKNOWN")

            cost_1 = s1.get("total_cost", 0) or 0
            cost_2 = s2.get("total_cost", 0) or 0
            sla_1 = s1.get("sla_success_rate", 0) or 0
            sla_2 = s2.get("sla_success_rate", 0) or 0
            carbon_1 = s1.get("carbon_emissions", 0) or 0
            carbon_2 = s2.get("carbon_emissions", 0) or 0

            matrix.append({
                "scenario_a": s1_type,
                "scenario_b": s2_type,
                "cost_diff_pct": _pct_diff(cost_1, cost_2),
                "sla_diff_points": round(sla_1 - sla_2, 1),
                "carbon_diff_pct": _pct_diff(carbon_1, carbon_2),
            })

    return matrix


# Dominant / dominated scenario detection

def detect_dominance(scenarios: List[Dict]) -> Dict:
    """
    Check if any scenario dominates (better on ALL metrics) or is
    dominated by (worse on ALL metrics) another scenario.

    A dominant scenario is a no-brainer — pick it regardless of priorities.
    A dominated scenario should never be chosen since another option
    beats it on every front.

    Returns dict with dominant and dominated scenario types (or null).
    """
    if len(scenarios) < 2:
        return {"dominant": None, "dominated": None}

    dominant = None
    dominated = None

    for i, s1 in enumerate(scenarios):
        # Check if s1 dominates all others
        dominates_all = True
        # Check if s1 is dominated by any other
        dominated_by_any = False

        cost_1 = s1.get("total_cost", 0) or 0
        sla_1 = s1.get("sla_success_rate", 0) or 0
        carbon_1 = s1.get("carbon_emissions", 0) or 0

        for j, s2 in enumerate(scenarios):
            if i == j:
                continue

            cost_2 = s2.get("total_cost", 0) or 0
            sla_2 = s2.get("sla_success_rate", 0) or 0
            carbon_2 = s2.get("carbon_emissions", 0) or 0

            # s1 dominates s2 if s1 is better or equal on ALL three metrics
            # (lower cost, higher SLA, lower carbon)
            s1_dominates_s2 = (cost_1 <= cost_2 and sla_1 >= sla_2 and carbon_1 <= carbon_2)
            # Must be strictly better on at least one metric to truly dominate
            s1_strictly_better = (cost_1 < cost_2 or sla_1 > sla_2 or carbon_1 < carbon_2)

            if not (s1_dominates_s2 and s1_strictly_better):
                dominates_all = False

            # Check if s2 dominates s1
            s2_dominates_s1 = (cost_2 <= cost_1 and sla_2 >= sla_1 and carbon_2 <= carbon_1)
            s2_strictly_better = (cost_2 < cost_1 or sla_2 > sla_1 or carbon_2 < carbon_1)

            if s2_dominates_s1 and s2_strictly_better:
                dominated_by_any = True

        if dominates_all:
            dominant = s1.get("scenario_type", "UNKNOWN")
        if dominated_by_any:
            dominated = s1.get("scenario_type", "UNKNOWN")

    return {"dominant": dominant, "dominated": dominated}


# LLM-powered narrative (optional, uses Gemini via LangChain)

def generate_llm_narrative(analysis: Dict) -> Optional[str]:
    """
    Use Gemini to write a recommendation memo that ties together
    the scenario rankings, trade-offs, and recommendations into
    a cohesive narrative a logistics manager would want to read.

    This is the "consultant's take" on the simulation results —
    it goes beyond the numbers to explain what they mean operationally.

    Returns None if no API key is set or the LLM call fails.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY", "")
    if not google_api_key:
        return None

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=google_api_key,
            temperature=0.4,
        )

        recommendations = analysis.get("recommendations", {})
        dominance = analysis.get("dominance", {})

        prompt = f"""You are a logistics optimization consultant reviewing freight consolidation simulation results.

Four scenarios were simulated, and here are the recommendations per objective:

Cost-Optimized Recommendation:
{json.dumps(recommendations.get("cost_optimized", {}), indent=2, default=str)}

SLA-Optimized Recommendation:
{json.dumps(recommendations.get("sla_optimized", {}), indent=2, default=str)}

Carbon-Optimized Recommendation:
{json.dumps(recommendations.get("carbon_optimized", {}), indent=2, default=str)}

Balanced Recommendation:
{json.dumps(recommendations.get("balanced", {}), indent=2, default=str)}

Dominance Analysis:
- Dominant scenario (better on ALL metrics): {dominance.get("dominant", "None")}
- Dominated scenario (worse on ALL metrics): {dominance.get("dominated", "None")}

Write a concise recommendation memo (5-8 sentences) that:
1. States which scenario to pick if they had to choose one (and why)
2. Highlights the key trade-off tension (usually cost vs SLA)
3. Mentions if any scenario is clearly dominant or should be avoided
4. Ends with a specific, actionable recommendation

Use concrete numbers (costs in ₹, SLA in %, carbon in kg).
Write in a professional but conversational tone — like a trusted advisor, not a report."""

        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content

    except Exception as e:
        print(f"[Scenario Agent] LLM narrative generation failed: {e}")
        return None


# Main entry point

def run_scenario_analysis(
    scenarios: List[Dict],
    cost_weight: float = 0.40,
    sla_weight: float = 0.35,
    carbon_weight: float = 0.25,
) -> Dict:
    """
    Full scenario analysis pipeline: rank, recommend, compare, and narrate.

    This is what the /simulate endpoint calls after all 4 scenarios
    have been run. Returns the complete analysis that powers the
    scenario comparison view on the frontend.

    Args:
        scenarios: List of scenario result dicts (one per scenario type)
        cost_weight: Weight for cost in balanced scoring (0-1)
        sla_weight: Weight for SLA in balanced scoring (0-1)
        carbon_weight: Weight for carbon in balanced scoring (0-1)

    Returns:
        Dict with scenario_rankings, recommendations, trade_off_matrix,
        dominance analysis, and optionally llm_narrative.
    """
    # Validate and normalize weights so they sum to 1.0
    total_weight = cost_weight + sla_weight + carbon_weight
    if total_weight == 0:
        total_weight = 1.0  # Fallback to avoid division by zero
    weights = {
        "cost": round(cost_weight / total_weight, 4),
        "sla": round(sla_weight / total_weight, 4),
        "carbon": round(carbon_weight / total_weight, 4),
    }

    # Step 1: Rank scenarios per objective
    rankings = rank_scenarios(scenarios)

    # Step 2: Generate per-objective recommendations with trade-off analysis
    recommendations = generate_recommendations(scenarios, weights)

    # Step 3: Build pairwise trade-off matrix for the comparison table
    trade_off_matrix = build_trade_off_matrix(scenarios)

    # Step 4: Check for dominant/dominated scenarios
    dominance = detect_dominance(scenarios)

    # Assemble the full analysis
    analysis = {
        "scenario_rankings": rankings,
        "recommendations": recommendations,
        "trade_off_matrix": trade_off_matrix,
        "dominance": dominance,
        "weights_used": weights,
    }

    # Step 5: Optional LLM narrative
    analysis["llm_narrative"] = generate_llm_narrative(analysis)

    return analysis