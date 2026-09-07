"""Production inference API hook for Voltix Condition / Drift Engine."""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from .features import extract_features_single
from .baseline import BaselineDriftModel
from .scoring import DriftScorer

# Global in-memory cache for loaded per-machine models and scorers
_MODEL_CACHE: Dict[str, BaselineDriftModel] = {}
_SCORER_CACHE: Dict[str, DriftScorer] = {}


def _get_models_dir() -> str:
    """Returns absolute path to models/drift directory."""
    if os.environ.get("VOLTIX_MODELS_DIR"):
        return os.environ["VOLTIX_MODELS_DIR"]
    
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    candidate_1 = os.path.join(base_dir, "models", "drift")
    if os.path.exists(candidate_1):
        return candidate_1
        
    candidate_2 = os.path.join(base_dir, "voltix-condition", "models", "drift")
    if os.path.exists(candidate_2):
        return candidate_2
        
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models", "drift"))


def get_or_load_machine_model(machine_id: str, models_dir: Optional[str] = None) -> BaselineDriftModel:
    """Retrieves cached model instance or loads artifact from disk."""
    models_dir = models_dir or _get_models_dir()
    if machine_id not in _MODEL_CACHE:
        model = BaselineDriftModel(machine_id=machine_id)
        model.load(models_dir)
        _MODEL_CACHE[machine_id] = model
        
        # Initialize corresponding scorer with model hyperparameters
        params = model.params
        _SCORER_CACHE[machine_id] = DriftScorer(
            z_threshold=params.get("z_threshold", 3.0),
            score_lambda=params.get("score_lambda", 0.4),
            persistence_m=params.get("persistence_m", 3),
            persistence_n=params.get("persistence_n", 5),
        )
        
    return _MODEL_CACHE[machine_id]


def predict_drift(
    machine_id: str,
    i_rms_a: float,
    history_i: Optional[List[float]] = None,
    state: str = "ACTIVE",
    temp_c: Optional[float] = None,
    ts: Optional[str] = None,
    models_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Predicts electrical condition drift for an ACTIVE machine window.
    
    Product Contract (Voltix Layer 3):
    - Skips non-ACTIVE states (returns flag=False, drift_score=0.0).
    - Returns standardized dictionary:
      {
        "machine_id": str,
        "flag": bool,
        "drift_score": float, # 0..1
        "severity": "low" | "medium" | "high",
        "model_version": "drift-v1",
        "message": str,
        "ts": str
      }
    """
    ts_val = ts or datetime.now(timezone.utc).isoformat()
    
    # 1. State-Gating Rule: Skip non-ACTIVE states
    if state != "ACTIVE":
        return {
            "machine_id": machine_id,
            "flag": False,
            "drift_score": 0.0,
            "severity": "low",
            "model_version": "drift-v1",
            "message": "skipped_non_active",
            "ts": ts_val,
        }

    # 2. Retrieve per-machine model and scorer
    try:
        model = get_or_load_machine_model(machine_id, models_dir=models_dir)
        scorer = _SCORER_CACHE[machine_id]
    except FileNotFoundError:
        # Fallback if specific machine_id artifact is missing: default to generic laptop_charger_01
        try:
            model = get_or_load_machine_model("laptop_charger_01", models_dir=models_dir)
            scorer = _SCORER_CACHE["laptop_charger_01"]
        except Exception as e:
            return {
                "machine_id": machine_id,
                "flag": False,
                "drift_score": 0.0,
                "severity": "low",
                "model_version": "drift-v1",
                "message": f"model_artifact_not_found: {e}",
                "ts": ts_val,
            }

    # 3. Extract window features
    window_size = model.params.get("window_size", 15)
    feat_dict = extract_features_single(i_rms_a, history=history_i, window_size=window_size)

    # 4. Calculate raw Z-score / distance
    raw_z_score, max_z = model.calculate_z_score(feat_dict)

    # 5. Evaluate persistence filter & severity mapping
    baseline_mean = model.params["means"]["i_rms_a"]
    baseline_std = model.params["stds"]["i_rms_a"]
    
    flag, drift_score, severity, message = scorer.evaluate_sample(
        raw_z_score=raw_z_score,
        feature_val=i_rms_a,
        baseline_mean=baseline_mean,
        baseline_std=baseline_std,
    )

    return {
        "machine_id": machine_id,
        "flag": flag,
        "drift_score": drift_score,
        "severity": severity,
        "model_version": model.model_version,
        "message": message,
        "ts": ts_val,
    }


def reset_inference_cache():
    """Clears in-memory model and persistence buffer cache (useful for testing)."""
    _MODEL_CACHE.clear()
    _SCORER_CACHE.clear()
