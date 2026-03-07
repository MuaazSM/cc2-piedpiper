"""
Policy Guardrail Tool (Decide Phase).

Sits between the Reason phase (compatibility scoring) and the Act phase
(OR solver). Checks the compatibility graph output against hard operational
policies that are non-negotiable in freight logistics.

If any policy is violated, the guardrail flags the violation and sends
the pipeline back to the Reason phase to re-score with tighter constraints.

Three hard policies:
1. Hazmat cannot share a truck with food/refrigerated cargo
2. HIGH priority shipments cannot be co-loaded in ways that cause delay
3. Special handling requirements must match (fragile needs padded trucks, etc.)

This is NOT the same as the validation agent (which checks raw data quality).
The guardrail checks the OUTPUT of the ML compatibility model — it's a
safety net in case the ML model produces bad compatibility edges.
"""

from typing import List, Dict, Tuple


# ---------------------------------------------------------------------------
# Policy definitions
# ---------------------------------------------------------------------------

# Cargo type pairs that must NEVER share a vehicle.
# These are safety regulations, not optimization preferences.
FORBIDDEN_CARGO_PAIRS = {
    frozenset({"hazardous", "refrigerated"}),   # Chemical contamination risk
    frozenset({"hazardous", "fragile"}),         # Vibration + hazmat = dangerous
    frozenset({"hazardous", "oversized"}),       # Space + hazmat = handling risk
}

# Priority combinations that create unacceptable SLA risk.
# HIGH priority shipments should not be delayed by LOW priority stops.
RISKY_PRIORITY_PAIRS = {
    frozenset({"HIGH", "LOW"}),
}


# ---------------------------------------------------------------------------
# Individual policy checks
# ---------------------------------------------------------------------------

def check_cargo_compatibility(
    edges: List[Dict],
    shipments_lookup: Dict,
) -> List[Dict]:
    """
    Check all compatibility edges for forbidden cargo co-loading.

    Iterates through every edge (compatible pair) in the graph and
    verifies that their special handling types don't conflict.
    Returns a list of violations — each one is a specific edge that
    the ML model said was OK but policy says is NOT.

    Args:
        edges: List of edge dicts with shipment_a, shipment_b, score
        shipments_lookup: Dict mapping shipment_id → shipment data

    Returns:
        List of violation dicts with edge info and violation reason
    """
    violations = []

    for edge in edges:
        sid_a = edge.get("shipment_a", "")
        sid_b = edge.get("shipment_b", "")

        handling_a = shipments_lookup.get(sid_a, {}).get("special_handling") or "none"
        handling_b = shipments_lookup.get(sid_b, {}).get("special_handling") or "none"

        # Skip if either shipment has no special handling
        if handling_a == "none" or handling_b == "none":
            continue

        pair = frozenset({handling_a, handling_b})
        if pair in FORBIDDEN_CARGO_PAIRS:
            violations.append({
                "type": "FORBIDDEN_CARGO",
                "severity": "CRITICAL",
                "shipment_a": sid_a,
                "shipment_b": sid_b,
                "handling_a": handling_a,
                "handling_b": handling_b,
                "message": (
                    f"Policy violation: {sid_a} ({handling_a}) and {sid_b} ({handling_b}) "
                    f"cannot share a vehicle. This is a safety regulation."
                ),
            })

    return violations


def check_priority_conflicts(
    edges: List[Dict],
    shipments_lookup: Dict,
) -> List[Dict]:
    """
    Check for HIGH + LOW priority co-loading in the compatibility graph.

    HIGH priority shipments have strict SLA commitments. Putting them
    on the same truck as LOW priority shipments (which have flexible
    timing) creates a risk that the HIGH priority delivery gets delayed
    by LOW priority stops along the route.

    This is a soft policy — not a safety issue, but an SLA risk that
    operations managers typically want to avoid.
    """
    violations = []

    for edge in edges:
        sid_a = edge.get("shipment_a", "")
        sid_b = edge.get("shipment_b", "")

        priority_a = shipments_lookup.get(sid_a, {}).get("priority", "MEDIUM")
        priority_b = shipments_lookup.get(sid_b, {}).get("priority", "MEDIUM")

        pair = frozenset({priority_a, priority_b})
        if pair in RISKY_PRIORITY_PAIRS:
            violations.append({
                "type": "PRIORITY_CONFLICT",
                "severity": "WARNING",
                "shipment_a": sid_a,
                "shipment_b": sid_b,
                "priority_a": priority_a,
                "priority_b": priority_b,
                "message": (
                    f"SLA risk: {sid_a} ({priority_a} priority) and {sid_b} ({priority_b} priority) "
                    f"are marked compatible but co-loading may delay the HIGH priority delivery."
                ),
            })

    return violations


