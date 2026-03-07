"""
Optimization endpoint — triggers the full LangGraph agent pipeline.

POST /optimize runs the LangGraph state graph which handles everything:
data loading, validation, ML scoring, guardrail, solver, simulation,
insights, scenario recommendation, and metrics.

The route is now a thin wrapper — it invokes the graph, saves results
to the DB, and returns the unified response.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.plan import (
    ConsolidationPlan, PlanAssignment, ScenarioResult,
    PlanStatusEnum, ScenarioTypeEnum,
)
from backend.app.agents.langgraph_pipeline import run_pipeline
import json

router = APIRouter()


@router.post("/optimize")
def run_optimization(
    run_simulation: bool = Query(True, description="Whether to run scenario simulations"),
    run_llm: bool = Query(True, description="Whether to generate LLM narratives (needs GOOGLE_API_KEY)"),
    cost_weight: float = Query(0.40, ge=0, le=1, description="Cost weight for balanced scenario scoring"),
    sla_weight: float = Query(0.35, ge=0, le=1, description="SLA weight for balanced scenario scoring"),
    carbon_weight: float = Query(0.25, ge=0, le=1, description="Carbon weight for balanced scenario scoring"),
    db: Session = Depends(get_db),
):
    """
    Trigger the full LangGraph optimization pipeline.

    The graph is now self-contained — it loads data from the DB,
    runs all agents and tools, and returns the unified response.
    This route just invokes the graph, persists the results, and
    returns the response.
    """
    # --- Run the LangGraph pipeline ---
    # The graph handles its own data loading via the Shipment Data Tool.
    # We only pass config — no shipments or vehicles needed here.
    config = {
        "run_simulation": run_simulation,
        "run_llm": run_llm,
        "cost_weight": cost_weight,
        "sla_weight": sla_weight,
        "carbon_weight": carbon_weight,
    }

    result = run_pipeline(shipments=[], vehicles=[], config=config)

    # If the pipeline returned an error (empty DB, validation failure),
    # return the result as-is — no DB persistence needed
    if not result:
        return result

    # --- Persist results to DB ---
    plan_data = result.get("plan")
    if plan_data and plan_data.get("status") not in ("FAILED", None):
        db_status = PlanStatusEnum.DRAFT if plan_data.get("is_infeasible") else PlanStatusEnum.OPTIMIZED

        db_plan = ConsolidationPlan(
            status=db_status,
            total_trucks=plan_data.get("total_trucks", 0),
            trips_baseline=plan_data.get("trips_baseline", 0),
            avg_utilization=plan_data.get("avg_utilization", 0),
            cost_saving_pct=plan_data.get("cost_saving_pct", 0),
            carbon_saving_pct=plan_data.get("carbon_saving_pct", 0),
        )
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)

        # Inject DB-generated ID into the response
        result["plan"]["id"] = db_plan.id
        result["plan"]["created_at"] = db_plan.created_at.isoformat() if db_plan.created_at else None

        # Save assignments
        for assignment in plan_data.get("assigned", []):
            db_assignment = PlanAssignment(
                plan_id=db_plan.id,
                vehicle_id=assignment.get("vehicle_id", ""),
                shipment_ids=json.dumps(assignment.get("shipment_ids", [])),
                utilization_pct=assignment.get("utilization_pct"),
                route_detour_km=assignment.get("route_detour_km"),
            )
            db.add(db_assignment)

        # Save scenario results
        for scenario in (result.get("scenarios") or []):
            try:
                scenario_type = ScenarioTypeEnum(scenario.get("scenario_type", ""))
            except ValueError:
                continue

            db_scenario = ScenarioResult(
                plan_id=db_plan.id,
                scenario_type=scenario_type,
                trucks_used=scenario.get("trucks_used"),
                avg_utilization=scenario.get("avg_utilization"),
                total_cost=scenario.get("total_cost"),
                carbon_emissions=scenario.get("carbon_emissions"),
                sla_success_rate=scenario.get("sla_success_rate"),
            )
            db.add(db_scenario)

        db.commit()

    return result