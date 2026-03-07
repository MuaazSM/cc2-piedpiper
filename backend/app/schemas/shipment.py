"""
Pydantic schemas for Shipment endpoints.

These schemas handle request validation and response serialization.
FastAPI uses them to:
- Validate incoming JSON on POST requests
- Serialize ORM objects into clean JSON responses
- Generate OpenAPI docs automatically
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ShipmentCreate(BaseModel):
    """
    Schema for creating a single shipment.
    Used by POST /shipments — the client sends this JSON structure.
    shipment_id is required because it's user-provided (e.g. from their TMS).
    """
    shipment_id: str
    origin: str
    destination: str
    pickup_time: datetime
    delivery_time: datetime
    weight: float
    volume: float
    priority: str = "MEDIUM"           # Defaults to MEDIUM if not provided
    special_handling: Optional[str] = None  # e.g. "refrigerated", "fragile", or left blank
    status: str = "PENDING"            # New shipments start as PENDING


class ShipmentResponse(BaseModel):
    """
    Schema for returning a shipment in API responses.
    Mirrors the DB model exactly — what goes in is what comes out.
    model_config with from_attributes lets Pydantic read SQLAlchemy ORM objects directly.
    """
    shipment_id: str
    origin: str
    destination: str
    pickup_time: datetime
    delivery_time: datetime
    weight: float
    volume: float
    priority: str
    special_handling: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}


class ShipmentListResponse(BaseModel):
    """
    Wrapper for paginated shipment lists.
    Returns the total count (for frontend pagination) along with the actual items.
    """
    total: int
    shipments: List[ShipmentResponse]