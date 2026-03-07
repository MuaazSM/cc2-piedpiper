"""
Pydantic schemas for ConsolidationPlan, PlanAssignment, and ScenarioResult.

These schemas structure the optimizer's output for the frontend.
A plan response includes everything the dashboard needs:
the plan summary, each vehicle's assignments, and all scenario results.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PlanAssignmentResponse(BaseModel):
    """
    One vehicle's assignment within a plan.
    shipment_ids comes back as a raw JSON string from the DB —
    the frontend parses it into an array for display.
    """
    id: int
    plan_id: int
    vehicle_id: str
    shipment_ids: str              # JSON string like '["S001", "S003"]'
    utilization_pct: Optional[float] = None
    route_detour_km: Optional[float] = None

    model_config = {"from_attributes": True}


class ScenarioResultResponse(BaseModel):
    """
    Results from one of the 4 simulation scenarios.
    Agent 4 reads these to recommend the best plan per objective.
    """
    id: int
    plan_id: int
    scenario_type: str             # One of: STRICT_SLA, FLEXIBLE_SLA, VEHICLE_SHORTAGE, DEMAND_SURGE
    trucks_used: Optional[int] = None
    avg_utilization: Optional[float] = None
    total_cost: Optional[float] = None
    carbon_emissions: Optional[float] = None
    sla_success_rate: Optional[float] = None

    model_config = {"from_attributes": True}


class PlanResponse(BaseModel):
    """
    Full consolidation plan with nested assignments and scenario results.
    This is the main payload returned by GET /plan/{id}.
    The frontend dashboard renders this as the plan detail view.
    """
    id: int
    created_at: Optional[datetime] = None
    status: str
    total_trucks: Optional[int] = None
    trips_baseline: Optional[int] = None
    avg_utilization: Optional[float] = None
    cost_saving_pct: Optional[float] = None
    carbon_saving_pct: Optional[float] = None
    assignments: List[PlanAssignmentResponse] = []
    scenarios: List[ScenarioResultResponse] = []

    model_config = {"from_attributes": True}


class MetricsResponse(BaseModel):
    """
    Before/after metrics for a plan, plus scenario comparison.
    Used by GET /metrics to power the dashboard's impact summary cards
    and scenario comparison charts.
    """
    plan_id: int
    total_trucks: Optional[int] = None
    trips_baseline: Optional[int] = None
    avg_utilization: Optional[float] = None
    cost_saving_pct: Optional[float] = None
    carbon_saving_pct: Optional[float] = None
    scenarios: List[ScenarioResultResponse] = []