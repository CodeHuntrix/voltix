"""Per-Machine Baseline Z-Score / Mahalanobis Condition Model."""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Tuple


class BaselineDriftModel:
    def __init__(self, machine_id: str = "laptop_charger_01", model_version: str = "drift-v1"):
        self.machine_id = machine_id
        self.model_version = model_version
        self.features = ["i_rms_a", "i_rolling_mean", "i_rolling_std"]
        self.params: Dict[str, Any] = {}
        self.is_fitted = False

    def fit(
        self,
        df_features: pd.DataFrame,
        window_size: int = 15,
        z_threshold: float = 5.0,
        target_false_alarm_rate: float = 0.01,
    ):
        """
        Fits baseline mean, std, and covariance from healthy ACTIVE feature rows.
        Optionally auto-calibrates z_threshold to achieve target_false_alarm_rate
        on the training data itself (conservative: sets threshold at the
        (1 - target_false_alarm_rate) quantile of training scores).
        """
        X = df_features[self.features].values
        means = np.mean(X, axis=0)
        stds = np.std(X, axis=0, ddof=1)
        stds = np.where(stds == 0, 1e-6, stds)  # avoid division by zero
        
        cov = np.cov(X, rowvar=False)
        cov_inv = np.linalg.pinv(cov)
        
        # Auto-calibrate threshold from training distribution
        diffs = X - means
        training_scores = np.array([
            float(np.max(np.abs(d / stds)))
            for d in diffs
        ])
        calibrated_threshold = float(np.percentile(training_scores, (1 - target_false_alarm_rate) * 100))
        # Use the larger of manual threshold and calibrated to avoid being too aggressive
        effective_threshold = max(z_threshold, calibrated_threshold)

        min_ts = str(df_features["ts"].min()) if "ts" in df_features.columns else ""
        max_ts = str(df_features["ts"].max()) if "ts" in df_features.columns else ""
        
        self.params = {
            "machine_id": self.machine_id,
            "model_version": self.model_version,
            "training_date": datetime.now(timezone.utc).isoformat(),
            "train_date_range": f"{min_ts} to {max_ts}",
            "sample_count": int(len(df_features)),
            "window_size": int(window_size),
            "z_threshold": float(effective_threshold),
            "z_threshold_manual": float(z_threshold),
            "z_threshold_calibrated": float(calibrated_threshold),
            "target_false_alarm_rate": float(target_false_alarm_rate),
            "score_lambda": 0.4,
            "persistence_m": 3,
            "persistence_n": 5,
            "features": self.features,
            "means": {feat: float(m) for feat, m in zip(self.features, means)},
            "stds": {feat: float(s) for feat, s in zip(self.features, stds)},
            "cov_inv": cov_inv.tolist(),
        }
        self.is_fitted = True

    def calculate_z_score(self, feature_dict: Dict[str, float]) -> Tuple[float, float]:
        """
        Calculates raw Z-score and Mahalanobis distance for a feature dictionary.
        Returns: (raw_score, max_single_feature_z)
        """
        if not self.is_fitted:
            raise RuntimeError("BaselineDriftModel is not fitted yet.")
            
        x_vec = np.array([feature_dict[feat] for feat in self.features])
        mean_vec = np.array([self.params["means"][feat] for feat in self.features])
        std_vec = np.array([self.params["stds"][feat] for feat in self.features])
        
        # 1. Max Z-score across features
        z_scores = np.abs((x_vec - mean_vec) / std_vec)
        max_z = float(np.max(z_scores))
        
        # 2. Mahalanobis distance
        diff = x_vec - mean_vec
        cov_inv = np.array(self.params["cov_inv"])
        mahal_dist = float(np.sqrt(np.clip(diff.T @ cov_inv @ diff, 0, None)))
        
        # Primary raw anomaly score combines max Z and Mahalanobis
        raw_score = max(max_z, mahal_dist)
        return raw_score, max_z

    def save(self, models_dir: str):
        """Saves baseline JSON and metadata JSON files."""
        os.makedirs(models_dir, exist_ok=True)
        baseline_path = os.path.join(models_dir, f"{self.machine_id}_baseline.json")
        meta_path = os.path.join(models_dir, f"{self.machine_id}_meta.json")
        
        with open(baseline_path, "w") as f:
            json.dump(self.params, f, indent=2)
            
        meta = {
            "machine_id": self.machine_id,
            "model_version": self.model_version,
            "features": self.features,
            "z_threshold": self.params["z_threshold"],
            "window_size": self.params["window_size"],
            "training_date": self.params["training_date"],
            "sample_count": self.params["sample_count"],
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

    def load(self, models_dir: str):
        """Loads model parameters from baseline JSON file."""
        baseline_path = os.path.join(models_dir, f"{self.machine_id}_baseline.json")
        if not os.path.exists(baseline_path):
            raise FileNotFoundError(f"Model artifact not found at {baseline_path}")
            
        with open(baseline_path, "r") as f:
            self.params = json.load(f)
            
        self.machine_id = self.params["machine_id"]
        self.model_version = self.params.get("model_version", "drift-v1")
        self.features = self.params["features"]
        self.is_fitted = True
