"""Pulse / machine-state engine: GMM-v1 when a model exists, else rules-v1."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Machine, MachineLatest, MachineStateEvent, Telemetry
from app.services.gmm_pulse import gmm_available, gmm_machine_id, predict_gmm_instant

DEBOUNCE_SECONDS = 8


def classify_current(i_rms: float, machine: Machine) -> str:
    if i_rms < machine.thr_off:
        return "OFF"
    if i_rms < machine.thr_idle:
        return "IDLE"
    if i_rms < machine.thr_active:
        return "IDLE"
    return "ACTIVE"


def refine_waste(raw_state: str, kw_est: float, machine: Machine) -> str:
    """IDLE above baseline idle draw → WASTE (parasitic / no-load waste)."""
    if raw_state == "IDLE" and kw_est > machine.baseline_idle_kw * 1.15:
        return "WASTE"
    if raw_state == "ACTIVE" and kw_est < machine.baseline_idle_kw * 1.5:
        return "IDLE"
    return raw_state


async def recent_current_history(db: AsyncSession, machine_id: UUID) -> list[float]:
    """Past current samples for GMM / drift features (excludes newest if already written)."""
    result = await db.execute(
        select(Telemetry.i_rms_a)
        .where(Telemetry.machine_id == machine_id)
        .order_by(Telemetry.time.desc())
        .limit(16)
    )
    newest_first = list(result.scalars().all())
    return list(reversed(newest_first[1:]))


async def _recent_history(db: AsyncSession, machine_id: UUID) -> list[float]:
    hist = await recent_current_history(db, machine_id)
    return hist[-2:]


def _waste_threshold_seconds(meta: dict) -> float:
    settings = get_settings()
    if settings.pulse_waste_seconds is not None:
        return float(settings.pulse_waste_seconds)
    waste = meta.get("waste_detection") or {}
    if waste.get("enabled"):
        return float(waste.get("duration_seconds", 300))
    return 0.0


async def _classify(
    db: AsyncSession,
    machine: Machine,
    i_rms_a: float,
    kw_est: float,
    latest: MachineLatest | None,
    now: datetime,
) -> tuple[str, float, str]:
    gmm_id = gmm_machine_id(machine.machine_type, machine.name)
    # Live CT on laptop/charger is shop-floor amp range — use rules, not charger GMM.
    charger_live_ct = gmm_id == "laptop_charger_01" and i_rms_a > 0.5
    if gmm_id and gmm_available() and not charger_live_ct:
        try:
            history = await _recent_history(db, machine.id)
            instant, confidence, version, meta = predict_gmm_instant(gmm_id, i_rms_a, history)
            if instant == "IDLE":
                refined = refine_waste("IDLE", kw_est, machine)
                if refined == "WASTE":
                    threshold = _waste_threshold_seconds(meta)
                    if threshold <= 0:
                        threshold = float(get_settings().pulse_waste_seconds or 60)
                    if latest and latest.state in ("IDLE", "WASTE") and latest.state_since:
                        since = latest.state_since
                        if since.tzinfo is None:
                            since = since.replace(tzinfo=UTC)
                        if (now - since).total_seconds() >= threshold:
                            instant = "WASTE"
                    elif threshold <= 0:
                        instant = "WASTE"
            return instant, confidence, version
        except Exception:
            pass

    raw = classify_current(i_rms_a, machine)
    candidate = refine_waste(raw, kw_est, machine)
    confidence = 0.85 if candidate == "WASTE" else 0.95
    return candidate, confidence, "rules-v1"


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
    now = now or datetime.now(UTC)
    result = await db.execute(select(MachineLatest).where(MachineLatest.machine_id == machine.id))
    latest = result.scalar_one_or_none()

    candidate, confidence, version = await _classify(db, machine, i_rms_a, kw_est, latest, now)

    if latest is None:
        return candidate, confidence, True

    current = latest.state or "OFF"
    if candidate == current:
        latest.pending_state = None
        latest.pending_since = None
        latest.model_version = version
        return current, latest.state_confidence or confidence, False

    if latest.pending_state != candidate:
        latest.pending_state = candidate
        latest.pending_since = now
        latest.model_version = version
        return current, latest.state_confidence or confidence, False

    pending_since = latest.pending_since or now
    if pending_since.tzinfo is None:
        pending_since = pending_since.replace(tzinfo=UTC)
    if now - pending_since < timedelta(seconds=DEBOUNCE_SECONDS):
        return current, latest.state_confidence or confidence, False

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
            model_version=version,
            started_at=now,
        )
    )
    latest.state = candidate
    latest.state_confidence = confidence
    latest.state_since = now
    latest.pending_state = None
    latest.pending_since = None
    latest.model_version = version
    return candidate, confidence, True


def residual_waste_kw(kw_est: float, state: str, machine: Machine) -> float:
    if state == "WASTE":
        return max(0.0, kw_est - machine.baseline_idle_kw * 0.25)
    if state == "IDLE":
        return max(0.0, kw_est - machine.baseline_idle_kw)
    return 0.0
