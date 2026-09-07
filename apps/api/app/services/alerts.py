"""Alert creation helpers — CS Layer 5 (waste / offline / drift)."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, Machine, MachineLatest

WASTE_ALERT_MINUTES = 10
OFFLINE_MINUTES = 3
RULE_VERSION = "rules-alerts-v1"


async def _open_alert(
    db: AsyncSession,
    machine_id: UUID,
    alert_type: str,
) -> Alert | None:
    existing = await db.execute(
        select(Alert)
        .where(
            Alert.machine_id == machine_id,
            Alert.alert_type == alert_type,
            Alert.acknowledged.is_(False),
        )
        .limit(1)
    )
    return existing.scalar_one_or_none()


async def clear_alerts(
    db: AsyncSession,
    machine_id: UUID,
    alert_type: str,
) -> None:
    """V1 resolve path: mark open alerts acknowledged when trigger clears."""
    await db.execute(
        update(Alert)
        .where(
            Alert.machine_id == machine_id,
            Alert.alert_type == alert_type,
            Alert.acknowledged.is_(False),
        )
        .values(acknowledged=True)
    )


async def maybe_create_waste_alert(
    db: AsyncSession,
    machine: Machine,
    state: str,
    duration_min: float,
    waste_inr_per_hr: float,
) -> Alert | None:
    if state != "WASTE":
        await clear_alerts(db, machine.id, "waste")
        return None
    if duration_min < WASTE_ALERT_MINUTES:
        return None
    if await _open_alert(db, machine.id, "waste"):
        return None

    alert = Alert(
        site_id=machine.site_id,
        machine_id=machine.id,
        alert_type="waste",
        severity="warning" if duration_min < 30 else "critical",
        title=f"{machine.name} · WASTE {int(duration_min)}m",
        message=(
            f"Sustained waste ~₹{waste_inr_per_hr:.0f}/hr "
            f"({RULE_VERSION}). Review AutoCut eligibility."
        ),
    )
    db.add(alert)
    return alert


async def maybe_create_offline_alert(
    db: AsyncSession,
    machine: Machine,
    latest: MachineLatest | None,
) -> Alert | None:
    if latest is None or latest.time is None:
        return None
    t = latest.time
    if t.tzinfo is None:
        t = t.replace(tzinfo=UTC)
    age = datetime.now(UTC) - t
    if age < timedelta(minutes=OFFLINE_MINUTES):
        await clear_alerts(db, machine.id, "offline")
        return None
    if await _open_alert(db, machine.id, "offline"):
        return None

    alert = Alert(
        site_id=machine.site_id,
        machine_id=machine.id,
        alert_type="offline",
        severity="critical",
        title=f"{machine.name} · OFFLINE",
        message=(
            f"No telemetry for {int(age.total_seconds() // 60)} minutes "
            f"({RULE_VERSION}). Device/gateway loss — not machine OFF."
        ),
    )
    db.add(alert)
    return alert
