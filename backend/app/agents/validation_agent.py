"""
Validation Agent (Agent 1) — Pre-optimization data quality checker.

This agent runs BEFORE the OR solver touches anything. Its job is to
catch bad data early so we don't waste compute on infeasible or
garbage-in-garbage-out optimization runs.

Architecture:
- Core validation logic is pure Python (fast, deterministic, no LLM needed).
  This ensures validation works even without an API key.
- Optionally, the structured error report gets passed to Gemini (via LangChain)
  to generate a human-readable summary that the frontend can display
  in the agent insights panel.

Three severity levels:
- ERROR: blocks optimization (e.g. delivery before pickup, negative weight)
- WARNING: optimization proceeds but results may be suboptimal
- INFO: nice-to-know observations about the data
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from backend.app.data_loader.synthetic_generator import get_distance
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Validation report structure

def create_issue(
    severity: str,
    message: str,
    shipment_id: Optional[str] = None,
    field: Optional[str] = None,
) -> Dict:
    """
    Build a single validation issue entry.

    Each issue is a flat dict that's easy to serialize to JSON and
    easy for the frontend to render in a table or list view.

    Args:
        severity: "ERROR", "WARNING", or "INFO"
        message: Human-readable description of the problem
        shipment_id: Which shipment has the issue (None for fleet-level issues)
        field: Which field is problematic (None for general issues)
    """
    return {
        "severity": severity,
        "shipment_id": shipment_id,
        "field": field,
        "message": message,
    }


# Core validation rules (pure Python, no LLM)

def validate_shipments(shipments: List[Dict], vehicles: List[Dict]) -> Dict:
    """
    Run all validation checks against the shipment and vehicle data.

    This is the main entry point for the validation agent. It runs
    every check in sequence, collects all issues, and returns a
    structured report.

    Args:
        shipments: List of shipment dicts (from DB query, converted to dicts)
        vehicles: List of vehicle dicts (from DB query, converted to dicts)

    Returns:
        Dict with keys: is_valid, errors, warnings, info, summary_counts
    """
    errors = []
    warnings = []
    info = []

    # Track seen IDs to catch duplicates
    seen_ids = set()

    # Pre-compute fleet capabilities for cross-referencing
    max_fleet_weight = max((v["capacity_weight"] for v in vehicles), default=0)
    max_fleet_volume = max((v["capacity_volume"] for v in vehicles), default=0)
    fleet_types = set(v["vehicle_type"] for v in vehicles)
    has_refrigerated = "refrigerated" in fleet_types

    # Per-shipment checks
    for s in shipments:
        sid = s.get("shipment_id", "UNKNOWN")

        # CRITICAL: Missing required fields 
        # These fields are absolutely necessary for the optimizer to work.
        required_fields = ["origin", "destination", "weight", "volume", "pickup_time", "delivery_time"]
        for field in required_fields:
            value = s.get(field)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                errors.append(create_issue(
                    "ERROR", f"Missing required field: {field}", sid, field
                ))

        # CRITICAL: Duplicate shipment IDs 
        # The optimizer assigns each shipment exactly once — duplicates break this.
        if sid in seen_ids:
            errors.append(create_issue(
                "ERROR", f"Duplicate shipment ID found", sid, "shipment_id"
            ))
        seen_ids.add(sid)

        #  CRITICAL: Negative or zero weight/volume 
        # Physics doesn't allow negative freight. Zero weight means empty shipment.
        weight = s.get("weight", 0)
        volume = s.get("volume", 0)
        if isinstance(weight, (int, float)) and weight <= 0:
            errors.append(create_issue(
                "ERROR", f"Weight must be positive, got {weight}", sid, "weight"
            ))
        if isinstance(volume, (int, float)) and volume <= 0:
            errors.append(create_issue(
                "ERROR", f"Volume must be positive, got {volume}", sid, "volume"
            ))

        # CRITICAL: Delivery time before pickup time 
        # Can't deliver something before it's picked up.
        pickup = s.get("pickup_time")
        delivery = s.get("delivery_time")
        if pickup and delivery:
            # Handle both string and datetime inputs
            if isinstance(pickup, str):
                try:
                    pickup = datetime.fromisoformat(pickup)
                except ValueError:
                    errors.append(create_issue(
                        "ERROR", f"Invalid pickup_time format", sid, "pickup_time"
                    ))
                    continue
            if isinstance(delivery, str):
                try:
                    delivery = datetime.fromisoformat(delivery)
                except ValueError:
                    errors.append(create_issue(
                        "ERROR", f"Invalid delivery_time format", sid, "delivery_time"
                    ))
                    continue

            if delivery <= pickup:
                errors.append(create_issue(
                    "ERROR",
                    f"Delivery time ({delivery}) is before or equal to pickup time ({pickup})",
                    sid, "delivery_time"
                ))

            # WARNING: Pickup time in the past 
            # Not a hard blocker, but suspicious — might be stale data.
            if pickup < datetime.now():
                warnings.append(create_issue(
                    "WARNING",
                    f"Pickup time is in the past ({pickup.strftime('%Y-%m-%d %H:%M')})",
                    sid, "pickup_time"
                ))

            # WARNING: Very tight delivery window for long distances 
            # If someone expects Mumbai→Delhi delivery in 2 hours, that's not realistic.
            origin = s.get("origin", "")
            destination = s.get("destination", "")
            if origin and destination and origin != destination:
                distance = get_distance(origin, destination)
                window_hours = (delivery - pickup).total_seconds() / 3600

                # Minimum realistic hours: distance / 60 km/h average truck speed
                min_realistic_hours = distance / 60.0
                if window_hours < min_realistic_hours * 0.5:
                    warnings.append(create_issue(
                        "WARNING",
                        f"Very tight window ({window_hours:.1f}h) for {origin}→{destination} ({distance}km). "
                        f"Minimum realistic transit: {min_realistic_hours:.1f}h",
                        sid, "delivery_time"
                    ))

        #  WARNING: Shipment too heavy for any vehicle in the fleet 
        # The optimizer will fail to assign this shipment if no truck can carry it.
        if isinstance(weight, (int, float)) and weight > max_fleet_weight:
            warnings.append(create_issue(
                "WARNING",
                f"Weight ({weight}kg) exceeds largest vehicle capacity ({max_fleet_weight}kg). "
                f"This shipment cannot be assigned to any truck.",
                sid, "weight"
            ))

        #  WARNING: Shipment too large for any vehicle in the fleet 
        if isinstance(volume, (int, float)) and volume > max_fleet_volume:
            warnings.append(create_issue(
                "WARNING",
                f"Volume ({volume}m³) exceeds largest vehicle capacity ({max_fleet_volume}m³). "
                f"This shipment cannot be assigned to any truck.",
                sid, "volume"
            ))

        #  WARNING: Refrigerated shipment but no reefer trucks 
        special = s.get("special_handling")
        if special == "refrigerated" and not has_refrigerated:
            warnings.append(create_issue(
                "WARNING",
                f"Requires refrigerated handling but no refrigerated vehicles in fleet",
                sid, "special_handling"
            ))

    # Fleet-level checks

    #  WARNING: Fleet might be too small 
    # Quick sanity check: if total fleet weight capacity is less than total shipment weight,
    # we definitely can't fit everything even with perfect packing.
    total_shipment_weight = sum(s.get("weight", 0) for s in shipments if isinstance(s.get("weight"), (int, float)))
    total_fleet_weight = sum(v.get("capacity_weight", 0) for v in vehicles)
    if total_fleet_weight > 0 and total_shipment_weight > total_fleet_weight:
        warnings.append(create_issue(
            "WARNING",
            f"Total shipment weight ({total_shipment_weight:.0f}kg) exceeds total fleet capacity "
            f"({total_fleet_weight:.0f}kg). Some shipments may not be assignable.",
        ))

    #  INFO: Fleet size relative to shipment count 
    if len(vehicles) > 0 and len(shipments) > len(vehicles) * 5:
        info.append(create_issue(
            "INFO",
            f"High shipment-to-vehicle ratio ({len(shipments)} shipments / {len(vehicles)} vehicles). "
            f"Consider adding more vehicles for better consolidation options.",
        ))

    #  INFO: Origin distribution imbalance 
    # If most shipments come from one city, consolidation opportunities are limited.
    if shipments:
        origin_counts = {}
        for s in shipments:
            origin = s.get("origin", "UNKNOWN")
            origin_counts[origin] = origin_counts.get(origin, 0) + 1

        max_origin = max(origin_counts, key=origin_counts.get)
        max_pct = (origin_counts[max_origin] / len(shipments)) * 100
        if max_pct > 70:
            info.append(create_issue(
                "INFO",
                f"{max_pct:.0f}% of shipments originate from {max_origin}. "
                f"Heavily skewed origins may limit consolidation diversity.",
            ))

    #  INFO: Priority distribution 
    # Let the user know if many shipments defaulted to MEDIUM
    if shipments:
        medium_count = sum(1 for s in shipments if s.get("priority") == "MEDIUM")
        if medium_count == len(shipments):
            info.append(create_issue(
                "INFO",
                f"All {len(shipments)} shipments have MEDIUM priority. "
                f"Consider setting priorities to enable smarter SLA-based optimization.",
            ))

    # Build the final report
    is_valid = len(errors) == 0

    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "summary_counts": {
            "total_shipments": len(shipments),
            "total_vehicles": len(vehicles),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "info_count": len(info),
        },
    }


# LLM-powered summary (optional, uses Gemini via LangChain)

def generate_llm_summary(validation_report: Dict) -> Optional[str]:
    """
    Pass the structured validation report to Gemini to get a natural language
    summary that the frontend can display in the agent insights panel.

    Uses Google Gemini as the primary LLM via LangChain's ChatGoogleGenerativeAI.
    Falls back gracefully if no API key is configured — the validation report
    is still fully usable without the LLM summary.

    Returns None if the LLM call fails or no key is set.
    """
    # Check for Google API key first — if not set, skip the LLM call entirely
    google_api_key = os.getenv("GOOGLE_API_KEY", "")
    if not google_api_key:
        return None

    try:
        # Initialize Gemini through LangChain
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.3,  # Low temperature for factual, consistent summaries
        )

        # Build a prompt that gives the LLM all the context it needs
        # to write a useful summary without hallucinating.
        prompt = f"""You are a logistics data validation assistant for a freight consolidation system.

        Below is a structured validation report for a set of shipment and vehicle data.
        Write a brief, clear summary (3-5 sentences) that a logistics manager would find useful.

        Focus on:
        - Whether the data is ready for optimization or has blocking issues
        - The most important warnings they should be aware of
        - Any quick fixes they could make to improve results

        Validation Report:
        - Valid for optimization: {validation_report['is_valid']}
        - Errors (block optimization): {len(validation_report['errors'])}
        - Warnings (may affect quality): {len(validation_report['warnings'])}
        - Info (observations): {len(validation_report['info'])}
        - Total shipments: {validation_report['summary_counts']['total_shipments']}
        - Total vehicles: {validation_report['summary_counts']['total_vehicles']}

        Error details: {validation_report['errors'][:5]}
        Warning details: {validation_report['warnings'][:5]}
        Info details: {validation_report['info'][:5]}

        Write the summary in plain English. Be concise and actionable."""

        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content

    except Exception as e:
        # If anything goes wrong (bad key, network error, import missing),
        # just skip the LLM summary. Validation still works without it.
        print(f"[Validation Agent] LLM summary generation failed: {e}")
        return None


# Main entry point — combines rule checks + LLM summary

def run_validation(shipments: List[Dict], vehicles: List[Dict]) -> Dict:
    """
    Full validation pipeline: rule-based checks + optional LLM summary.

    This is what the /optimize endpoint calls. Returns the complete
    validation report with an optional llm_summary field.

    Args:
        shipments: List of shipment dicts
        vehicles: List of vehicle dicts

    Returns:
        Complete validation report dict with is_valid, errors, warnings,
        info, summary_counts, and optionally llm_summary.
    """
    # Step 1: Run all rule-based validation checks
    report = validate_shipments(shipments, vehicles)

    # Step 2: Generate a natural language summary using Gemini (if available)
    report["llm_summary"] = generate_llm_summary(report)

    return report