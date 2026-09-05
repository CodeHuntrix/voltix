"""Pulse / machine-state engine with debounce. GMM-ready via model_version hook."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Machine, MachineLatest, MachineStateEvent

DEBOUNCE_SECONDS = 8


def classify_current(i_rms: float, machine: Machine) -> str:
    if i_rms < machine.thr_off:
        return "OFF"
    if i_rms < machine.thr_idle:
        return "IDLE"
    if i_rms < machine.thr_active:
        # Between idle and active band → treat as IDLE/WASTE candidate when prolonged
        return "IDLE"
    return "ACTIVE"


def refine_waste(raw_state: str, kw_est: float, machine: Machine) -> str:
    """IDLE above baseline idle draw → WASTE (parasitic / no-load waste)."""
    if raw_state == "IDLE" and kw_est > machine.baseline_idle_kw * 1.15:
        return "WASTE"
    if raw_state == "ACTIVE" and kw_est < machine.baseline_idle_kw * 1.5:
        # Low active band with elevated idle — still waste-like
        return "IDLE"
    return raw_state


async def apply_pulse(
    db: AsyncSession,
    machine: Machine,
    i_rms_a: float,
    kw_est: float,
    now: datetime | None = None,
) -> tuple[str, float, bool]:
    """
    Update machine latest state with debounce.
    Returns (state, confidence, state_changed).
    """
    settings = get_settings()
    now = now or datetime.now(UTC)
    raw = classify_current(i_rms_a, machine)
    candidate = refine_waste(raw, kw_est, machine)
    confidence = 0.85 if candidate == "WASTE" else 0.95

    result = await db.execute(select(MachineLatest).where(MachineLatest.machine_id == machine.id))
    latest = result.scalar_one_or_none()
    if latest is None:
        return candidate, confidence, True

    current = latest.state or "OFF"
    if candidate == current:
        latest.pending_state = None
        latest.pending_since = None
        return current, latest.state_confidence or confidence, False

    # Debounce: require sustained candidate
    if latest.pending_state != candidate:
        latest.pending_state = candidate
        latest.pending_since = now
        return current, latest.state_confidence or confidence, False

    pending_since = latest.pending_since or now
    if pending_since.tzinfo is None:
        pending_since = pending_since.replace(tzinfo=UTC)
    if now - pending_since < timedelta(seconds=DEBOUNCE_SECONDS):
        return current, latest.state_confidence or confidence, False

    # Commit state change
    open_evt = await db.execute(
        select(MachineStateEvent)
        .where(MachineStateEvent.machine_id == machine.id, MachineStateEvent.ended_at.is_(None))
        .order_by(MachineStateEvent.started_at.desc())
        .limit(1)
    )
    prev = open_evt.scalar_one_or_none()
    if prev:
        prev.ended_at = now

    db.add(
        MachineStateEvent(
            machine_id=machine.id,
            state=candidate,
            confidence=confidence,
            model_version=settings.model_version,
            started_at=now,
        )
    )
    latest.state = candidate
    latest.state_confidence = confidence
    latest.state_since = now
    latest.pending_state = None
    latest.pending_since = None
    latest.model_version = settings.model_version
    return candidate, confidence, True


def residual_waste_kw(kw_est: float, state: str, machine: Machine) -> float:
    if state == "WASTE":
        return max(0.0, kw_est - machine.baseline_idle_kw * 0.25)
    if state == "IDLE":
        return max(0.0, kw_est - machine.baseline_idle_kw)
    return 0.0
