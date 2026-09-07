"""
IsolationForest-based comparative model for Voltix Condition Engine.

Uses sklearn.ensemble.IsolationForest.
If sklearn/scipy is unavailable, falls back to a lightweight
pure-numpy anomaly scorer that mimics the same interface.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

# Try sklearn; gracefully fall back to pure-numpy approximation
_SKLEARN_AVAILABLE = False
try:
    from sklearn.ensemble import IsolationForest as _SklearnIF
    _SKLEARN_AVAILABLE = True
except ImportError:
    pass

try:
    import joblib as _joblib
    _JOBLIB_AVAILABLE = True
except ImportError:
    _JOBLIB_AVAILABLE = False


class _NumpyAnomalyScorer:
    """
    Lightweight pure-numpy anomaly scorer used when sklearn is unavailable.
    Fits a multivariate normal distribution on healthy data and scores
    new points by their normalised Mahalanobis distance.
    Mimics the interface of IsolationForest so the rest of the codebase
    doesn't need to know which backend is running.
    """
    def __init__(self, contamination: float = 0.01):
        self.contamination = contamination
        self._mean: np.ndarray | None = None
        self._cov_inv: np.ndarray | None = None
        self._threshold: float = 0.0

    def fit(self, X: np.ndarray) -> None:
        self._mean = np.mean(X, axis=0)
        cov = np.cov(X, rowvar=False)
        self._cov_inv = np.linalg.pinv(cov)
        scores = self._raw_scores(X)
        self._threshold = float(np.percentile(scores, (1 - self.contamination) * 100))

    def _raw_scores(self, X: np.ndarray) -> np.ndarray:
        diffs = X - self._mean
        return np.array([
            float(np.sqrt(np.clip(d @ self._cov_inv @ d, 0, None)))
            for d in diffs
        ])

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Positive = normal, negative = anomaly (same sign convention as sklearn)."""
        scores = self._raw_scores(X)
        return (self._threshold - scores)


class IsolationForestDriftModel:
    """
    Comparative condition drift model (sklearn IsolationForest or numpy fallback).

    This model is used to benchmark against the primary Baseline Z-Score model.
    It does not replace the primary model; it exists for evaluation only.
    """

    def __init__(
        self,
        machine_id: str = "laptop_charger_01",
        model_version: str = "drift-v1",
        contamination: float = 0.01,
    ):
        self.machine_id = machine_id
        self.model_version = model_version
        self.contamination = contamination
        self.features = ["i_rms_a", "i_rolling_mean", "i_rolling_std"]
        self.backend = "sklearn" if _SKLEARN_AVAILABLE else "numpy"

        if _SKLEARN_AVAILABLE:
            self.model = _SklearnIF(
                n_estimators=100,
                contamination=self.contamination,
                random_state=42,
            )
        else:
            self.model = _NumpyAnomalyScorer(contamination=self.contamination)

        self.is_fitted = False

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(self, df_features: pd.DataFrame) -> None:
        """Fits the model on healthy ACTIVE feature matrix."""
        X = df_features[self.features].values
        self.model.fit(X)
        self.is_fitted = True

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def calculate_score(self, feature_dict: Dict[str, float]) -> Tuple[float, float]:
        """
        Returns (raw_anomaly_score, decision_val).

        decision_function > 0 → normal; < 0 → anomaly (sklearn convention).
        raw_anomaly_score is a non-negative value: higher = more anomalous.
        """
        if not self.is_fitted:
            raise RuntimeError("IsolationForestDriftModel is not fitted yet.")

        x_vec = np.array([[feature_dict[feat] for feat in self.features]])
        decision_val = float(self.model.decision_function(x_vec)[0])
        raw_score = float(max(0.0, -decision_val * 10.0))
        return raw_score, decision_val

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, models_dir: str) -> None:
        """Saves model artifact. Uses joblib if available, else JSON (numpy backend)."""
        os.makedirs(models_dir, exist_ok=True)

        if self.backend == "sklearn" and _JOBLIB_AVAILABLE:
            import joblib
            path = os.path.join(models_dir, f"{self.machine_id}_drift.joblib")
            joblib.dump(self.model, path)
        else:
            # Serialise numpy backend as JSON
            path = os.path.join(models_dir, f"{self.machine_id}_drift_numpy.json")
            payload = {
                "backend": "numpy",
                "mean": self.model._mean.tolist() if self.model._mean is not None else [],
                "cov_inv": self.model._cov_inv.tolist() if self.model._cov_inv is not None else [],
                "threshold": float(self.model._threshold),
                "contamination": self.contamination,
                "features": self.features,
            }
            with open(path, "w") as f:
                json.dump(payload, f, indent=2)

    def load(self, models_dir: str) -> None:
        """Loads model artifact from disk."""
        joblib_path = os.path.join(models_dir, f"{self.machine_id}_drift.joblib")
        numpy_path = os.path.join(models_dir, f"{self.machine_id}_drift_numpy.json")

        if os.path.exists(joblib_path) and _JOBLIB_AVAILABLE:
            import joblib
            self.model = joblib.load(joblib_path)
            self.backend = "sklearn"
        elif os.path.exists(numpy_path):
            with open(numpy_path) as f:
                payload = json.load(f)
            scorer = _NumpyAnomalyScorer(contamination=payload["contamination"])
            scorer._mean = np.array(payload["mean"])
            scorer._cov_inv = np.array(payload["cov_inv"])
            scorer._threshold = payload["threshold"]
            self.model = scorer
            self.backend = "numpy"
        else:
            raise FileNotFoundError(
                f"No model artifact found for {self.machine_id} in {models_dir}"
            )
        self.is_fitted = True

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"IsolationForestDriftModel("
            f"machine_id={self.machine_id!r}, "
            f"backend={self.backend!r}, "
            f"fitted={self.is_fitted})"
        )
