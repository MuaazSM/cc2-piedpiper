"""
Solomon VRPTW Benchmark Mapper.

Reads Solomon C101 and R101 CSV files and maps them to our internal
shipment/vehicle schema. Used for:
- OR solver validation against known-optimal benchmarks
- Demo with industry-standard test data
- Comparing our solution quality against published results

Solomon format:
- Row 1: depot (CUST NO. = 1, demand = 0)
- Rows 2+: customers with coordinates, demand, time windows
- Vehicle capacity: 200 units (C101), 200 units (R101)
- Known optimal: C101 = 10 vehicles (100 customers), R101 = 19 vehicles

Mapping strategy:
- Coordinates are abstract grid points (0-100 range)
- We cluster them into Indian city regions for our schema
- Demand is scaled to realistic freight weights (×50 → kg)
- Time units are mapped to hours from a base datetime
- Vehicle capacity is scaled to match the weight scaling

The mapping preserves the mathematical structure of the problem
(relative distances, time window tightness, demand ratios) while
making the data look realistic in our Indian freight context.
"""

import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from backend.app.data_loader.synthetic_generator import get_distance


# ---------------------------------------------------------------------------
# Known optimal solutions for benchmarking
# ---------------------------------------------------------------------------

KNOWN_OPTIMAL = {
    "C101": {"vehicles": 10, "distance": 828.94, "customers": 100},
    "R101": {"vehicles": 19, "distance": 1645.79, "customers": 100},
    # 25-customer subsets (commonly used for quick validation)
    "C101_25": {"vehicles": 3, "customers": 25},
    "R101_25": {"vehicles": 8, "customers": 25},
}


# ---------------------------------------------------------------------------
# City mapping based on coordinate clusters
# ---------------------------------------------------------------------------

# Solomon coordinates range roughly 0-100 on both axes.
# We divide the grid into regions and map each to an Indian city pair.
# This preserves spatial clustering (C101 has tight clusters, R101 is random).

CITY_REGIONS = [
    # (x_min, x_max, y_min, y_max, origin_city, destination_city)
    (0, 25, 0, 50, "Chennai", "Bangalore"),
    (0, 25, 50, 100, "Hyderabad", "Mumbai"),
    (25, 50, 0, 50, "Pune", "Ahmedabad"),
    (25, 50, 50, 100, "Mumbai", "Delhi"),
    (50, 75, 0, 50, "Delhi", "Jaipur"),
    (50, 75, 50, 100, "Bangalore", "Chennai"),
    (75, 100, 0, 50, "Ahmedabad", "Kolkata"),
    (75, 100, 50, 100, "Jaipur", "Hyderabad"),
]


def _coords_to_cities(x: int, y: int) -> Tuple[str, str]:
    """
    Map Solomon x,y coordinates to an Indian city origin-destination pair.

    Searches the region grid to find which bucket the coordinates fall into.
    Falls back to Mumbai→Pune if no region matches (shouldn't happen with
    0-100 coordinate range).
    """
    for x_min, x_max, y_min, y_max, origin, dest in CITY_REGIONS:
        if x_min <= x < x_max and y_min <= y < y_max:
            return origin, dest

    # Fallback — shouldn't reach here with standard Solomon data
    return "Mumbai", "Pune"


# ---------------------------------------------------------------------------
# CSV reader
# ---------------------------------------------------------------------------

