"""Backend Service Integration for Layer 3 Condition / Drift Engine."""

import sys
import os
from datetime import UTC, datetime, timedelta
from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, Machine, MachineLatest

# Ensure voltix-condition package is importable
voltix_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, os.path.join(voltix_root, "voltix-condition", "src"))
sys.path.insert(0, voltix_root)

from condition.inference import predict_drift


async def maybe_create_drift_alert(
    db: AsyncSession,
    machine: Machine,
    state: str,
    i_rms_a: float,
    temp_c: Optional[float] = None,
    history_i: Optional[list[float]] = None,
) -> tuple[Dict[str, Any], Optional[Alert]]:
    """
    Evaluates condition drift for an ACTIVE machine telemetry sample.
    If flag == True, creates an Alert with alert_type='drift'.
    Returns: (drift_result_dict, created_alert_or_none)
    """
    machine_id_str = str(machine.id)
    drift_res = predict_drift(
        machine_id=machine_id_str,
        i_rms_a=i_rms_a,
        history_i=history_i,
        state=state,
        temp_c=temp_c,
    )
    
    if not drift_res.get("flag", False):
        return drift_res, None

    # Check for existing unacknowledged drift alert in the last 30 minutes to prevent alert spam
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

    severity_str = "critical" if drift_res["severity"] == "high" else "warning"
    alert = Alert(
        site_id=machine.site_id,
        machine_id=machine.id,
        alert_type="drift",
        severity=severity_str,
        title=f"{machine.name} · Condition Drift ({drift_res['severity'].upper()})",
        message=f"{drift_res['message']}",
    )
    db.add(alert)
    return drift_res, alert
