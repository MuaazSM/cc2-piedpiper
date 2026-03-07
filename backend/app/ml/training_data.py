import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from backend.app.data_loader.synthetic_generator import (
    SyntheticGenerator,
    get_distance,
    CITIES,
)


# These pairs of handling types should NEVER share a truck.
# Used as hard negatives in labeling.
HANDLING_CONFLICTS = {
    frozenset({"hazardous", "fragile"}),
    frozenset({"hazardous", "refrigerated"}),
    frozenset({"hazardous", "oversized"}),
}


# Feature extraction

def extract_features(shipment_a: Dict, shipment_b: Dict) -> Dict:
    """
    Compute pairwise features for two shipments.

    These features capture every dimension that matters for consolidation:
    - Geography: are they going the same way?
    - Timing: can they share a truck without delaying either?
    - Physical: do they fit together in one vehicle?
    - Compatibility: do their handling requirements conflict?

    Returns a flat dict of feature name → value, ready for DataFrame conversion.
    """
    origin_a = shipment_a.get("origin", "")
    origin_b = shipment_b.get("origin", "")
    dest_a = shipment_a.get("destination", "")
    dest_b = shipment_b.get("destination", "")

    #  Geographic features 
    # Same lane is the strongest consolidation signal — both shipments
    # are going from the exact same origin to the exact same destination.
    same_lane = 1 if (origin_a == origin_b and dest_a == dest_b) else 0
    same_origin = 1 if origin_a == origin_b else 0
    same_destination = 1 if dest_a == dest_b else 0

    # Distance between the two origins and destinations.
    # Close origins mean pickup consolidation is feasible.
    # Close destinations mean delivery consolidation is feasible.
    origin_distance_km = get_distance(origin_a, origin_b) if origin_a != origin_b else 0
    dest_distance_km = get_distance(dest_a, dest_b) if dest_a != dest_b else 0

    #  Time window features 
    # Calculate what percentage of the two shipments' time windows overlap.
    # Higher overlap = easier to schedule on the same truck.
    pickup_a = _parse_time(shipment_a.get("pickup_time"))
    pickup_b = _parse_time(shipment_b.get("pickup_time"))
    delivery_a = _parse_time(shipment_a.get("delivery_time"))
    delivery_b = _parse_time(shipment_b.get("delivery_time"))

    time_overlap_pct = 0.0
    if all([pickup_a, pickup_b, delivery_a, delivery_b]):
        time_overlap_pct = _compute_time_overlap(pickup_a, delivery_a, pickup_b, delivery_b)

    #  Physical dimension features 
    weight_a = shipment_a.get("weight", 0)
    weight_b = shipment_b.get("weight", 0)
    volume_a = shipment_a.get("volume", 0)
    volume_b = shipment_b.get("volume", 0)

    # Weight and volume ratios — closer to 1.0 means similar-sized shipments,
    # which generally pack better together.
    weight_ratio = min(weight_a, weight_b) / max(weight_a, weight_b) if max(weight_a, weight_b) > 0 else 0
    volume_ratio = min(volume_a, volume_b) / max(volume_a, volume_b) if max(volume_a, volume_b) > 0 else 0

    # Combined weight and volume — the solver needs these to fit within
    # a single vehicle's capacity.
    combined_weight = weight_a + weight_b
    combined_volume = volume_a + volume_b

    #  Priority features 
    priority_a = shipment_a.get("priority", "MEDIUM")
    priority_b = shipment_b.get("priority", "MEDIUM")

    # Same priority = no scheduling tension between the two
    priority_match = 1 if priority_a == priority_b else 0

    # HIGH + LOW on the same truck creates tension — the LOW shipment's
    # stops may delay the HIGH priority delivery.
    priority_conflict = 1 if (
        {priority_a, priority_b} == {"HIGH", "LOW"}
    ) else 0

    #  Special handling features 
    handling_a = shipment_a.get("special_handling") or "none"
    handling_b = shipment_b.get("special_handling") or "none"

    # Hard conflict: these two handling types cannot share a vehicle
    handling_pair = frozenset({handling_a, handling_b}) - {"none"}
    handling_conflict = 1 if handling_pair in HANDLING_CONFLICTS else 0

    # At least one shipment is hazardous — restricts co-loading options
    either_hazardous = 1 if "hazardous" in {handling_a, handling_b} else 0

    return {
        "same_lane": same_lane,
        "same_origin": same_origin,
        "same_destination": same_destination,
        "origin_distance_km": origin_distance_km,
        "dest_distance_km": dest_distance_km,
        "time_overlap_pct": round(time_overlap_pct, 4),
        "weight_ratio": round(weight_ratio, 4),
        "volume_ratio": round(volume_ratio, 4),
        "combined_weight": round(combined_weight, 1),
        "combined_volume": round(combined_volume, 2),
        "priority_match": priority_match,
        "priority_conflict": priority_conflict,
        "handling_conflict": handling_conflict,
        "either_hazardous": either_hazardous,
    }


