"""Drift scoring, normalization, persistence filter, and severity mapper."""

import math
from collections import deque
from typing import Tuple, List, Dict


class DriftScorer:
    def __init__(
        self,
        z_threshold: float = 3.0,
        score_lambda: float = 0.4,
        persistence_m: int = 3,
        persistence_n: int = 5,
        severity_low_thresh: float = 0.0,
        severity_med_thresh: float = 0.40,
        severity_high_thresh: float = 0.75,
    ):
        self.z_threshold = z_threshold
        self.score_lambda = score_lambda
        self.persistence_m = persistence_m
        self.persistence_n = persistence_n
        self.severity_med_thresh = severity_med_thresh
        self.severity_high_thresh = severity_high_thresh
        self.history_buffer = deque(maxlen=persistence_n)

    def normalize_score(self, raw_score: float) -> float:
        """
        Monotonic bounded mapping from raw score (Z-score / Mahalanobis dist) to 0..1 range.
        S = 1 - exp(-lambda * max(0, raw_score))
        """
        if raw_score <= 0:
            return 0.0
        val = 1.0 - math.exp(-self.score_lambda * raw_score)
        return float(min(1.0, max(0.0, round(val, 4))))

    def assign_severity(self, drift_score: float, flag: bool) -> str:
        """Assigns low / medium / high severity string."""
        if not flag or drift_score < self.severity_med_thresh:
            return "low"
        elif drift_score < self.severity_high_thresh:
            return "medium"
        else:
            return "high"

    def evaluate_sample(self, raw_z_score: float, feature_val: float, baseline_mean: float, baseline_std: float) -> Tuple[bool, float, str, str]:
        """
        Evaluates a single sample with persistence filter.
        Returns: (flag, drift_score, severity, message)
        """
        drift_score = self.normalize_score(raw_z_score)
        is_candidate_anomaly = raw_z_score >= self.z_threshold
        
        self.history_buffer.append(is_candidate_anomaly)
        recent_anomalies = sum(self.history_buffer)
        
        flag = recent_anomalies >= self.persistence_m
        severity = self.assign_severity(drift_score, flag)
        
        if flag:
            diff = feature_val - baseline_mean
            direction = "above" if diff >= 0 else "below"
            msg = f"ACTIVE i_rms {direction} baseline band (z={raw_z_score:.2f}, score={drift_score:.2f})"
        elif is_candidate_anomaly:
            msg = f"Transient current spike detected (z={raw_z_score:.2f}); persistence filter active"
        else:
            msg = f"ACTIVE operation within normal baseline (z={raw_z_score:.2f})"

        return flag, drift_score, severity, msg

    def reset_buffer(self):
        """Clears persistence buffer."""
        self.history_buffer.clear()
