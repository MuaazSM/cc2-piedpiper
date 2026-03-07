"""
Outcome Logging Tool — Persists optimization results for the Learn phase.

Writes a complete record of every optimization run to the
OptimizationOutcome table. This enables:
- Historical tracking of optimization quality over time
- Auditing of what the system recommended and why
- ML model retraining based on actual outcomes
- Dashboard analytics across multiple runs

Also manages the compatibility model retraining hook — after every
N outcomes, triggers a retrain so the ML model improves based on
which consolidations the solver actually produced.

Sits at the very end of the pipeline, after metrics_node.
"""

import json
from typing import Dict, Optional
from backend.app.db.session import SessionLocal
from backend.app.models.outcome import OptimizationOutcome


# ---------------------------------------------------------------------------
# Retraining configuration
# ---------------------------------------------------------------------------

# Retrain the compatibility model after this many logged outcomes.
# Lower = more frequent retraining (better adaptation, more compute).
# Higher = less frequent (stable model, less overhead).
# 10 is a good starting point for a hackathon demo — shows the
# "learning" aspect without excessive retraining.
RETRAIN_EVERY_N_OUTCOMES = 10


def log_outcome(
    pipeline_result: Dict,
    plan_id: Optional[int] = None,
) -> Dict:
    """
    Write a complete optimization outcome to the database.

    Extracts all relevant data from the pipeline result and persists
    it as a single OptimizationOutcome row. Complex nested data
    (violations, scenarios, metrics) is serialized as JSON.

    Args:
        pipeline_result: The full response dict from run_pipeline()
        plan_id: The DB-generated plan ID (if the plan was persisted)

    Returns:
        Dict with outcome_id, should_retrain flag, and total outcome count
    """
    db = SessionLocal()

    try:
        # --- Extract key metrics from the pipeline result ---
        plan = pipeline_result.get("plan") or {}
        metrics = pipeline_result.get("metrics") or {}
        metadata = pipeline_result.get("pipeline_metadata") or {}
        scenarios = pipeline_result.get("scenarios")
        violations = pipeline_result.get("guardrail", {})
        compatibility = pipeline_result.get("compatibility") or {}

        # Compute trip reduction from metrics
        before = metrics.get("before", {})
        savings = metrics.get("savings", {})
        after = metrics.get("after", {})

        # --- Build the outcome record ---
        outcome = OptimizationOutcome(
            plan_id=plan_id,
            solver_used=plan.get("solver_used"),
            solver_status=plan.get("solver_status"),
            is_feasible=0 if plan.get("is_infeasible", False) else 1,
            retry_count=metadata.get("retry_count", 0),
            total_shipments=metrics.get("fleet", {}).get("shipments_assigned", 0) +
                           metrics.get("fleet", {}).get("shipments_unassigned", 0),
            total_vehicles=metrics.get("fleet", {}).get("trucks_available", 0),
            trucks_used=after.get("total_trips", 0),
            utilization_achieved=after.get("avg_utilization", 0),
            cost_saving_pct=savings.get("cost_saving_pct", 0),
            carbon_saving_pct=savings.get("carbon_saving_pct", 0),
            trip_reduction_pct=savings.get("trip_reduction_pct", 0),
            pipeline_duration_ms=metadata.get("total_duration_ms", 0),

            # Serialize complex data as JSON
            constraint_violations=_safe_json(violations.get("violations", [])),
            scenario_results=_safe_json(scenarios),
            metrics_json=_safe_json(metrics),
            assignments_json=_safe_json(plan.get("assigned", [])),
            compatibility_stats=_safe_json(compatibility.get("stats", {})),
            pipeline_steps=_safe_json(metadata.get("steps", [])),
        )

        db.add(outcome)
        db.commit()
        db.refresh(outcome)

        outcome_id = outcome.id

        # --- Check if retraining should be triggered ---
        total_outcomes = db.query(OptimizationOutcome).count()
        should_retrain = (total_outcomes % RETRAIN_EVERY_N_OUTCOMES == 0) and total_outcomes > 0

        print(f"[Outcome Logger] Logged outcome #{outcome_id} "
              f"(total: {total_outcomes}, retrain: {should_retrain})")

        return {
            "outcome_id": outcome_id,
            "total_outcomes": total_outcomes,
            "should_retrain": should_retrain,
        }

    except Exception as e:
        print(f"[Outcome Logger] Failed to log outcome: {e}")
        db.rollback()
        return {
            "outcome_id": None,
            "total_outcomes": 0,
            "should_retrain": False,
            "error": str(e),
        }

    finally:
        db.close()


def trigger_retraining() -> Dict:
    """
    Trigger the compatibility model to retrain.

    Called when the outcome count hits the RETRAIN_EVERY_N_OUTCOMES threshold.
    The retrained model will use the same synthetic training data pipeline
    but with a new seed — in a production system, this would incorporate
    actual outcome data to improve future predictions.

    Returns:
        Training result dict from the compatibility model
    """
    try:
        from backend.app.agents.tools.compatibility_scoring_tool import retrain_model

        print("[Outcome Logger] Triggering compatibility model retraining...")
        result = retrain_model()
        print(f"[Outcome Logger] Retraining complete: {result.get('model_type')} "
              f"with F1={result.get('best_f1')}")
        return result

    except Exception as e:
        print(f"[Outcome Logger] Retraining failed: {e}")
        return {"status": "failed", "error": str(e)}


def get_outcome_history(limit: int = 20) -> list:
    """
    Fetch recent optimization outcomes for the history dashboard.

    Returns a list of outcome summaries ordered by most recent first.
    Used by the /history frontend page.
    """
    db = SessionLocal()
    try:
        outcomes = (
            db.query(OptimizationOutcome)
            .order_by(OptimizationOutcome.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": o.id,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "plan_id": o.plan_id,
                "solver_used": o.solver_used,
                "is_feasible": bool(o.is_feasible),
                "total_shipments": o.total_shipments,
                "trucks_used": o.trucks_used,
                "utilization_achieved": o.utilization_achieved,
                "cost_saving_pct": o.cost_saving_pct,
                "carbon_saving_pct": o.carbon_saving_pct,
                "trip_reduction_pct": o.trip_reduction_pct,
                "pipeline_duration_ms": o.pipeline_duration_ms,
            }
            for o in outcomes
        ]

    finally:
        db.close()


def _safe_json(data) -> Optional[str]:
    """
    Safely serialize data to JSON string.
    Returns None if serialization fails instead of crashing.
    """
    if data is None:
        return None
    try:
        return json.dumps(data, default=str)
    except (TypeError, ValueError) as e:
        print(f"[Outcome Logger] JSON serialization failed: {e}")
        return None