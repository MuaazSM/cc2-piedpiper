"""
Simulation endpoint — runs 4 scenario simulations and analyzes results.

POST /simulate takes a plan_id, generates results for all 4 scenarios,
then passes them through the Scenario Recommendation Agent for
multi-objective comparison and recommendation.

Query params:
- plan_id: which plan to simulate against
- cost_weight: weight for cost in balanced scoring (default 0.40)
- sla_weight: weight for SLA in balanced scoring (default 0.35)
- carbon_weight: weight for carbon in balanced scoring (default 0.25)

Returns:
{
    "scenarios": [ ... ],     // raw scenario results
    "analysis": { ... }       // agent's recommendations and trade-offs
}
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.plan import ConsolidationPlan, ScenarioResult, ScenarioTypeEnum
from backend.app.schemas.plan import ScenarioResultResponse
from backend.app.agents.scenario_agent import run_scenario_analysis
from typing import List

router = APIRouter()


@router.post("/simulate")
def run_simulation(
    plan_id: int = Query(..., description="ID of the consolidation plan to simulate"),
    cost_weight: float = Query(0.40, ge=0, le=1, description="Weight for cost in balanced scoring"),
    sla_weight: float = Query(0.35, ge=0, le=1, description="Weight for SLA in balanced scoring"),
    carbon_weight: float = Query(0.25, ge=0, le=1, description="Weight for carbon in balanced scoring"),
    db: Session = Depends(get_db),
):
    """
    Run all 4 scenario simulations for a given plan, then analyze results.

    The simulation engine (placeholder for now) generates metrics for
    each scenario. Then Agent 4 (Scenario Recommender) compares them
    across cost, SLA, and carbon objectives to produce recommendations.

    The weights let the frontend expose a slider where users can
    adjust their priorities and see how the recommendation changes.
    """
    # Verify the plan exists before running simulations
    plan = db.query(ConsolidationPlan).filter(ConsolidationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")

    # Clear any previous simulation results for this plan
    # (in case the user re-runs simulations after tweaking data)
    db.query(ScenarioResult).filter(ScenarioResult.plan_id == plan_id).delete()
    db.commit()

    # --- PLACEHOLDER: actual simulation engine goes here ---
    # For now, generate dummy metrics for each scenario type.
    # These will be replaced by real solver re-runs with modified constraints.
    # The placeholder values are designed to show realistic trade-offs:
    # - Strict SLA: highest SLA, highest cost, moderate carbon
    # - Flexible SLA: best cost, moderate SLA, lowest carbon
    # - Vehicle Shortage: fewest trucks, highest utilization, lower SLA
    # - Demand Surge: most trucks, lowest utilization, highest cost & carbon
    placeholder_scenarios = [
        {
            "scenario_type": ScenarioTypeEnum.STRICT_SLA,
            "trucks_used": 12,
            "avg_utilization": 72.5,
            "total_cost": 45000.0,
            "carbon_emissions": 1200.0,
            "sla_success_rate": 95.0,
        },
        {
            "scenario_type": ScenarioTypeEnum.FLEXIBLE_SLA,
            "trucks_used": 9,
            "avg_utilization": 85.3,
            "total_cost": 35000.0,
            "carbon_emissions": 950.0,
            "sla_success_rate": 88.0,
        },
        {
            "scenario_type": ScenarioTypeEnum.VEHICLE_SHORTAGE,
            "trucks_used": 7,
            "avg_utilization": 91.0,
            "total_cost": 38000.0,
            "carbon_emissions": 1050.0,
            "sla_success_rate": 78.0,
        },
        {
            "scenario_type": ScenarioTypeEnum.DEMAND_SURGE,
            "trucks_used": 15,
            "avg_utilization": 68.0,
            "total_cost": 55000.0,
            "carbon_emissions": 1500.0,
            "sla_success_rate": 70.0,
        },
    ]

    # Save scenario results to the database
    created = []
    for scenario_data in placeholder_scenarios:
        result = ScenarioResult(plan_id=plan_id, **scenario_data)
        db.add(result)
        created.append(result)

    db.commit()

    # Refresh to pick up auto-generated IDs
    for c in created:
        db.refresh(c)

    # Convert ORM objects to dicts for the scenario agent
    scenario_dicts = [
        {
            "id": c.id,
            "plan_id": c.plan_id,
            "scenario_type": c.scenario_type.value if c.scenario_type else None,
            "trucks_used": c.trucks_used,
            "avg_utilization": c.avg_utilization,
            "total_cost": c.total_cost,
            "carbon_emissions": c.carbon_emissions,
            "sla_success_rate": c.sla_success_rate,
        }
        for c in created
    ]

    # --- Run the Scenario Recommendation Agent ---
    # This compares all 4 scenarios across cost/SLA/carbon and
    # produces ranked recommendations with trade-off analysis.
    analysis = run_scenario_analysis(
        scenarios=scenario_dicts,
        cost_weight=cost_weight,
        sla_weight=sla_weight,
        carbon_weight=carbon_weight,
    )

    return {
        "scenarios": scenario_dicts,
        "analysis": analysis,
    }