def _compute_time_overlap(
    start_a: datetime, end_a: datetime,
    start_b: datetime, end_b: datetime,
) -> float:
    """
    Calculate the percentage of time window overlap between two shipments.

    Returns a value between 0.0 (no overlap) and 1.0 (complete overlap).
    The overlap is expressed as a fraction of the shorter window,
    so a small shipment fully inside a large shipment's window = 1.0.
    """
    # Find the overlap interval
    overlap_start = max(start_a, start_b)
    overlap_end = min(end_a, end_b)

    if overlap_start >= overlap_end:
        return 0.0  # No overlap at all

    overlap_seconds = (overlap_end - overlap_start).total_seconds()

    # Normalize by the shorter window so the metric is symmetric
    window_a = (end_a - start_a).total_seconds()
    window_b = (end_b - start_b).total_seconds()
    shorter_window = min(window_a, window_b)

    if shorter_window <= 0:
        return 0.0

    return min(overlap_seconds / shorter_window, 1.0)


def _parse_time(value) -> datetime:
    """
    Safely parse a datetime from string or return as-is if already datetime.
    Returns None on failure so callers can handle gracefully.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


# Labeling function

def label_pair(features: Dict, noise_rate: float = 0.07) -> int:
    """
    Assign a binary compatibility label to a shipment pair based on domain rules.

    The labeling logic encodes what freight logistics experts know:
    - Some constraints are hard (handling conflicts = always incompatible)
    - Some are soft (time overlap, route similarity = scored and thresholded)

    We add random noise (default 7%) to prevent the ML model from
    memorizing the exact rule boundaries. This forces it to learn
    smoother, more generalizable decision surfaces.

    Args:
        features: Dict of pairwise features from extract_features()
        noise_rate: Probability of flipping the label (0.0 to 1.0)

    Returns:
        1 (compatible) or 0 (incompatible)
    """
    #  Hard constraints: instant rejection 
    # Handling conflicts are non-negotiable safety rules
    if features["handling_conflict"] == 1:
        label = 0
        # Still apply noise — a small chance of "compatible despite conflict"
        # teaches the model that the boundary isn't perfectly sharp
        if random.random() < noise_rate:
            label = 1
        return label

    # Zero time overlap means the shipments can't possibly share a truck
    if features["time_overlap_pct"] == 0:
        label = 0
        if random.random() < noise_rate:
            label = 1
        return label

    #  Soft scoring: weighted combination of positive signals 
    score = 0.0

    # Same lane is the strongest signal — direct consolidation opportunity
    if features["same_lane"] == 1:
        score += 0.35
    elif features["same_origin"] == 1:
        score += 0.15
    elif features["same_destination"] == 1:
        score += 0.10

    # Close origins/destinations boost consolidation feasibility.
    # We normalize distance: 0km → full score, >1000km → zero score
    if features["origin_distance_km"] < 300:
        score += 0.10 * (1 - features["origin_distance_km"] / 300)
    if features["dest_distance_km"] < 300:
        score += 0.10 * (1 - features["dest_distance_km"] / 300)

    # Time overlap is crucial — more overlap = easier scheduling
    score += 0.25 * features["time_overlap_pct"]

    # Similar-sized shipments pack better together
    score += 0.05 * features["weight_ratio"]
    score += 0.05 * features["volume_ratio"]

    # Priority alignment reduces scheduling tension
    if features["priority_match"] == 1:
        score += 0.05

    # Priority conflict is a soft negative — not impossible but risky
    if features["priority_conflict"] == 1:
        score -= 0.15

    # Hazardous materials restrict options even without a direct conflict
    if features["either_hazardous"] == 1:
        score -= 0.05

    # Threshold: pairs scoring above 0.35 are labeled compatible.
    # This threshold was tuned to give roughly 40-50% positive rate,
    # which is realistic (not every pair can consolidate).
    label = 1 if score >= 0.35 else 0

    # Apply noise to prevent overfitting to exact rule boundaries
    if random.random() < noise_rate:
        label = 1 - label  # Flip the label

    return label


# Main training data generation

def generate_training_data(
    n_pairs: int = 8000,
    n_shipments: int = 200,
    noise_rate: float = 0.07,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Generate a full labeled dataset for training the compatibility model.

    Pipeline:
    1. Generate a pool of synthetic shipments
    2. Sample random pairs from the pool
    3. Extract features for each pair
    4. Label each pair using domain rules + noise

    Args:
        n_pairs: Number of shipment pairs to generate
        n_shipments: Size of the shipment pool to sample from
        noise_rate: Label noise rate (0.0 to 1.0)
        seed: Random seed for reproducibility

    Returns:
        Tuple of:
        - X: numpy array of shape (n_pairs, n_features)
        - y: numpy array of shape (n_pairs,) with binary labels
        - feature_names: list of feature name strings
    """
    random.seed(seed)
    np.random.seed(seed)

    # Step 1: Generate a pool of shipments to pair up.
    # We use more shipments than the default 20 to get diverse pairs.
    generator = SyntheticGenerator(seed=seed)
    shipments = generator.generate_shipments(count=n_shipments, mode="normal")

    # Step 2: Sample random pairs. We avoid pairing a shipment with itself
    # and limit to n_pairs to keep training time reasonable.
    pairs = []
    attempts = 0
    max_attempts = n_pairs * 3  # Safety valve to prevent infinite loops

    seen_pairs = set()
    while len(pairs) < n_pairs and attempts < max_attempts:
        i = random.randint(0, len(shipments) - 1)
        j = random.randint(0, len(shipments) - 1)
        if i == j:
            attempts += 1
            continue

        # Canonical pair key so (i,j) and (j,i) are the same pair
        pair_key = (min(i, j), max(i, j))
        if pair_key in seen_pairs:
            attempts += 1
            continue

        seen_pairs.add(pair_key)
        pairs.append((shipments[i], shipments[j]))
        attempts += 1

    # Step 3 & 4: Extract features and generate labels for each pair
    feature_dicts = []
    labels = []

    for shipment_a, shipment_b in pairs:
        features = extract_features(shipment_a, shipment_b)
        label = label_pair(features, noise_rate=noise_rate)
        feature_dicts.append(features)
        labels.append(label)

    # Convert to numpy arrays for scikit-learn
    feature_names = list(feature_dicts[0].keys())
    X = np.array([[f[name] for name in feature_names] for f in feature_dicts])
    y = np.array(labels)

    print(f"[Training Data] Generated {len(pairs)} pairs from {len(shipments)} shipments")
    print(f"[Training Data] Positive rate: {y.mean():.1%} ({y.sum()}/{len(y)})")
    print(f"[Training Data] Features: {len(feature_names)}")

    return X, y, feature_names