"""
Consolidation plan models — ConsolidationPlan, PlanAssignment, ScenarioResult.

These three tables are tightly coupled:
- ConsolidationPlan: the top-level result of an optimization run
- PlanAssignment: each row maps one vehicle to its assigned shipments within a plan
- ScenarioResult: stores metrics from the 4 simulation scenarios for comparison

Kept in one file because they reference each other via foreign keys
and are always queried together.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.sql import func
from backend.app.db.base import Base
import enum


class PlanStatusEnum(str, enum.Enum):
    """
    Lifecycle of a consolidation plan.
    - DRAFT: plan created but solver hasn't run yet
    - OPTIMIZED: solver completed, assignments are final
    - EXECUTED: plan has been acted on operationally (future use)
    """
    DRAFT = "DRAFT"
    OPTIMIZED = "OPTIMIZED"
    EXECUTED = "EXECUTED"


class ScenarioTypeEnum(str, enum.Enum):
    """
    The four simulation scenarios we run on every plan.
    Each scenario tweaks constraints to explore trade-offs:
    - STRICT_SLA: no time window relaxation, penalizes any SLA breach
    - FLEXIBLE_SLA: allows ±30min window flexibility for better consolidation
    - VEHICLE_SHORTAGE: simulates fewer available trucks (e.g. 70% fleet)
    - DEMAND_SURGE: simulates 1.5x shipment volume to stress-test capacity
    """
    STRICT_SLA = "STRICT_SLA"
    FLEXIBLE_SLA = "FLEXIBLE_SLA"
    VEHICLE_SHORTAGE = "VEHICLE_SHORTAGE"
    DEMAND_SURGE = "DEMAND_SURGE"


class ConsolidationPlan(Base):
    """
    Top-level optimization result. One row per /optimize call.
    Stores summary metrics that the dashboard displays as before/after comparisons.
    """
    __tablename__ = "consolidation_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Automatically set when the plan is created — used for sorting and history.
    created_at = Column(DateTime, server_default=func.now())

    # Tracks whether this plan is still being built or is finalized.
    status = Column(SAEnum(PlanStatusEnum), default=PlanStatusEnum.DRAFT)

    # Number of trucks the optimizer decided to use for this plan.
    total_trucks = Column(Integer, nullable=True)

    # Baseline: how many individual trips would be needed WITHOUT consolidation.
    # Used to calculate trip reduction percentage.
    trips_baseline = Column(Integer, nullable=True)

    # Average truck utilization across all assignments (0.0 to 100.0).
    # Higher is better — means trucks are fuller and fewer trips are wasted.
    avg_utilization = Column(Float, nullable=True)

    # Percentage cost saved vs. the no-consolidation baseline.
    cost_saving_pct = Column(Float, nullable=True)

    # Percentage carbon emissions saved — proportional to trip/distance reduction.
    carbon_saving_pct = Column(Float, nullable=True)


class PlanAssignment(Base):
    """
    Maps a vehicle to its assigned shipments within a consolidation plan.
    One row per vehicle used. A plan with 5 trucks will have 5 PlanAssignment rows.
    """
    __tablename__ = "plan_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Which plan this assignment belongs to.
    plan_id = Column(Integer, ForeignKey("consolidation_plans.id"), nullable=False)

    # Which vehicle was assigned these shipments.
    vehicle_id = Column(String, ForeignKey("vehicles.vehicle_id"), nullable=False)

    # List of shipment IDs assigned to this vehicle, stored as a JSON string.
    # Example: '["S001", "S003", "S007"]'
    # We use Text instead of a JSON column type for SQLite compatibility.
    shipment_ids = Column(Text, nullable=False)

    # How full this vehicle is (0.0 to 100.0), based on the binding constraint
    # (whichever is tighter — weight or volume).
    utilization_pct = Column(Float, nullable=True)

    # Extra distance added by serving multiple pickup/delivery points
    # instead of direct routes. Lower is better.
    route_detour_km = Column(Float, nullable=True)


class ScenarioResult(Base):
    """
    Stores the output of one simulation scenario for a given plan.
    Each plan gets 4 rows here — one per ScenarioTypeEnum value.
    Agent 4 (Scenario Recommender) reads these to compare and recommend.
    """
    __tablename__ = "scenario_results"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Which plan this scenario was run against.
    plan_id = Column(Integer, ForeignKey("consolidation_plans.id"), nullable=False)

    # Which of the 4 scenarios this result represents.
    scenario_type = Column(SAEnum(ScenarioTypeEnum), nullable=False)

    # How many trucks were needed under this scenario's constraints.
    trucks_used = Column(Integer, nullable=True)

    # Average utilization achieved under this scenario (0.0 to 100.0).
    avg_utilization = Column(Float, nullable=True)

    # Total transportation cost under this scenario (in currency units).
    total_cost = Column(Float, nullable=True)

    # Total carbon emissions estimate (in kg CO2 equivalent).
    carbon_emissions = Column(Float, nullable=True)

    # Percentage of shipments that met their delivery SLA (0.0 to 100.0).
    # Strict SLA scenario typically has lower values; Flexible SLA has higher.
    sla_success_rate = Column(Float, nullable=True)