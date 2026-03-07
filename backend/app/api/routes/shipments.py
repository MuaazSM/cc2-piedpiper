"""
Shipment endpoints — create and list shipments.

POST /shipments accepts either a single shipment or a list of shipments
(bulk upload). This flexibility lets the frontend send one-off entries
from a form OR batch-upload from a CSV/file.

GET /shipments returns a filtered, paginated list for the shipment table view.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Union
from backend.app.db.session import get_db
from backend.app.models.shipment import Shipment
from backend.app.schemas.shipment import ShipmentCreate, ShipmentResponse, ShipmentListResponse

router = APIRouter()


@router.post("/shipments", response_model=List[ShipmentResponse])
def create_shipments(
    payload: Union[ShipmentCreate, List[ShipmentCreate]],
    db: Session = Depends(get_db),
):
    """
    Create one or more shipments.

    Accepts either a single ShipmentCreate object or a list of them.
    If a single object comes in, we wrap it in a list so the rest of
    the logic stays uniform. Each shipment is checked for duplicate IDs
    before insertion — we don't want silent overwrites.
    """
    # Normalize input: wrap single shipment in a list for uniform processing
    if isinstance(payload, ShipmentCreate):
        shipments_in = [payload]
    else:
        shipments_in = payload

    created = []
    for s in shipments_in:
        # Check if this shipment ID already exists in the database
        existing = db.query(Shipment).filter(Shipment.shipment_id == s.shipment_id).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Shipment {s.shipment_id} already exists. Use unique IDs.",
            )

        # Create the ORM object from the validated Pydantic data
        db_shipment = Shipment(**s.model_dump())
        db.add(db_shipment)
        created.append(db_shipment)

    # Commit all at once — if any fail, the whole batch rolls back
    db.commit()

    # Refresh each object so SQLAlchemy loads any DB-generated defaults
    for c in created:
        db.refresh(c)

    return created


@router.get("/shipments", response_model=ShipmentListResponse)
def list_shipments(
    origin: Optional[str] = Query(None, description="Filter by origin city"),
    destination: Optional[str] = Query(None, description="Filter by destination city"),
    priority: Optional[str] = Query(None, description="Filter by priority: LOW, MEDIUM, HIGH"),
    status: Optional[str] = Query(None, description="Filter by status: PENDING, ASSIGNED, etc."),
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip (for pagination)"),
    db: Session = Depends(get_db),
):
    """
    List shipments with optional filters and pagination.

    The frontend shipment table calls this with various filter combinations.
    Filters are additive (AND logic) — if you pass origin=Mumbai&priority=HIGH,
    you get only HIGH priority shipments from Mumbai.
    """
    # Start with a base query, then chain filters as needed
    query = db.query(Shipment)

    if origin:
        query = query.filter(Shipment.origin == origin)
    if destination:
        query = query.filter(Shipment.destination == destination)
    if priority:
        query = query.filter(Shipment.priority == priority)
    if status:
        query = query.filter(Shipment.status == status)

    # Get total count BEFORE applying limit/offset (needed for pagination UI)
    total = query.count()

    # Apply pagination and fetch results
    shipments = query.offset(offset).limit(limit).all()

    return ShipmentListResponse(total=total, shipments=shipments)