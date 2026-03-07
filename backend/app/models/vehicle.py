"""
Vehicle ORM model.

Represents a truck/vehicle in the fleet. The optimizer assigns shipments
to vehicles based on their weight and volume capacities. Operating cost
feeds into the objective function — the solver minimizes total trip cost
while maximizing utilization.
"""

from sqlalchemy import Column, String, Float
from backend.app.db.base import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    # Unique vehicle identifier (e.g. "V001", "TRUCK-MH-1234")
    vehicle_id = Column(String, primary_key=True, index=True)

    # Type label for grouping (e.g. "small", "medium", "large", "refrigerated")
    vehicle_type = Column(String, nullable=False)

    # Maximum weight this vehicle can carry (in kg).
    # Constraint: sum of assigned shipment weights <= capacity_weight
    capacity_weight = Column(Float, nullable=False)

    # Maximum volume this vehicle can carry (in cubic meters).
    # Constraint: sum of assigned shipment volumes <= capacity_volume
    capacity_volume = Column(Float, nullable=False)

    # Cost per trip for this vehicle (in currency units).
    # Used in the objective function: minimize total Σ operating_cost across used trucks.
    operating_cost = Column(Float, nullable=False)