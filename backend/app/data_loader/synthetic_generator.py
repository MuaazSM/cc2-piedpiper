"""
Synthetic data generator for Indian freight lanes.

Generates realistic shipment and vehicle data for demos, testing,
and scenario simulation. Uses real Indian city pairs with approximate
distances, realistic weight/volume ranges, and time windows that
make sense for domestic freight.

Two modes:
- normal: standard shipment distribution for everyday testing
- surge: 1.5x volume, heavier loads, tighter windows — simulates peak demand

Usage:
    from backend.app.data_loader.synthetic_generator import SyntheticGenerator
    gen = SyntheticGenerator()
    shipments = gen.generate_shipments(count=20, mode="normal")
    vehicles = gen.generate_vehicles(count=10)
"""

import random
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional


# ---------------------------------------------------------------------------
# City data and distance matrix
# ---------------------------------------------------------------------------

# Major Indian logistics hubs. These are the most common freight lane
# endpoints in domestic trucking — chosen for realism in demos.
CITIES = [
    "Mumbai", "Pune", "Delhi", "Bangalore", "Chennai",
    "Hyderabad", "Ahmedabad", "Kolkata", "Jaipur",
]

# Approximate road distances (in km) between major Indian cities.
# Used for delivery time estimation and later for carbon/detour calculations.
# Format: (city_a, city_b): distance_km
# These are one-way — the lookup function checks both directions.
DISTANCE_MATRIX = {
    ("Mumbai", "Pune"): 150,
    ("Mumbai", "Delhi"): 1400,
    ("Mumbai", "Bangalore"): 980,
    ("Mumbai", "Chennai"): 1330,
    ("Mumbai", "Hyderabad"): 710,
    ("Mumbai", "Ahmedabad"): 530,
    ("Mumbai", "Kolkata"): 2050,
    ("Mumbai", "Jaipur"): 1150,
    ("Pune", "Delhi"): 1450,
    ("Pune", "Bangalore"): 840,
    ("Pune", "Chennai"): 1180,
    ("Pune", "Hyderabad"): 560,
    ("Pune", "Ahmedabad"): 670,
    ("Pune", "Kolkata"): 1900,
    ("Pune", "Jaipur"): 1300,
    ("Delhi", "Bangalore"): 2150,
    ("Delhi", "Chennai"): 2200,
    ("Delhi", "Hyderabad"): 1500,
    ("Delhi", "Ahmedabad"): 940,
    ("Delhi", "Kolkata"): 1530,
    ("Delhi", "Jaipur"): 280,
    ("Bangalore", "Chennai"): 350,
    ("Bangalore", "Hyderabad"): 570,
    ("Bangalore", "Ahmedabad"): 1500,
    ("Bangalore", "Kolkata"): 1870,
    ("Bangalore", "Jaipur"): 2100,
    ("Chennai", "Hyderabad"): 630,
    ("Chennai", "Ahmedabad"): 1850,
    ("Chennai", "Kolkata"): 1670,
    ("Chennai", "Jaipur"): 2200,
    ("Hyderabad", "Ahmedabad"): 1200,
    ("Hyderabad", "Kolkata"): 1500,
    ("Hyderabad", "Jaipur"): 1400,
    ("Ahmedabad", "Kolkata"): 2100,
    ("Ahmedabad", "Jaipur"): 670,
    ("Kolkata", "Jaipur"): 1800,
}


def get_distance(city_a: str, city_b: str) -> int:
    """
    Look up the road distance between two cities.
    Checks both (A, B) and (B, A) since the matrix only stores one direction.
    Returns a default of 500 km if the pair isn't in the matrix (shouldn't happen
    with our city list, but safe fallback).
    """
    if city_a == city_b:
        return 0
    return DISTANCE_MATRIX.get(
        (city_a, city_b),
        DISTANCE_MATRIX.get((city_b, city_a), 500)
    )


# ---------------------------------------------------------------------------
# Vehicle templates
# ---------------------------------------------------------------------------