def check_handling_match(
    edges: List[Dict],
    shipments_lookup: Dict,
) -> List[Dict]:
    """
    Check that shipments with specific handling needs are only paired
    with shipments that have compatible handling requirements.

    For example, a refrigerated shipment should ideally only go on a
    truck with other refrigerated shipments (or shipments with no
    special handling that won't be harmed by cold temperatures).

    This is a softer check than forbidden cargo — it's about optimal
    handling, not safety.
    """
    violations = []

    # Handling types that need dedicated vehicle conditions
    DEDICATED_HANDLING = {"refrigerated", "fragile"}

    for edge in edges:
        sid_a = edge.get("shipment_a", "")
        sid_b = edge.get("shipment_b", "")

        handling_a = shipments_lookup.get(sid_a, {}).get("special_handling") or "none"
        handling_b = shipments_lookup.get(sid_b, {}).get("special_handling") or "none"

        # If both are "none", no issue
        if handling_a == "none" and handling_b == "none":
            continue

        # If both have the same handling, they're fine together
        if handling_a == handling_b:
            continue

        # Flag when a dedicated-handling shipment is paired with a different type
        if handling_a in DEDICATED_HANDLING and handling_b != "none" and handling_a != handling_b:
            violations.append({
                "type": "HANDLING_MISMATCH",
                "severity": "INFO",
                "shipment_a": sid_a,
                "shipment_b": sid_b,
                "handling_a": handling_a,
                "handling_b": handling_b,
                "message": (
                    f"Handling mismatch: {sid_a} ({handling_a}) paired with "
                    f"{sid_b} ({handling_b}). Consider separate vehicles for "
                    f"optimal handling conditions."
                ),
            })

        if handling_b in DEDICATED_HANDLING and handling_a != "none" and handling_a != handling_b:
            # Avoid duplicate if we already flagged this pair
            pair_key = frozenset({sid_a, sid_b})
            already_flagged = any(
                frozenset({v["shipment_a"], v["shipment_b"]}) == pair_key
                for v in violations if v["type"] == "HANDLING_MISMATCH"
            )
            if not already_flagged:
                violations.append({
                    "type": "HANDLING_MISMATCH",
                    "severity": "INFO",
                    "shipment_a": sid_a,
                    "shipment_b": sid_b,
                    "handling_a": handling_a,
                    "handling_b": handling_b,
                    "message": (
                        f"Handling mismatch: {sid_b} ({handling_b}) paired with "
                        f"{sid_a} ({handling_a}). Consider separate vehicles."
                    ),
                })

    return violations


# ---------------------------------------------------------------------------
# Main guardrail entry point
# ---------------------------------------------------------------------------

def run_guardrail(
    compatibility_edges: List[Dict],
    shipments: List[Dict],
) -> Dict:
    """
    Run all policy checks against the compatibility graph edges.

    This is the main entry point called by the LangGraph pipeline
    during the Decide phase. It takes the edges from the ML
    compatibility model and filters out any that violate hard policies.

    Returns:
        Dict with:
        - passed: bool — True if no CRITICAL violations found
        - violations: List of all violations (CRITICAL + WARNING + INFO)
        - critical_count: number of hard policy violations
        - filtered_edges: edges with CRITICAL violations removed
          (these clean edges go to the solver)
    """
    # Build lookup for quick access by shipment ID
    shipments_lookup = {s.get("shipment_id", ""): s for s in shipments}

    # Run all three policy checks
    cargo_violations = check_cargo_compatibility(compatibility_edges, shipments_lookup)
    priority_violations = check_priority_conflicts(compatibility_edges, shipments_lookup)
    handling_violations = check_handling_match(compatibility_edges, shipments_lookup)

    all_violations = cargo_violations + priority_violations + handling_violations

    # Count critical violations — these MUST be removed from the graph
    critical_violations = [v for v in all_violations if v["severity"] == "CRITICAL"]
    critical_count = len(critical_violations)

    # Build a set of forbidden edges (from CRITICAL violations only).
    # WARNING and INFO violations are reported but NOT removed — the solver
    # can still use those edges, and the insight agent will flag them.
    forbidden_pairs = set()
    for v in critical_violations:
        forbidden_pairs.add(frozenset({v["shipment_a"], v["shipment_b"]}))

    # Filter the edges: remove any that have CRITICAL violations
    filtered_edges = [
        edge for edge in compatibility_edges
        if frozenset({edge.get("shipment_a", ""), edge.get("shipment_b", "")}) not in forbidden_pairs
    ]

    edges_removed = len(compatibility_edges) - len(filtered_edges)

    passed = critical_count == 0

    print(f"[Guardrail] {'PASSED' if passed else 'VIOLATIONS FOUND'}: "
          f"{critical_count} critical, {len(priority_violations)} warnings, "
          f"{len(handling_violations)} info. {edges_removed} edges removed.")

    return {
        "passed": passed,
        "violations": all_violations,
        "critical_count": critical_count,
        "warning_count": len(priority_violations),
        "info_count": len(handling_violations),
        "edges_removed": edges_removed,
        "filtered_edges": filtered_edges,
    }