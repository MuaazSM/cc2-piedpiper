"""
Optimization endpoint — triggers the full consolidation pipeline.

POST /optimize kicks off:
1. Validation Agent checks input data 
2. ML compatibility scoring (TODO)
3. OR-Tools solver builds the plan (TODO — placeholder for now)
4. Insight Agent explains the results 

Returns a consistent JSON shape every time:
- validation: always present (errors, warnings, info, llm_summary)
- plan: present only if validation passed and solver ran
- insights: present only if a plan was generated
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.shipment import Shipment
from backend.app.models.vehicle import Vehicle
from backend.app.models.plan import ConsolidationPlan, PlanStatusEnum
from backend.app.agents.validation_agent import run_validation
from backend.app.agents.insight_agent import run_insight_analysis

router = APIRouter()


@router.post("/optimize")
def run_optimization(db: Session = Depends(get_db)):
    """
    Trigger the optimization pipeline.

    Always returns a 200 with a consistent response shape:
    {
        "validation": { ... },   // always present
        "plan": { ... } | null,  // null if validation failed or no data
        "insights": { ... } | null  // null if no plan was generated
    }

    The frontend uses validation.is_valid to decide whether to show
    the plan view or the validation issues panel. Warnings and info
    are shown alongside the plan even when optimization succeeds.
    Insights are rendered in the agent insights panel.
    """
    # Step 0: Load all shipments and vehicles from the DB
    # Convert ORM objects to plain dicts so the agents
    # don't need to know about SQLAlchemy internals.
    shipment_rows = db.query(Shipment).all()
    vehicle_rows = db.query(Vehicle).all()

    shipments = [
        {
            "shipment_id": s.shipment_id,
            "origin": s.origin,
            "destination": s.destination,
            "pickup_time": s.pickup_time.isoformat() if s.pickup_time else None,
            "delivery_time": s.delivery_time.isoformat() if s.delivery_time else None,
            "weight": s.weight,
            "volume": s.volume,
            "priority": s.priority.value if s.priority else None,
            "special_handling": s.special_handling,
            "status": s.status.value if s.status else None,
        }
        for s in shipment_rows
    ]

    vehicles = [
        {
            "vehicle_id": v.vehicle_id,
            "vehicle_type": v.vehicle_type,
            "capacity_weight": v.capacity_weight,
            "capacity_volume": v.capacity_volume,
            "operating_cost": v.operating_cost,
        }
        for v in vehicle_rows
    ]

    # Handle empty database — no point running validation on nothing
    if not shipments:
        return {
            "validation": {
                "is_valid": False,
                "errors": [{"severity": "ERROR", "shipment_id": None, "field": None,
                            "message": "No shipments found. Upload shipments first via POST /shipments or POST /dev/seed."}],
                "warnings": [],
                "info": [],
                "summary_counts": {"total_shipments": 0, "total_vehicles": len(vehicles),
                                   "error_count": 1, "warning_count": 0, "info_count": 0},
                "llm_summary": None,
            },
            "plan": None,
            "insights": None,
        }

    if not vehicles:
        return {
            "validation": {
                "is_valid": False,
                "errors": [{"severity": "ERROR", "shipment_id": None, "field": None,
                            "message": "No vehicles found. Seed vehicle fleet first via POST /dev/seed."}],
                "warnings": [],
                "info": [],
                "summary_counts": {"total_shipments": len(shipments), "total_vehicles": 0,
                                   "error_count": 1, "warning_count": 0, "info_count": 0},
                "llm_summary": None,
            },
            "plan": None,
            "insights": None,
        }

    # Step 1: Run the Validation Agent
    validation_report = run_validation(shipments, vehicles)

    # If validation found critical errors, return the report without running the solver.
    # The frontend shows the validation panel so the user can fix their data.
    if not validation_report["is_valid"]:
        return {
            "validation": validation_report,
            "plan": None,
            "insights": None,
        }

    # Step 2: TODO — ML compatibility scoring
    # compatibility_graph = compatibility_model.score(shipments)

    # Step 3: TODO — OR-Tools solver
    # solver_result = solver.optimize(shipments, vehicles, compatibility_graph)

    # PLACEHOLDER: create a draft plan until solver is wired in
    plan = ConsolidationPlan(
        status=PlanStatusEnum.DRAFT,
        total_trucks=0,
        trips_baseline=len(shipments),
        avg_utilization=0.0,
        cost_saving_pct=0.0,
        carbon_saving_pct=0.0,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    # Build the plan dict for the response and for the insight agent
    plan_dict = {
        "id": plan.id,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "status": plan.status.value,
        "total_trucks": plan.total_trucks,
        "trips_baseline": plan.trips_baseline,
        "avg_utilization": plan.avg_utilization,
        "cost_saving_pct": plan.cost_saving_pct,
        "carbon_saving_pct": plan.carbon_saving_pct,
        "assignments": [],
        "scenarios": [],
    }

    # Step 4: Run the Insight Agent
    # Even with a draft plan (no assignments), the insight agent will return
    # a "no assignments to analyze" message. Once the solver is wired in,
    # this will produce full lane-level insights and risk flags.
    insights = run_insight_analysis(
        plan=plan_dict,
        assignments=[],  # Empty until solver is wired in
        shipments=shipments,
        vehicles=vehicles,
    )

    # Step 5: TODO — Constraint Relaxation Agent (if infeasible)
    # Step 6: TODO — Scenario Recommendation Agent

    return {
        "validation": validation_report,
        "plan": plan_dict,
        "insights": insights,
    }