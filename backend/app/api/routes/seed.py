"""
Dev seed endpoint — populates the database with synthetic test data.

POST /dev/seed generates fake shipments and vehicles using the
synthetic generator and inserts them directly into the DB.
Supports both normal and surge modes, with configurable counts.

Query params:
- shipment_count: how many shipments to generate (default 20)
- vehicle_count: how many vehicles to generate (default 10)
- mode: "normal" or "surge" (default "normal")
- clear: if true, wipes existing data first (default true)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.shipment import Shipment
from backend.app.models.vehicle import Vehicle
from backend.app.data_loader.synthetic_generator import SyntheticGenerator
from datetime import datetime

router = APIRouter()


@router.post("/seed")
def seed_data(
    shipment_count: int = Query(20, ge=1, le=500, description="Number of shipments to generate"),
    vehicle_count: int = Query(10, ge=1, le=100, description="Number of vehicles to generate"),
    mode: str = Query("normal", description="Generation mode: 'normal' or 'surge'"),
    clear: bool = Query(True, description="Clear existing shipments and vehicles before seeding"),
    db: Session = Depends(get_db),
):
    """
    Seed the database with synthetic Indian freight data.

    This is the fastest way to get a working demo:
    1. Hit POST /dev/seed
    2. Hit POST /optimize
    3. Hit POST /simulate?plan_id=1
    4. Open the frontend dashboard

    The clear=true default means each seed call gives you a fresh dataset.
    Set clear=false if you want to accumulate data across multiple calls.
    """
    generator = SyntheticGenerator()

    # Optionally wipe existing data so we start fresh
    if clear:
        db.query(Shipment).delete()
        db.query(Vehicle).delete()
        db.commit()

    # Generate shipments and vehicles using the synthetic generator
    raw_shipments = generator.generate_shipments(count=shipment_count, mode=mode)
    raw_vehicles = generator.generate_vehicles(count=vehicle_count)

    # Convert generated dicts into ORM objects and add to session.
    # We parse the ISO datetime strings back into datetime objects
    # since the generator outputs strings (for JSON compatibility).
    shipments_created = 0
    for s in raw_shipments:
        db_shipment = Shipment(
            shipment_id=s["shipment_id"],
            origin=s["origin"],
            destination=s["destination"],
            pickup_time=datetime.fromisoformat(s["pickup_time"]),
            delivery_time=datetime.fromisoformat(s["delivery_time"]),
            weight=s["weight"],
            volume=s["volume"],
            priority=s["priority"],
            special_handling=s["special_handling"],
            status=s["status"],
        )
        db.add(db_shipment)
        shipments_created += 1

    vehicles_created = 0
    for v in raw_vehicles:
        db_vehicle = Vehicle(
            vehicle_id=v["vehicle_id"],
            vehicle_type=v["vehicle_type"],
            capacity_weight=v["capacity_weight"],
            capacity_volume=v["capacity_volume"],
            operating_cost=v["operating_cost"],
        )
        db.add(db_vehicle)
        vehicles_created += 1

    # Commit everything in one transaction
    db.commit()

    # Also export to JSON files for inspection / sharing with the team
    generator.export_to_json(raw_shipments, raw_vehicles)

    return {
        "message": "Database seeded successfully.",
        "mode": mode,
        "shipments_created": shipments_created,
        "vehicles_created": vehicles_created,
        "note": "JSON files also saved to data/synthetic/",
    }