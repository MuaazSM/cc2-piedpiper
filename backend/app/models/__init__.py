"""
Models package — re-exports all ORM models and enums.

This file exists so that other parts of the app can do:
    from backend.app.models import Shipment, Vehicle, ConsolidationPlan
instead of importing from individual files.

It also ensures all models are registered with Base.metadata
when we run create_all() at startup — SQLAlchemy only knows about
models that have been imported at least once.
"""

from backend.app.models.shipment import Shipment, PriorityEnum, StatusEnum
from backend.app.models.vehicle import Vehicle
from backend.app.models.plan import (
    ConsolidationPlan,
    PlanAssignment,
    ScenarioResult,
    PlanStatusEnum,
    ScenarioTypeEnum,
)
from backend.app.models.outcome import OptimizationOutcome