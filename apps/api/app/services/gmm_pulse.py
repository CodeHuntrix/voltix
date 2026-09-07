"""Load Eesha/Ramitha GMM artifacts and score instantaneous OFF/IDLE/ACTIVE."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

_here = Path(__file__).resolve()
_PULSE_ROOT = Path("/pulse") if Path("/pulse/src").exists() else None
if _PULSE_ROOT is None:
    for parent in _here.parents:
        candidate = parent / "voltix-pulse"
        if candidate.exists():
            _PULSE_ROOT = candidate
            break
if _PULSE_ROOT and str(_PULSE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PULSE_ROOT))

GMM_TYPE_KEYS = {
    "compressor": "compressor_01",
    "air_compressor": "compressor_01",
    "aircompressor": "compressor_01",
    "laptop": "laptop_charger_01",
    "laptop_charger": "laptop_charger_01",
    "charger": "laptop_charger_01",
}


def gmm_machine_id(machine_type: str | None, name: str | None = None) -> str | None:
    blob = f"{machine_type or ''} {name or ''}".lower()
    if "compress" in blob:
        return "compressor_01"
    if "laptop" in blob or "charger" in blob:
        return "laptop_charger_01"
    key = (machine_type or "").lower().strip().replace(" ", "_")
    mapped = GMM_TYPE_KEYS.get(key)
    if mapped:
        return mapped
    return None


def gmm_available() -> bool:
    try:
        from src.pulse.predict import load_model_and_meta  # noqa: F401

        return True
    except Exception:
        return False


@lru_cache(maxsize=8)
def _load(gmm_id: str) -> tuple[Any, dict]:
    from src.pulse.predict import load_model_and_meta

    return load_model_and_meta(gmm_id)


def predict_gmm_instant(
    gmm_id: str,
    i_rms_a: float,
    history_i: list[float] | None = None,
) -> tuple[str, float, str, dict]:
    """Returns (OFF|IDLE|ACTIVE, confidence, model_version, meta). Does not apply WASTE."""
    from src.pulse.predict import compute_causal_features_online

    gmm, meta = _load(gmm_id)
    x = compute_causal_features_online(i_rms_a, history_i)
    cluster_id = int(gmm.predict(x)[0])
    probabilities = gmm.predict_proba(x)[0]
    confidence = float(max(probabilities))
    cluster_map = meta.get("cluster_map", {})
    state = cluster_map.get(str(cluster_id), "IDLE")
    if i_rms_a < 0.02:
        state = "OFF"
        confidence = 1.0
    version = meta.get("model_version", "gmm-v1")
    return state, round(confidence, 4), version, meta