# Realistic Indian freight vehicle types with their specs.
# The generator picks from these based on a weighted distribution.
VEHICLE_TEMPLATES = [
    {
        "vehicle_type": "small_tempo",
        "capacity_weight": 2000.0,      # 2 tonnes — Tata Ace / Mahindra Bolero pickup
        "capacity_volume": 8.0,          # ~8 cubic meters
        "operating_cost": 3000.0,        # INR per trip (local/short haul)
    },
    {
        "vehicle_type": "medium_truck",
        "capacity_weight": 7000.0,       # 7 tonnes — Eicher / Tata 407
        "capacity_volume": 25.0,         # ~25 cubic meters
        "operating_cost": 8000.0,        # INR per trip (regional)
    },
    {
        "vehicle_type": "large_trailer",
        "capacity_weight": 15000.0,      # 15 tonnes — Tata LPT / Ashok Leyland
        "capacity_volume": 50.0,         # ~50 cubic meters
        "operating_cost": 15000.0,       # INR per trip (long haul)
    },
    {
        "vehicle_type": "refrigerated",
        "capacity_weight": 5000.0,       # 5 tonnes — reefer truck
        "capacity_volume": 18.0,         # ~18 cubic meters (insulation eats space)
        "operating_cost": 12000.0,       # Higher cost due to cooling equipment
    },
]

# How often each vehicle type appears in a generated fleet.
# More medium trucks than anything else — matches real Indian fleet composition.
VEHICLE_TYPE_WEIGHTS = [0.20, 0.40, 0.25, 0.15]


# ---------------------------------------------------------------------------
# Special handling and priority distributions
# ---------------------------------------------------------------------------

# Most shipments have no special handling. When they do, these are
# the common categories in Indian freight.
SPECIAL_HANDLING_OPTIONS = [
    None, None, None, None, None, None,   # ~60% chance of no special handling
    "fragile",                             # Glass, electronics, ceramics
    "refrigerated",                        # Pharma, dairy, frozen food
    "hazardous",                           # Chemicals, flammable goods
    "oversized",                           # Machinery, large equipment
]

