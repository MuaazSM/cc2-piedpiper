"""
Dev seed endpoint — populates the database with test data.

POST /dev/seed supports multiple data sources:
- synthetic (default): generated Indian city freight data
- solomon_c101: Solomon C101 clustered benchmark
- solomon_r101: Solomon R101 random benchmark

Query params:
- dataset: which data source to use
- shipment_count: how many shipments (synthetic only)
- vehicle_count: how many vehicles (synthetic only)
- max_customers: limit Solomon customers (e.g. 25 for quick tests)
- mode: "normal" or "surge" (synthetic only)
- clear: wipe existing data first (default true)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.shipment import Shipment
from backend.app.models.vehicle import Vehicle
from backend.app.data_loader.synthetic_generator import SyntheticGenerator
from backend.app.data_loader.solomon_mapper import (
    load_c101, load_r101, get_benchmark_info,
)
from datetime import datetime
from typing import Optional

router = APIRouter()


@router.post("/seed")
def seed_data(
    dataset: str = Query("synthetic", description="Data source: 'synthetic', 'solomon_c101', or 'solomon_r101'"),
    shipment_count: int = Query(20, ge=1, le=500, description="Number of shipments (synthetic only)"),
    vehicle_count: int = Query(10, ge=1, le=100, description="Number of vehicles (synthetic only)"),
    max_customers: Optional[int] = Query(None, ge=1, le=100, description="Limit Solomon customers (e.g. 25)"),
    mode: str = Query("normal", description="Generation mode: 'normal' or 'surge' (synthetic only)"),
    clear: bool = Query(True, description="Clear existing data before seeding"),
    db: Session = Depends(get_db),
):
    """
    Seed the database with shipment and vehicle data.

    Three data sources:
    - synthetic: AI-generated Indian freight data (fastest for demos)
    - solomon_c101: Clustered benchmark (validates solver quality)
    - solomon_r101: Random benchmark (stress-tests solver)

    Solomon datasets are read from dataset/C1/C101.csv and dataset/R1/R101.csv.
    Use max_customers=25 for quick tests, omit for full 100-customer instance.
    """
    # Optionally wipe existing data
    if clear:
        db.query(Shipment).delete()
        db.query(Vehicle).delete()
        db.commit()

    # --- Generate data based on selected source ---
    if dataset == "solomon_c101":
        raw_shipments, raw_vehicles = load_c101(max_customers=max_customers)
        benchmark = get_benchmark_info("C101_25" if max_customers and max_customers <= 25 else "C101")
        source_info = {
            "dataset": "Solomon C101 (Clustered)",
            "benchmark_optimal_vehicles": benchmark.get("vehicles"),
            "max_customers": max_customers or "all",
        }

    elif dataset == "solomon_r101":
        raw_shipments, raw_vehicles = load_r101(max_customers=max_customers)
        benchmark = get_benchmark_info("R101_25" if max_customers and max_customers <= 25 else "R101")
        source_info = {
            "dataset": "Solomon R101 (Random)",
            "benchmark_optimal_vehicles": benchmark.get("vehicles"),
            "max_customers": max_customers or "all",
        }

    elif dataset == "synthetic":
        generator = SyntheticGenerator()
        raw_shipments = generator.generate_shipments(count=shipment_count, mode=mode)
        raw_vehicles = generator.generate_vehicles(count=vehicle_count)
        generator.export_to_json(raw_shipments, raw_vehicles)
        source_info = {
            "dataset": "Synthetic Indian freight",
            "mode": mode,
        }

    else:
        return {
            "error": f"Unknown dataset '{dataset}'. Use 'synthetic', 'solomon_c101', or 'solomon_r101'.",
        }

    # --- Insert shipments into DB ---
    shipments_created = 0
    for s in raw_shipments:
        # Parse pickup/delivery times — handle both string and datetime
        pickup = s.get("pickup_time")
        delivery = s.get("delivery_time")
        if isinstance(pickup, str):
            pickup = datetime.fromisoformat(pickup)
        if isinstance(delivery, str):
            delivery = datetime.fromisoformat(delivery)

        db_shipment = Shipment(
            shipment_id=s["shipment_id"],
            origin=s["origin"],
            destination=s["destination"],
            pickup_time=pickup,
            delivery_time=delivery,
            weight=s["weight"],
            volume=s["volume"],
            priority=s.get("priority", "MEDIUM"),
            special_handling=s.get("special_handling"),
            status=s.get("status", "PENDING"),
        )
        db.add(db_shipment)
        shipments_created += 1

    # --- Insert vehicles into DB ---
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

    db.commit()

    return {
        "message": "Database seeded successfully.",
        "shipments_created": shipments_created,
        "vehicles_created": vehicles_created,
        **source_info,
    }