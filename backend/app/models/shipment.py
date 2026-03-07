"""
Shipment ORM model.

Represents a single freight shipment in the system. Each shipment has
an origin, destination, time windows for pickup/delivery, physical
dimensions (weight + volume), a priority level, and a processing status.

This is the core input entity — the optimizer reads shipments and
groups them into vehicle loads.
"""

from sqlalchemy import Column, String, Float, DateTime, Enum as SAEnum
from backend.app.db.base import Base
import enum


class PriorityEnum(str, enum.Enum):
    """
    Shipment priority levels.
    HIGH priority shipments get stricter time window enforcement
    in the optimizer and are less likely to be relaxed by Agent 3.
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class StatusEnum(str, enum.Enum):
    """
    Tracks where a shipment is in the pipeline.
    - PENDING: just uploaded, not yet optimized
    - ASSIGNED: optimizer has placed it in a consolidation plan
    - IN_TRANSIT: vehicle is en route (future use)
    - DELIVERED: shipment completed (future use)
    """
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"


class Shipment(Base):
    __tablename__ = "shipments"

    # Unique shipment identifier — provided by the user or generated (e.g. "S001")
    shipment_id = Column(String, primary_key=True, index=True)

    # Origin and destination cities/locations (e.g. "Mumbai", "Delhi")
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)

    # Time windows — the optimizer must respect these when grouping shipments.
    # A shipment can only share a truck with another if their windows overlap enough.
    pickup_time = Column(DateTime, nullable=False)
    delivery_time = Column(DateTime, nullable=False)

    # Physical dimensions — used in capacity constraints.
    # The solver ensures total weight and volume per truck don't exceed limits.
    weight = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    # Priority affects how aggressively the optimizer protects this shipment's SLA.
    priority = Column(SAEnum(PriorityEnum), default=PriorityEnum.MEDIUM)

    # Free-text field for special requirements (e.g. "refrigerated", "fragile").
    # The compatibility model uses this to decide if two shipments can share a truck.
    special_handling = Column(String, nullable=True)

    # Current processing status — updated as the shipment moves through the pipeline.
    status = Column(SAEnum(StatusEnum), default=StatusEnum.PENDING)