# Priority distribution: most freight is routine (MEDIUM), some is urgent (HIGH),
# and a smaller chunk is low-priority (can wait for consolidation).
PRIORITY_OPTIONS = ["MEDIUM"] * 12 + ["HIGH"] * 5 + ["LOW"] * 3  # ~60/25/15 split


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class SyntheticGenerator:
    """
    Generates synthetic shipment and vehicle data for the Lorri system.

    The generator uses randomization with realistic constraints so that
    the generated data makes sense for Indian domestic freight:
    - City pairs are real routes
    - Delivery times scale with distance
    - Weight and volume are correlated (not random junk)
    - Vehicle capacities match common Indian truck types
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the generator with an optional random seed.
        Setting a seed makes output reproducible — useful for consistent demos.
        """
        if seed is not None:
            random.seed(seed)

    def _generate_time_windows(self, distance_km: int, mode: str) -> tuple:
        """
        Generate realistic pickup and delivery time windows based on distance.

        Logic:
        - Pickup happens 1-3 days from now (simulates advance booking)
        - Delivery window is based on distance: ~60 km/h average truck speed
          plus a buffer for loading, unloading, rest stops, etc.
        - Surge mode tightens windows by 20% to simulate pressure

        Returns (pickup_time, delivery_time) as datetime objects.
        """
        now = datetime.now()

        # Pickup is 1 to 3 days from now
        pickup_offset_hours = random.uniform(24, 72)
        pickup_time = now + timedelta(hours=pickup_offset_hours)

        # Estimate transit time: average 60 km/h for trucks on Indian highways,
        # plus 2-6 hours buffer for loading/unloading/rest
        transit_hours = (distance_km / 60.0) + random.uniform(2, 6)

        # In surge mode, reduce the delivery buffer by 20% (tighter deadlines)
        if mode == "surge":
            transit_hours *= 0.8

        delivery_time = pickup_time + timedelta(hours=transit_hours)

        return pickup_time, delivery_time

    def _generate_weight_volume(self, mode: str) -> tuple:
        """
        Generate correlated weight and volume for a shipment.

        Weight range: 100-5000 kg (normal), 500-7000 kg (surge — heavier loads).
        Volume is derived from weight using a density factor with random noise,
        so they're correlated but not perfectly predictable. This is more realistic
        than generating them independently.
        """
        if mode == "surge":
            weight = round(random.uniform(500, 7000), 1)
        else:
            weight = round(random.uniform(100, 5000), 1)

        # Density factor: kg per cubic meter. Real freight varies a lot —
        # feathers vs. steel. We use 150-400 kg/m³ as a reasonable range.
        density = random.uniform(150, 400)
        volume = round(weight / density, 2)

        return weight, volume

    def generate_shipments(self, count: int = 20, mode: str = "normal") -> List[Dict]:
        """
        Generate a list of synthetic shipments.

        Args:
            count: Number of shipments to generate. In surge mode, this gets
                   multiplied by 1.5 (rounded up) to simulate demand spike.
            mode: "normal" for standard distribution, "surge" for peak demand.

        Returns:
            List of dicts matching the ShipmentCreate schema, ready for
            direct insertion into the DB or JSON export.
        """
        # Surge mode increases the shipment count to simulate demand spikes
        if mode == "surge":
            count = int(count * 1.5)

        shipments = []
        for i in range(count):
            # Pick a random origin-destination pair (no same-city shipments)
            origin = random.choice(CITIES)
            destination = random.choice([c for c in CITIES if c != origin])

            distance_km = get_distance(origin, destination)
            pickup_time, delivery_time = self._generate_time_windows(distance_km, mode)
            weight, volume = self._generate_weight_volume(mode)

            shipment = {
                "shipment_id": f"SH-{i + 1:04d}",
                "origin": origin,
                "destination": destination,
                "pickup_time": pickup_time.isoformat(),
                "delivery_time": delivery_time.isoformat(),
                "weight": weight,
                "volume": volume,
                "priority": random.choice(PRIORITY_OPTIONS),
                "special_handling": random.choice(SPECIAL_HANDLING_OPTIONS),
                "status": "PENDING",
            }
            shipments.append(shipment)

        return shipments

    def generate_vehicles(self, count: int = 10) -> List[Dict]:
        """
        Generate a fleet of vehicles with realistic type distribution.

        Uses weighted random selection so the fleet composition matches
        real Indian logistics — mostly medium trucks, fewer specialized vehicles.

        Args:
            count: Number of vehicles to generate.

        Returns:
            List of dicts matching the VehicleCreate schema.
        """
        vehicles = []
        for i in range(count):
            # Pick a vehicle template based on the weighted distribution
            template = random.choices(VEHICLE_TEMPLATES, weights=VEHICLE_TYPE_WEIGHTS, k=1)[0]

            # Add slight variation to capacity and cost so not every truck
            # of the same type is identical (reflects real fleet diversity)
            weight_variation = random.uniform(0.9, 1.1)
            volume_variation = random.uniform(0.9, 1.1)
            cost_variation = random.uniform(0.85, 1.15)

            vehicle = {
                "vehicle_id": f"VH-{i + 1:04d}",
                "vehicle_type": template["vehicle_type"],
                "capacity_weight": round(template["capacity_weight"] * weight_variation, 1),
                "capacity_volume": round(template["capacity_volume"] * volume_variation, 1),
                "operating_cost": round(template["operating_cost"] * cost_variation, 1),
            }
            vehicles.append(vehicle)

        return vehicles

    def export_to_json(
        self,
        shipments: List[Dict],
        vehicles: List[Dict],
        output_dir: str = "data/synthetic",
    ) -> Dict[str, str]:
        """
        Dump generated data to JSON files for inspection or sharing.

        Creates two files in the output directory:
        - shipments.json: all generated shipments
        - vehicles.json: all generated vehicles

        Returns a dict with the file paths for confirmation.
        """
        os.makedirs(output_dir, exist_ok=True)

        shipments_path = os.path.join(output_dir, "shipments.json")
        vehicles_path = os.path.join(output_dir, "vehicles.json")

        with open(shipments_path, "w") as f:
            json.dump(shipments, f, indent=2, default=str)

        with open(vehicles_path, "w") as f:
            json.dump(vehicles, f, indent=2, default=str)

        return {
            "shipments_file": shipments_path,
            "vehicles_file": vehicles_path,
        }

    def get_distance_matrix(self) -> Dict:
        """
        Returns the full distance matrix for use by the solver and carbon calculator.
        Converts the tuple-keyed dict to a JSON-friendly string-keyed format.
        """
        return {
            f"{a}-{b}": dist
            for (a, b), dist in DISTANCE_MATRIX.items()
        }