"""
Compatibility Scoring Tool — LangGraph tool node for the Reason phase.

Wraps the scikit-learn compatibility model to score all shipment pairs
and build a compatibility graph. The graph tells the solver which
shipments CAN share a truck based on ML-predicted feasibility.

Workflow:
1. Load the trained model from disk (or train if first run)
2. Score all unique shipment pairs → P(compatible) for each
3. Build a networkx graph where edges = pairs above the threshold
4. Return the graph, edges ranked by score, and summary stats

The tool handles model lifecycle (load/train) so the pipeline node
doesn't need to worry about it. If the model fails for any reason,
it returns an empty graph — the solver can still run, just without
pair constraints.
"""

from typing import List, Dict, Optional
from backend.app.ml.compatibility_model import CompatibilityModel
from backend.app.optimizer.compatibility import filter_compatibility_graph


# Module-level model instance — loaded once, reused across requests.
# This avoids reloading the model from disk on every optimization run.
_model_instance: Optional[CompatibilityModel] = None


def _get_model() -> CompatibilityModel:
    """
    Get or create the singleton model instance.

    On first call, initializes the CompatibilityModel (which tries
    to load from disk). On subsequent calls, returns the same instance.
    This keeps the model in memory between optimization runs.
    """
    global _model_instance
    if _model_instance is None:
        _model_instance = CompatibilityModel()
    return _model_instance


def score_shipment_pairs(
    shipments: List[Dict],
    vehicles: List[Dict] = None,
    threshold: float = 0.6,
    force_retrain: bool = False,
) -> Dict:
    """
    Score all shipment pairs and build the compatibility graph.

    This is the main function called by the LangGraph pipeline node.
    It handles the full workflow: ensure model is trained, score pairs,
    build graph, and package results.

    Args:
        shipments: List of shipment dicts from AgentState
        vehicles: List of vehicle dicts, needed for capacity-based edge filtering.
                  If None, capacity filter is skipped.
        threshold: Minimum P(compatible) to create a graph edge.
                   Higher = stricter pairing, fewer edges.
                   Lower = more permissive, more consolidation options.
        force_retrain: Force model retraining even if a saved model exists.
                       Useful after the retraining hook accumulates new outcomes.

    Returns:
        Dict with:
        - stats: summary metrics about the graph (pairs scored, compatibility rate, etc.)
        - edges: list of compatible pairs ranked by score descending
        - graph_object: networkx Graph for the solver and guardrail
        - model_info: which model type was used and its training metrics
    """
    model = _get_model()

    # Ensure the model is trained before scoring.
    # First run: trains from synthetic data and saves to disk (~2-3 seconds).
    # Subsequent runs: loads from disk instantly.
    if not model.is_trained or force_retrain:
        training_result = model.train(force_retrain=force_retrain)
        model_info = {
            "status": training_result.get("status"),
            "model_type": training_result.get("model_type"),
            "best_f1": training_result.get("best_f1"),
        }
    else:
        model_info = {
            "status": "loaded_from_disk",
            "model_type": model.model_type,
            "best_f1": None,  # Not available when loaded from disk
        }

    # Handle edge case: fewer than 2 shipments means no pairs to score
    if len(shipments) < 2:
        print(f"[Compatibility Tool] Only {len(shipments)} shipment(s) — no pairs to score")
        return {
            "stats": {
                "total_shipments": len(shipments),
                "total_pairs_scored": 0,
                "compatible_pairs": 0,
                "compatibility_rate": 0,
                "threshold_used": threshold,
                "avg_connections_per_shipment": 0,
                "connected_components": len(shipments),
                "largest_component_size": 1 if shipments else 0,
            },
            "edges": [],
            "graph_object": None,
            "model_info": model_info,
        }

    # Score all pairs and build the initial graph
    graph_result = model.build_compatibility_graph(shipments, threshold=threshold)

    # Apply hard rule-based filters on top of ML scores.
    # The ML model catches most incompatibilities but these filters
    # enforce strict operational rules (detour limits, capacity, etc.)
    # If vehicles is None, skip capacity filtering by using effectively
    # unbounded capacities for the filter pass.
    vehicles_for_filter = vehicles
    if vehicles_for_filter is None:
        vehicles_for_filter = [{"capacity_weight": float("inf"), "capacity_volume": float("inf")}]

    filter_result = filter_compatibility_graph(
        graph=graph_result["graph"],
        shipments=shipments,
        vehicles=vehicles_for_filter,
    )

    # Merge stats from ML scoring and filtering
    combined_stats = {
        **graph_result["stats"],
        "edges_after_filter": filter_result["surviving_edge_count"],
        "edges_removed_by_filter": sum(filter_result["removed_counts"].values()),
        "filter_removal_reasons": filter_result["removed_counts"],
    }

    return {
        "stats": combined_stats,
        "edges": filter_result["edges"],
        "graph_object": filter_result["graph"],
        "model_info": model_info,
    }


def retrain_model() -> Dict:
    """
    Force retrain the compatibility model.

    Called by the retraining hook in the Learn phase after N optimization
    outcomes have been logged. This allows the model to improve over time
    based on which consolidations actually worked.

    Returns:
        Training result dict with model type, F1 score, etc.
    """
    model = _get_model()
    return model.train(force_retrain=True)