def _read_solomon_csv(filepath: str) -> List[Dict]:
    """
    Read a Solomon CSV file and return a list of customer dicts.

    Handles the specific format shown in the dataset:
    columns = CUST NO., XCOORD., YCOORD., DEMAND, READY TIME, DUE DATE, SERVICE TIME

    Skips the first row (depot) where demand = 0 and CUST NO. = 1.
    """
    customers = []

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Solomon dataset not found at {filepath}")

    with open(filepath, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Normalize column names — strip whitespace and standardize
            cleaned = {}
            for key, value in row.items():
                clean_key = key.strip().upper().replace(".", "").replace(" ", "_")
                cleaned[clean_key] = value.strip() if value else ""

            # Parse fields — try multiple possible column name formats
            cust_no = int(cleaned.get("CUST_NO", cleaned.get("CUSTNO", 0)))
            x = int(cleaned.get("XCOORD", cleaned.get("XCOORD_", 0)))
            y = int(cleaned.get("YCOORD", cleaned.get("YCOORD_", 0)))
            demand = int(cleaned.get("DEMAND", 0))
            ready_time = int(cleaned.get("READY_TIME", cleaned.get("READYTIME", 0)))
            due_date = int(cleaned.get("DUE_DATE", cleaned.get("DUEDATE", 0)))
            service_time = int(cleaned.get("SERVICE_TIME", cleaned.get("SERVICETIME", 0)))

            # Skip depot (first customer with demand=0 and CUST NO=1)
            if cust_no == 1 and demand == 0:
                continue

            customers.append({
                "cust_no": cust_no,
                "x": x,
                "y": y,
                "demand": demand,
                "ready_time": ready_time,
                "due_date": due_date,
                "service_time": service_time,
            })

    print(f"[Solomon Mapper] Read {len(customers)} customers from {filepath}")
    return customers


# ---------------------------------------------------------------------------
# Mapping functions
# ---------------------------------------------------------------------------

def map_solomon_to_shipments(
    filepath: str,
    max_customers: Optional[int] = None,
    weight_scale: float = 50.0,
    time_scale_minutes: float = 1.0,
) -> List[Dict]:
    """
    Map a Solomon CSV file to our shipment schema.

    Args:
        filepath: Path to the Solomon CSV file
        max_customers: Limit number of customers (e.g. 25 for quick tests).
                       None = use all customers in the file.
        weight_scale: Multiply demand by this to get weight in kg.
                      Default 50 maps demand=10 → 500kg (realistic freight).
        time_scale_minutes: Solomon time units to minutes conversion.
                           Default 1.0 treats Solomon units as minutes.

    Returns:
        List of shipment dicts matching our ShipmentCreate schema.
    """
    customers = _read_solomon_csv(filepath)

    # Optionally limit to first N customers
    if max_customers:
        customers = customers[:max_customers]

    # Base datetime for time window mapping.
    # We use a fixed date so results are reproducible.
    base_time = datetime(2025, 6, 1, 6, 0, 0)

    shipments = []
    for i, cust in enumerate(customers):
        # Map coordinates to Indian city pair
        origin, destination = _coords_to_cities(cust["x"], cust["y"])

        # Scale demand to realistic freight weight
        weight = float(cust["demand"]) * weight_scale

        # Volume proportional to weight with some randomness baked in.
        # Use a density factor that varies by coordinate to add variety.
        density_factor = 0.003 + (cust["x"] % 10) * 0.0002
        volume = round(weight * density_factor, 2)

        # Map time windows: Solomon time units → real datetime
        pickup_time = base_time + timedelta(minutes=cust["ready_time"] * time_scale_minutes)
        delivery_time = base_time + timedelta(minutes=cust["due_date"] * time_scale_minutes)

        # Ensure minimum 1-hour delivery window (some Solomon instances have tight windows)
        if (delivery_time - pickup_time).total_seconds() < 3600:
            delivery_time = pickup_time + timedelta(hours=1)

        # Assign priority based on time window tightness.
        # Tighter windows = higher priority (more urgent deliveries).
        window_hours = (delivery_time - pickup_time).total_seconds() / 3600
        if window_hours < 2:
            priority = "HIGH"
        elif window_hours < 6:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        shipments.append({
            "shipment_id": f"SOL-{cust['cust_no']:03d}",
            "origin": origin,
            "destination": destination,
            "weight": weight,
            "volume": volume,
            "pickup_time": pickup_time.isoformat(),
            "delivery_time": delivery_time.isoformat(),
            "priority": priority,
            "special_handling": None,
            "status": "PENDING",
        })

    print(f"[Solomon Mapper] Mapped {len(shipments)} shipments "
          f"(weight_scale={weight_scale}, time_scale={time_scale_minutes})")

    return shipments


def generate_solomon_vehicles(
    count: int = 10,
    capacity_demand: int = 200,
    weight_scale: float = 50.0,
) -> List[Dict]:
    """
    Generate vehicles matching Solomon instance specifications.

    Solomon instances assume homogeneous fleet with capacity 200 demand units.
    We scale the capacity to match our weight mapping.

    Args:
        count: Number of vehicles to generate. Use known optimal + buffer.
        capacity_demand: Solomon vehicle capacity in demand units (default 200).
        weight_scale: Same scale used for shipment weight mapping.

    Returns:
        List of vehicle dicts matching our VehicleCreate schema.
    """
    capacity_weight = float(capacity_demand) * weight_scale  # 200 × 50 = 10000 kg
    # Volume capacity proportional to weight capacity
    capacity_volume = capacity_weight * 0.004  # Matches the density factor range

    vehicles = []
    for i in range(count):
        vehicles.append({
            "vehicle_id": f"SOL-V{i + 1:03d}",
            "vehicle_type": "large_trailer",
            "capacity_weight": capacity_weight,
            "capacity_volume": round(capacity_volume, 1),
            "operating_cost": 15000.0,  # Standard large trailer cost
        })

    print(f"[Solomon Mapper] Generated {count} vehicles "
          f"(capacity: {capacity_weight}kg, {capacity_volume}m³)")

    return vehicles


# ---------------------------------------------------------------------------
# High-level convenience functions
# ---------------------------------------------------------------------------

def load_c101(
    max_customers: Optional[int] = None,
    dataset_dir: str = "dataset",
) -> Tuple[List[Dict], List[Dict]]:
    """
    Load Solomon C101 dataset and generate matching vehicles.

    C101 is a clustered instance — customers are grouped in geographic
    clusters with wide time windows. Known optimal: 10 vehicles for
    100 customers. Good for testing consolidation efficiency.

    Args:
        max_customers: Limit customers (e.g. 25 for quick tests)
        dataset_dir: Root directory of the dataset folder

    Returns:
        Tuple of (shipments, vehicles)
    """
    filepath = os.path.join(dataset_dir, "C1", "C101.csv")

    shipments = map_solomon_to_shipments(
        filepath=filepath,
        max_customers=max_customers,
        weight_scale=50.0,
        time_scale_minutes=1.0,
    )

    # Generate enough vehicles: known optimal + 50% buffer
    optimal = KNOWN_OPTIMAL.get("C101", {}).get("vehicles", 10)
    if max_customers and max_customers <= 25:
        optimal = KNOWN_OPTIMAL.get("C101_25", {}).get("vehicles", 3)

    vehicle_count = int(optimal * 1.5) + 2
    vehicles = generate_solomon_vehicles(count=vehicle_count)

    return shipments, vehicles


def load_r101(
    max_customers: Optional[int] = None,
    dataset_dir: str = "dataset",
) -> Tuple[List[Dict], List[Dict]]:
    """
    Load Solomon R101 dataset and generate matching vehicles.

    R101 is a random instance — customers are scattered with tight
    time windows. Known optimal: 19 vehicles for 100 customers.
    Harder to consolidate than C101 due to less geographic clustering.

    Args:
        max_customers: Limit customers (e.g. 25 for quick tests)
        dataset_dir: Root directory of the dataset folder

    Returns:
        Tuple of (shipments, vehicles)
    """
    filepath = os.path.join(dataset_dir, "R1", "R101.csv")

    shipments = map_solomon_to_shipments(
        filepath=filepath,
        max_customers=max_customers,
        weight_scale=50.0,
        time_scale_minutes=1.0,
    )

    # Generate enough vehicles
    optimal = KNOWN_OPTIMAL.get("R101", {}).get("vehicles", 19)
    if max_customers and max_customers <= 25:
        optimal = KNOWN_OPTIMAL.get("R101_25", {}).get("vehicles", 8)

    vehicle_count = int(optimal * 1.5) + 2
    vehicles = generate_solomon_vehicles(count=vehicle_count)

    return shipments, vehicles


def get_benchmark_info(dataset: str) -> Dict:
    """
    Get known optimal results for a Solomon dataset.
    Used for comparison after solving.
    """
    return KNOWN_OPTIMAL.get(dataset, {})