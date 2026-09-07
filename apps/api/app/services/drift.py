"""Backend Service Integration for Layer 3 Condition / Drift Engine."""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, Machine

_here = Path(__file__).resolve()
_voltix_root = next(
    (p for p in _here.parents if (p / "voltix-condition").exists()),
    _here.parents[4] if len(_here.parents) > 4 else _here.parent,
)
_condition_src = _voltix_root / "voltix-condition" / "src"
if _condition_src.exists() and str(_condition_src) not in sys.path:
    sys.path.insert(0, str(_condition_src))
if (_voltix_root / "voltix-condition").exists() and str(_voltix_root) not in sys.path:
    sys.path.insert(0, str(_voltix_root))


def drift_artifact_id(machine: Machine) -> str:
    blob = f"{machine.machine_type or ''} {machine.name or ''}".lower()
    if "compress" in blob:
        return "compressor_01"
    if "laptop" in blob or "charger" in blob:
        return "laptop_charger_01"
    return "laptop_charger_01"


def condition_models_dir() -> str | None:
    env = os.environ.get("VOLTIX_CONDITION_MODELS_DIR")
    if env and Path(env).exists():
        return env
    docker = Path("/condition/models/drift")
    if docker.exists():
        return str(docker)
    local = _voltix_root / "voltix-condition" / "models" / "drift"
    if local.exists():
        return str(local)
    return None


async def maybe_create_drift_alert(
    db: AsyncSession,
    machine: Machine,
    state: str,
    i_rms_a: float,
    temp_c: float | None = None,
    history_i: list[float] | None = None,
) -> tuple[dict[str, Any], Alert | None]:
    """ACTIVE-only condition drift; creates alert_type=drift when flagged."""
    from condition.inference import predict_drift

    if state != "ACTIVE":
        from app.services.alerts import clear_alerts

        await clear_alerts(db, machine.id, "drift")
        return {
            "machine_id": str(machine.id),
            "flag": False,
            "drift_score": 0.0,
            "severity": "low",
            "model_version": "drift-v1",
            "message": "skipped_non_active",
        }, None

    artifact = drift_artifact_id(machine)
    models_dir = condition_models_dir()
    try:
        drift_res = predict_drift(
            machine_id=artifact,
            i_rms_a=i_rms_a,
            history_i=history_i,
            state=state,
            temp_c=temp_c,
            models_dir=models_dir,
        )
    except Exception as exc:
        return {
            "machine_id": str(machine.id),
            "flag": False,
            "drift_score": 0.0,
            "severity": "low",
            "model_version": "drift-v1",
            "message": f"drift_eval_error: {exc}",
        }, None

    if not drift_res.get("flag", False):
        return drift_res, None

    since = datetime.now(UTC) - timedelta(minutes=30)
    existing = await db.execute(
        select(Alert)
        .where(
            Alert.machine_id == machine.id,
            Alert.alert_type == "drift",
            Alert.acknowledged.is_(False),
            Alert.created_at >= since,
        )
        .limit(1)
    )
    if existing.scalar_one_or_none():
        return drift_res, None

    severity_str = "critical" if drift_res.get("severity") == "high" else "warning"
    alert = Alert(
        site_id=machine.site_id,
        machine_id=machine.id,
        alert_type="drift",
        severity=severity_str,
        title=f"{machine.name} · Condition Drift ({str(drift_res.get('severity', 'medium')).upper()})",
        message=str(drift_res.get("message") or "ACTIVE electrical drift detected"),
    )
    db.add(alert)
    return drift_res, alert


async def evaluate_drift_safe(
    db: AsyncSession,
    machine: Machine,
    state: str,
    i_rms_a: float,
    temp_c: float | None,
    history_i: list[float] | None,
) -> None:
    """Ingest-safe wrapper — never raises into the telemetry path."""
    try:
        await maybe_create_drift_alert(
            db,
            machine,
            state=state,
            i_rms_a=i_rms_a,
            temp_c=temp_c,
            history_i=history_i,
        )
    except Exception:
        pass
