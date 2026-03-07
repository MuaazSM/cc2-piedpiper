"""
Plan retrieval endpoint — fetch a consolidation plan by ID.

GET /plan/{id} returns the full plan including:
- Summary metrics (trucks used, utilization, savings)
- All vehicle-to-shipment assignments
- All scenario simulation results

This is the main endpoint the frontend's plan detail page calls.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.plan import ConsolidationPlan, PlanAssignment, ScenarioResult
from backend.app.schemas.plan import PlanResponse, PlanAssignmentResponse, ScenarioResultResponse

router = APIRouter()


@router.get("/plan/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """
    Fetch a consolidation plan by ID with all nested data.

    Queries three tables:
    1. The plan itself (summary metrics)
    2. All assignments for this plan (which vehicle got which shipments)
    3. All scenario results for this plan (4 scenarios worth of metrics)

    Returns everything nested in a single response so the frontend
    doesn't need to make 3 separate API calls.
    """
    # Look up the plan — 404 if it doesn't exist
    plan = db.query(ConsolidationPlan).filter(ConsolidationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")

    # Fetch all assignments and scenario results linked to this plan
    assignments = db.query(PlanAssignment).filter(PlanAssignment.plan_id == plan_id).all()
    scenarios = db.query(ScenarioResult).filter(ScenarioResult.plan_id == plan_id).all()

    # Build the nested response manually because we're combining 3 query results.
    # Pydantic's from_attributes handles the ORM-to-dict conversion for each item.
    return PlanResponse(
        id=plan.id,
        created_at=plan.created_at,
        status=plan.status.value,
        total_trucks=plan.total_trucks,
        trips_baseline=plan.trips_baseline,
        avg_utilization=plan.avg_utilization,
        cost_saving_pct=plan.cost_saving_pct,
        carbon_saving_pct=plan.carbon_saving_pct,
        assignments=[PlanAssignmentResponse.model_validate(a) for a in assignments],
        scenarios=[ScenarioResultResponse.model_validate(s) for s in scenarios],
    )