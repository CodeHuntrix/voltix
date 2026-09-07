"""
Voltix Pulse Engine — Model Registry
Maps machine identifiers to machine-specific trained GMM models, metadata, and operational policies.
"""

import os
from typing import Any

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
MODELS_DIR = os.environ.get("VOLTIX_MODELS_DIR", os.path.join(PROJECT_ROOT, "models", "pulse"))

# Machine Model Registry
MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "laptop_charger_01": {
        "machine_type": "laptop_charger",
        "model_file": os.path.join(MODELS_DIR, "laptop_charger_gmm.joblib"),
        "meta_file": os.path.join(MODELS_DIR, "laptop_charger_meta.json"),
        "sampling_interval_seconds": 2.0,
        "effective_feature_window_seconds": 6.0,
        "waste_detection": {
            "enabled": False,
            "reason": "WASTE is not distinguishable from S4P10 dataset without continuous ground-truth policy"
        }
    },
    "compressor_01": {
        "machine_type": "compressor",
        "model_file": os.path.join(MODELS_DIR, "compressor_gmm.joblib"),
        "meta_file": os.path.join(MODELS_DIR, "compressor_meta.json"),
        "sampling_interval_seconds": 10.0,
        "effective_feature_window_seconds": 30.0,
        "waste_detection": {
            "enabled": True,
            "method": "duration_rule",
            "duration_seconds": 300  # 5 minutes of continuous unloaded operation = WASTE
        }
    }
}

# Alias mapping for machine types
TYPE_TO_ID = {
    "laptop_charger": "laptop_charger_01",
    "laptop": "laptop_charger_01",
    "compressor": "compressor_01",
    "air_compressor": "compressor_01"
}


def resolve_machine_id(machine_identifier: str) -> str:
    """Resolve identifier to standard machine_id."""
    clean = machine_identifier.lower().strip()
    if clean in MODEL_REGISTRY:
        return clean
    if clean in TYPE_TO_ID:
        return TYPE_TO_ID[clean]
    raise KeyError(f"Machine identifier '{machine_identifier}' not found in Voltix Model Registry. Registered: {list(MODEL_REGISTRY.keys())}")


def get_machine_config(machine_identifier: str) -> dict[str, Any]:
    """Retrieve configuration dict for a machine."""
    m_id = resolve_machine_id(machine_identifier)
    return MODEL_REGISTRY[m_id]


def get_model_path(machine_identifier: str) -> str:
    """Get path to the trained .joblib model."""
    return get_machine_config(machine_identifier)["model_file"]


def get_meta_path(machine_identifier: str) -> str:
    """Get path to the model metadata JSON."""
    return get_machine_config(machine_identifier)["meta_file"]
