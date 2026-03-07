"""
Metrics endpoint — returns before/after impact summary for a plan.

GET /metrics?plan_id=1 returns the plan's summary metrics alongside
all scenario results. The frontend uses this to render:
- Impact cards (trip reduction %, cost savings %, carbon savings %)
- Scenario comparison bar charts (Recharts)
- Utilization gauges
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.plan import ConsolidationPlan, ScenarioResult
from backend.app.schemas.plan import MetricsResponse, ScenarioResultResponse

router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(
    plan_id: int = Query(..., description="ID of the consolidation plan to get metrics for"),
    db: Session = Depends(get_db),
):
    """
    Fetch summary metrics and scenario comparison for a plan.

    Combines two things into one response:
    1. The plan's own summary metrics (trucks used, utilization, savings)
    2. All scenario results so the frontend can build comparison charts

    The plan_id is required — there's no "global metrics" view yet.
    We may add that later if the team wants cross-plan analytics.
    """
    # Look up the plan
    plan = db.query(ConsolidationPlan).filter(ConsolidationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")

    # Fetch all scenario results for comparison charts
    scenarios = db.query(ScenarioResult).filter(ScenarioResult.plan_id == plan_id).all()

    return MetricsResponse(
        plan_id=plan.id,
        total_trucks=plan.total_trucks,
        trips_baseline=plan.trips_baseline,
        avg_utilization=plan.avg_utilization,
        cost_saving_pct=plan.cost_saving_pct,
        carbon_saving_pct=plan.carbon_saving_pct,
        scenarios=[ScenarioResultResponse.model_validate(s) for s in scenarios],
    )