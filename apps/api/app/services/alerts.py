"""Alert creation helpers."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, Machine, MachineLatest


WASTE_ALERT_MINUTES = 10
OFFLINE_MINUTES = 3


async def maybe_create_waste_alert(
    db: AsyncSession,
    machine: Machine,
    state: str,
    duration_min: float,
    waste_inr_per_hr: float,
) -> Alert | None:
    if state != "WASTE" or duration_min < WASTE_ALERT_MINUTES:
        return None

    since = datetime.now(UTC) - timedelta(minutes=30)
    existing = await db.execute(
        select(Alert)
        .where(
            Alert.machine_id == machine.id,
            Alert.alert_type == "waste",
            Alert.acknowledged.is_(False),
            Alert.created_at >= since,
        )
        .limit(1)
    )
    if existing.scalar_one_or_none():
        return None

    alert = Alert(
        site_id=machine.site_id,
        machine_id=machine.id,
        alert_type="waste",
        severity="warning" if duration_min < 30 else "critical",
        title=f"{machine.name} · WASTE {int(duration_min)}m",
        message=f"Sustained waste ~₹{waste_inr_per_hr:.0f}/hr. Review AutoCut eligibility.",
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
        return None

    since = datetime.now(UTC) - timedelta(minutes=60)
    existing = await db.execute(
        select(Alert)
        .where(
            Alert.machine_id == machine.id,
            Alert.alert_type == "offline",
            Alert.acknowledged.is_(False),
            Alert.created_at >= since,
        )
        .limit(1)
    )
    if existing.scalar_one_or_none():
        return None

    alert = Alert(
        site_id=machine.site_id,
        machine_id=machine.id,
        alert_type="offline",
        severity="critical",
        title=f"{machine.name} · OFFLINE",
        message=f"No telemetry for {int(age.total_seconds() // 60)} minutes.",
    )
    db.add(alert)
    return alert
