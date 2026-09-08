"""
Voltix Pulse Engine — Inference Module
Provides high-throughput online inference for machine-specific GMM state detection
with decoupled temporal duration-based waste rule.
"""

import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import json
import joblib
import numpy as np
from typing import Any

from .model_registry import (
    resolve_machine_id,
    get_machine_config
)

# In-memory model and metadata cache
_MODEL_CACHE: dict[str, Any] = {}
_META_CACHE: dict[str, dict] = {}

# In-memory state duration tracker for temporal waste rules
# Maps machine_id -> {"current_state": str, "idle_duration_seconds": float}
_STATE_TRACKER: dict[str, dict[str, Any]] = {}


def load_model_and_meta(machine_id: str) -> tuple[Any, dict]:
    """Load and cache the trained GMM and metadata for a machine."""
    m_id = resolve_machine_id(machine_id)
    
    if m_id not in _MODEL_CACHE or m_id not in _META_CACHE:
        config = get_machine_config(m_id)
        model_file = config["model_file"]
        meta_file = config["meta_file"]
        
        if not os.path.exists(model_file):
            raise FileNotFoundError(f"Trained model artifact not found at {model_file}. Please run train.py first.")
        if not os.path.exists(meta_file):
            raise FileNotFoundError(f"Metadata file not found at {meta_file}. Please run train.py first.")
            
        _MODEL_CACHE[m_id] = joblib.load(model_file)
        with open(meta_file, "r", encoding="utf-8") as f:
            _META_CACHE[m_id] = json.load(f)
            
    return _MODEL_CACHE[m_id], _META_CACHE[m_id]


def reset_machine_state(machine_id: str | None = None) -> None:
    """Reset temporal state tracker for testing or session reset."""
    global _STATE_TRACKER
    if machine_id:
        m_id = resolve_machine_id(machine_id)
        _STATE_TRACKER.pop(m_id, None)
    else:
        _STATE_TRACKER.clear()


def compute_causal_features_online(
    i_rms_a: float,
    history_i: list[float] | None = None
) -> np.ndarray:
    """
    Computes [i_rms_a, i_mean_3samples, i_std_3samples] from current reading and past history.
    Uses strictly causal past observations (at most 2 past samples + current sample = 3 samples).
    """
    if history_i is None or len(history_i) == 0:
        samples = [i_rms_a]
    elif len(history_i) == 1:
        samples = [history_i[-1], i_rms_a]
    else:
        samples = [history_i[-2], history_i[-1], i_rms_a]
        
    mean_val = float(np.mean(samples))
    std_val = float(np.std(samples, ddof=1)) if len(samples) > 1 else 0.0
    
    return np.array([[i_rms_a, mean_val, std_val]], dtype=np.float64)


def predict_pulse_state(
    machine_id: str,
    i_rms_a: float,
    history_i: list[float] | None = None,
    time_delta_seconds: float | None = None
) -> tuple[str, float, str]:
    """
    Core Voltix Pulse Engine inference API.
    
    Parameters:
      machine_id: Machine identifier (e.g. 'laptop_charger_01', 'compressor_01')
      i_rms_a: Instantaneous RMS current in Amperes
      history_i: Optional list of past current observations (most recent last)
      time_delta_seconds: Optional elapsed seconds since last sample (defaults to machine nominal)
      
    Returns:
      (state, confidence, model_version)
      where state is one of: OFF, IDLE, ACTIVE, WASTE
    """
    m_id = resolve_machine_id(machine_id)
    gmm, meta = load_model_and_meta(m_id)
    
    # 1. Feature extraction (causal past only)
    x = compute_causal_features_online(i_rms_a, history_i)
    
    # 2. GMM prediction & exact posterior confidence
    cluster_id = int(gmm.predict(x)[0])
    probabilities = gmm.predict_proba(x)[0]
    confidence = float(np.max(probabilities))
    
    # 3. Map cluster to instantaneous operational state (OFF, IDLE, ACTIVE)
    cluster_map = meta.get("cluster_map", {})
    instantaneous_state = cluster_map.get(str(cluster_id), "IDLE")
    
    # Physical zero-current cutoff for unplugged/unpowered state
    if i_rms_a < 0.02 and "OFF" not in cluster_map.values():
        instantaneous_state = "OFF"
        confidence = 1.0
    
    # 4. Decoupled Pulse Engine duration-based WASTE policy
    final_state = instantaneous_state
    waste_config = meta.get("waste_detection", {})
    
    dt = time_delta_seconds if time_delta_seconds is not None else meta.get("sampling_interval_seconds", 1.0)
    
    # Initialize tracker for machine if not present
    if m_id not in _STATE_TRACKER:
        _STATE_TRACKER[m_id] = {
            "current_state": instantaneous_state,
            "idle_duration_seconds": 0.0
        }
        
    tracker = _STATE_TRACKER[m_id]
    
    if waste_config.get("enabled", False):
        threshold_seconds = waste_config.get("duration_seconds", 300)
        
        if instantaneous_state == "IDLE":
            tracker["idle_duration_seconds"] += dt
            if tracker["idle_duration_seconds"] >= threshold_seconds:
                final_state = "WASTE"
        else:
            # Machine is OFF or ACTIVE; reset prolonged idle duration
            tracker["idle_duration_seconds"] = 0.0
    else:
        # Machine does not support/enable duration-based waste rule
        tracker["idle_duration_seconds"] = 0.0
        
    tracker["current_state"] = final_state
    model_version = meta.get("model_version", "gmm-v1")
    
    return final_state, round(confidence, 4), model_version

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Voltix Pulse Engine inference"
    )

    parser.add_argument(
        "--machine",
        required=True,
        help="Machine ID"
    )

    parser.add_argument(
        "--current",
        type=float,
        required=True,
        help="RMS current in Amperes"
    )

    parser.add_argument(
        "--history",
        nargs="*",
        type=float,
        default=[],
        help="Previous current readings"
    )

    parser.add_argument(
        "--dt",
        type=float,
        default=None,
        help="Time since previous sample in seconds"
    )

    args = parser.parse_args()

    state, confidence, version = predict_pulse_state(
        machine_id=args.machine,
        i_rms_a=args.current,
        history_i=args.history,
        time_delta_seconds=args.dt
    )

    print(f"Machine    : {args.machine}")
    print(f"Current    : {args.current} A")
    print(f"State      : {state}")
    print(f"Confidence : {confidence}")
    print(f"Model      : {version}")
