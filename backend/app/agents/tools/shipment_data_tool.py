"""
Shipment Data Tool — LangGraph tool node for the Observe phase.

This is the first node in the pipeline. Its job is simple but critical:
fetch all shipments and vehicles from the database and load them into
AgentState so every downstream node has data to work with.

By putting the DB fetch inside the graph (instead of in the route),
the pipeline becomes self-contained — you invoke it with just a config
dict and it handles its own data loading. This makes testing easier
(no need for FastAPI) and keeps the route thin.

Creates its own DB session using the same engine as the rest of the app.
The session is opened, used, and closed within this node — no leaked
connections.
"""

from typing import List, Dict, Tuple
from backend.app.db.session import SessionLocal
from backend.app.models.shipment import Shipment
from backend.app.models.vehicle import Vehicle


def fetch_shipment_data() -> Tuple[List[Dict], List[Dict]]:
    """
    Query all shipments and vehicles from the database.

    Opens a fresh DB session, fetches everything, converts ORM objects
    to plain dicts (so downstream agents don't need SQLAlchemy), and
    closes the session.

    Returns:
        Tuple of (shipments_list, vehicles_list) where each item is
        a list of plain dicts matching the schema the agents expect.

    Raises:
        Exception if the DB connection fails — caught by the pipeline's
        error handling in the node wrapper.
    """
    db = SessionLocal()
    try:
        # Fetch all shipments and convert to plain dicts.
        # We do the conversion here so no other node needs to know
        # about SQLAlchemy models or ORM object behavior.
        shipment_rows = db.query(Shipment).all()
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

        # Fetch all vehicles and convert to plain dicts
        vehicle_rows = db.query(Vehicle).all()
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

        return shipments, vehicles

    finally:
        # Always close the session — even if the query throws an error.
        # This prevents connection leaks.
        db.close()