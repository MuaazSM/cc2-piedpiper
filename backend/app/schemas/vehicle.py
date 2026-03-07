"""
Pydantic schemas for Vehicle endpoints.

Vehicles are part of the fleet configuration — they get seeded
along with shipments and are referenced by the optimizer when
building consolidation plans.
"""

from pydantic import BaseModel


class VehicleCreate(BaseModel):
    """
    Schema for registering a vehicle in the fleet.
    All fields are required — the optimizer needs all of them
    to make assignment decisions.
    """
    vehicle_id: str
    vehicle_type: str              # e.g. "small", "large", "refrigerated"
    capacity_weight: float         # Max weight in kg
    capacity_volume: float         # Max volume in cubic meters
    operating_cost: float          # Cost per trip in currency units


class VehicleResponse(BaseModel):
    """
    Schema for returning vehicle data in API responses.
    """
    vehicle_id: str
    vehicle_type: str
    capacity_weight: float
    capacity_volume: float
    operating_cost: float

    model_config = {"from_attributes": True}