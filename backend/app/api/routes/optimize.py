"""
Optimization endpoint — triggers the full consolidation pipeline.

POST /optimize kicks off:
1. Validation Agent checks input data
2. ML compatibility scoring (TODO)
3. OR-Tools solver builds the plan (TODO)
4. Insight Agent explains the results (TODO)

Returns a consistent JSON shape every time:
- validation: always present (errors, warnings, info, llm_summary)
- plan: present only if validation passed and solver ran
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.shipment import Shipment
from backend.app.models.vehicle import Vehicle
from backend.app.models.plan import ConsolidationPlan, PlanStatusEnum
from backend.app.agents.validation_agent import run_validation

router = APIRouter()


@router.post("/optimize")
def run_optimization(db: Session = Depends(get_db)):
    """
    Trigger the optimization pipeline.

    Always returns a 200 with a consistent response shape:
    {
        "validation": { ... },   // always present
        "plan": { ... } | null   // null if validation failed or no data
    }

    The frontend uses validation.is_valid to decide whether to show
    the plan view or the validation issues panel. Warnings and info
    are shown alongside the plan even when optimization succeeds.
    """
    # --- Step 0: Load all shipments and vehicles from the DB ---
    # Convert ORM objects to plain dicts so the validation agent
    # doesn't need to know about SQLAlchemy internals.
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
        }

    # --- Step 1: Run the Validation Agent ---
    validation_report = run_validation(shipments, vehicles)

    # If validation found critical errors, return the report without running the solver.
    # The frontend shows the validation panel so the user can fix their data.
    if not validation_report["is_valid"]:
        return {
            "validation": validation_report,
            "plan": None,
        }

    # --- Step 2: TODO — ML compatibility scoring ---
    # compatibility_graph = compatibility_model.score(shipments)

    # --- Step 3: TODO — OR-Tools solver ---
    # plan = solver.optimize(shipments, vehicles, compatibility_graph)

    # --- PLACEHOLDER: create a draft plan until solver is wired in ---
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

    # --- Step 4: TODO — Insight Agent explains results ---
    # insight = insight_agent.explain(plan)

    # Return both validation report and plan together.
    # Even on success, warnings and info are included so the frontend
    # can display them alongside the plan results.
    return {
        "validation": validation_report,
        "plan": {
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
        },
    }