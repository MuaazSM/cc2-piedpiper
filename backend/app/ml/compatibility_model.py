import os
import joblib
import numpy as np
import networkx as nx
from typing import List, Dict, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report
from backend.app.ml.training_data import extract_features, generate_training_data


# Models are saved in a subdirectory next to this file.
# This keeps them versioned with the code and easy to find.
MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")
MODEL_PATH = os.path.join(MODEL_DIR, "compatibility_model.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")
METADATA_PATH = os.path.join(MODEL_DIR, "metadata.joblib")


class CompatibilityModel:
    """
    Shipment pair compatibility scorer.

    Wraps the full ML lifecycle: training data generation, model training,
    prediction, and compatibility graph construction. The model is persisted
    to disk after training so subsequent optimization runs can load it
    instantly without retraining.
    """

    def __init__(self):
        """
        Initialize the model. Tries to load a previously saved model
        from disk. If none exists, the model is uninitialized and
        needs to be trained before making predictions.
        """
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.model_type = None  # "RandomForest" or "LogisticRegression"
        self.is_trained = False

        # Try loading a saved model — skip training if one exists
        self._load_model()

    def train(
        self,
        n_pairs: int = 15000,
        n_shipments: int = 400,
        noise_rate: float = 0.05,
        seed: int = 42,
        force_retrain: bool = False,
    ) -> Dict:
        """
        Train the compatibility model from scratch.

        Generates synthetic training data, trains both RandomForest and
        LogisticRegression, picks the winner by F1 score, and saves
        the model to disk.

        Args:
            n_pairs: Number of training pairs to generate
            n_shipments: Shipment pool size for pair generation
            noise_rate: Label noise rate for training data
            seed: Random seed for reproducibility
            force_retrain: If True, retrain even if a saved model exists

        Returns:
            Dict with training metrics (accuracy, F1, model type, etc.)
        """
        # Skip if already trained and not forced
        if self.is_trained and not force_retrain:
            print("[Compatibility Model] Already trained. Use force_retrain=True to retrain.")
            return {"status": "already_trained", "model_type": self.model_type}

        print("[Compatibility Model] Generating training data...")
        X, y, feature_names = generate_training_data(
            n_pairs=n_pairs,
            n_shipments=n_shipments,
            noise_rate=noise_rate,
            seed=seed,
        )
        self.feature_names = feature_names

        # Split into train and test sets.
        # stratify=y ensures both sets have the same positive/negative ratio.
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=seed, stratify=y,
        )

        # Scale features — important for LogisticRegression, doesn't hurt RF.
        # StandardScaler normalizes each feature to mean=0, std=1.
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        #  Train RandomForest 
        print("[Compatibility Model] Training RandomForest...")
        rf = RandomForestClassifier(
            n_estimators=400,         # More trees = better ensemble averaging
            max_depth=25,             # Deeper trees capture complex feature interactions
            min_samples_leaf=2,       # Finer splits for better recall on compatible pairs
            class_weight="balanced",  # Upweight the minority class (compatible pairs)
            random_state=seed,
            n_jobs=-1,                # Use all CPU cores for training
        )
        rf.fit(X_train_scaled, y_train)
        rf_pred = rf.predict(X_test_scaled)
        rf_f1 = f1_score(y_test, rf_pred)

        #  Train LogisticRegression 
        print("[Compatibility Model] Training LogisticRegression...")
        lr = LogisticRegression(
            max_iter=2000,            # More iterations for convergence with balanced weights
            class_weight="balanced",  # Upweight minority class to improve recall
            C=0.5,                    # Slightly stronger regularization
            random_state=seed,
        )
        lr.fit(X_train_scaled, y_train)
        lr_pred = lr.predict(X_test_scaled)
        lr_f1 = f1_score(y_test, lr_pred)

        #  Pick the winner by F1 score 
        # F1 balances precision and recall, which matters here because
        # both false positives (incompatible pairs passing) and false
        # negatives (compatible pairs blocked) are costly.
        if rf_f1 >= lr_f1:
            self.model = rf
            self.model_type = "RandomForest"
            best_f1 = rf_f1
            best_pred = rf_pred
        else:
            self.model = lr
            self.model_type = "LogisticRegression"
            best_f1 = lr_f1
            best_pred = lr_pred

        self.is_trained = True

        # Print detailed metrics for debugging
        print(f"\n[Compatibility Model] Winner: {self.model_type}")
        print(f"  RandomForest F1:        {rf_f1:.4f}")
        print(f"  LogisticRegression F1:  {lr_f1:.4f}")
        print(f"\n{classification_report(y_test, best_pred, target_names=['Incompatible', 'Compatible'])}")

        # Save model artifacts to disk
        self._save_model()

        # Compute feature importances (RF has them natively, LR uses coefficients)
        if self.model_type == "RandomForest":
            importances = dict(zip(feature_names, rf.feature_importances_))
        else:
            importances = dict(zip(feature_names, abs(lr.coef_[0])))

        # Sort by importance descending
        importances = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))

        return {
            "status": "trained",
            "model_type": self.model_type,
            "train_size": len(X_train),
            "test_size": len(X_test),
            "positive_rate": float(y.mean()),
            "rf_f1": round(rf_f1, 4),
            "lr_f1": round(lr_f1, 4),
            "best_f1": round(best_f1, 4),
            "feature_importances": {k: round(v, 4) for k, v in importances.items()},
        }

    def predict(self, shipment_a: Dict, shipment_b: Dict) -> float:
        """
        Predict the probability that two shipments are compatible.

        Returns P(compatible) between 0.0 and 1.0. Higher means more
        likely to consolidate successfully. The OR solver uses a threshold
        (typically 0.6) to decide which pairs can share a truck.

        Args:
            shipment_a: First shipment dict
            shipment_b: Second shipment dict

        Returns:
            Float probability between 0.0 and 1.0

        Raises:
            RuntimeError if the model hasn't been trained yet
        """
        if not self.is_trained:
            raise RuntimeError(
                "Model not trained. Call model.train() first or ensure "
                "a saved model exists in backend/app/ml/model/"
            )

        # Extract features for this pair
        features = extract_features(shipment_a, shipment_b)

        # Convert to numpy array in the same feature order as training
        X = np.array([[features[name] for name in self.feature_names]])

        # Scale features using the same scaler from training
        X_scaled = self.scaler.transform(X)

        # predict_proba returns [[P(class_0), P(class_1)]]
        # We want P(compatible) which is class 1
        proba = self.model.predict_proba(X_scaled)[0][1]

        return round(float(proba), 4)

    def predict_batch(self, pairs: List[Tuple[Dict, Dict]]) -> List[float]:
        """
        Score multiple shipment pairs in one batch call.

        More efficient than calling predict() in a loop because
        feature extraction and scaling happen once for the full batch.

        Args:
            pairs: List of (shipment_a, shipment_b) tuples

        Returns:
            List of P(compatible) scores, same order as input
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call model.train() first.")

        if not pairs:
            return []

        # Batch feature extraction
        feature_rows = []
        for shipment_a, shipment_b in pairs:
            features = extract_features(shipment_a, shipment_b)
            feature_rows.append([features[name] for name in self.feature_names])

        X = np.array(feature_rows)
        X_scaled = self.scaler.transform(X)

        # Batch prediction
        probas = self.model.predict_proba(X_scaled)[:, 1]

        return [round(float(p), 4) for p in probas]

    def build_compatibility_graph(
        self,
        shipments: List[Dict],
        threshold: float = 0.6,
    ) -> Dict:
        """
        Score all shipment pairs and build a compatibility graph.

        The graph is a networkx Graph where:
        - Each node is a shipment (by shipment_id)
        - An edge exists between two shipments if P(compatible) >= threshold
        - Edge weight = P(compatible)

        This graph feeds into the OR solver as a constraint: only pairs
        connected by an edge can be assigned to the same vehicle.

        Args:
            shipments: List of shipment dicts
            threshold: Minimum compatibility probability to create an edge.
                       Higher = stricter (fewer edges, harder to consolidate).
                       Lower = looser (more edges, easier to consolidate).

        Returns:
            Dict with:
            - graph: networkx.Graph object
            - edges: list of (id_a, id_b, score) tuples
            - stats: summary statistics about the graph
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call model.train() first.")

        n = len(shipments)
        print(f"[Compatibility Model] Scoring {n * (n-1) // 2} shipment pairs...")

        # Generate all unique pairs
        pairs = []
        pair_ids = []
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append((shipments[i], shipments[j]))
                pair_ids.append((
                    shipments[i].get("shipment_id", f"S{i}"),
                    shipments[j].get("shipment_id", f"S{j}"),
                ))

        # Batch score all pairs at once (much faster than one-by-one)
        scores = self.predict_batch(pairs)

        # Build the networkx graph
        G = nx.Graph()

        # Add all shipments as nodes
        for s in shipments:
            sid = s.get("shipment_id", "")
            G.add_node(sid, **{
                "origin": s.get("origin", ""),
                "destination": s.get("destination", ""),
                "weight": s.get("weight", 0),
                "priority": s.get("priority", "MEDIUM"),
            })

        # Add edges for compatible pairs (above threshold)
        edges = []
        for (id_a, id_b), score in zip(pair_ids, scores):
            if score >= threshold:
                G.add_edge(id_a, id_b, weight=score)
                edges.append({"shipment_a": id_a, "shipment_b": id_b, "score": score})

        # Compute graph statistics for the insights panel
        total_pairs = len(pairs)
        compatible_pairs = len(edges)
        compatibility_rate = compatible_pairs / total_pairs if total_pairs > 0 else 0

        # Average node degree tells us how many consolidation options
        # each shipment has — higher is better for the optimizer
        avg_degree = sum(dict(G.degree()).values()) / n if n > 0 else 0

        # Connected components tell us how many independent groups exist.
        # Ideally one big connected component = lots of consolidation options.
        components = list(nx.connected_components(G))

        stats = {
            "total_shipments": n,
            "total_pairs_scored": total_pairs,
            "compatible_pairs": compatible_pairs,
            "compatibility_rate": round(compatibility_rate, 4),
            "threshold_used": threshold,
            "avg_connections_per_shipment": round(avg_degree, 1),
            "connected_components": len(components),
            "largest_component_size": len(max(components, key=len)) if components else 0,
        }

        print(f"[Compatibility Model] Graph built: {compatible_pairs}/{total_pairs} "
              f"pairs compatible ({compatibility_rate:.1%}), "
              f"avg {avg_degree:.1f} connections per shipment")

        return {
            "graph": G,
            "edges": edges,
            "stats": stats,
        }

    def _save_model(self):
        """
        Persist the trained model, scaler, and metadata to disk.
        Uses joblib for efficient serialization of numpy-heavy objects.
        """
        os.makedirs(MODEL_DIR, exist_ok=True)

        joblib.dump(self.model, MODEL_PATH)
        joblib.dump(self.scaler, SCALER_PATH)
        joblib.dump({
            "feature_names": self.feature_names,
            "model_type": self.model_type,
        }, METADATA_PATH)

        print(f"[Compatibility Model] Saved to {MODEL_DIR}/")

    def _load_model(self):
        """
        Load a previously saved model from disk.
        Called automatically on initialization — if a model exists,
        we're ready to predict without retraining.
        """
        if not all(os.path.exists(p) for p in [MODEL_PATH, SCALER_PATH, METADATA_PATH]):
            return  # No saved model found, training needed

        try:
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            metadata = joblib.load(METADATA_PATH)
            self.feature_names = metadata["feature_names"]
            self.model_type = metadata["model_type"]
            self.is_trained = True
            print(f"[Compatibility Model] Loaded {self.model_type} from {MODEL_DIR}/")
        except Exception as e:
            print(f"[Compatibility Model] Failed to load saved model: {e}")
            self.is_trained = False