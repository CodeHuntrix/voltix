"""Waste ranking: CS Layer 4 — primary order by qualified ₹/hr."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Machine, MachineLatest
from app.schemas import WasteRankItem

RULE_VERSION = "rules-ranker-v1"


def _reason_code(state: str, inr_per_hr: float, duration_min: float) -> str:
    if state == "WASTE" and inr_per_hr > 0:
        return "RANK_WASTE_COST_RATE"
    if state == "IDLE" and inr_per_hr > 0:
        return "RANK_IDLE_RESIDUAL"
    if state in ("WASTE", "IDLE"):
        return "RANK_QUALIFIED_LOW_COST"
    return "RANK_NOT_QUALIFIED"


def _explain(name: str, state: str, inr_per_hr: float, duration_min: float) -> str:
    if state == "WASTE":
        return (
            f"{name} is in WASTE at ~₹{inr_per_hr:.0f}/hr "
            f"for {duration_min:.0f} min — highest avoidable cost rate first."
        )
    if state == "IDLE":
        return (
            f"{name} is IDLE with residual ~₹{inr_per_hr:.0f}/hr "
            f"for {duration_min:.0f} min."
        )
    return f"{name} is not in a qualifying nonproductive state."


def _suggested_action(state: str, eligible: bool) -> str:
    if state == "WASTE" and eligible:
        return "Review AutoCut approval for this load"
    if state == "WASTE":
        return "Investigate idle waste; AutoCut not eligible"
    if state == "IDLE":
        return "Confirm whether load should be off or in standby"
    return "Monitor"


async def rank_site_waste(db: AsyncSession, site_id: UUID) -> list[WasteRankItem]:
    result = await db.execute(
        select(Machine, MachineLatest)
        .outerjoin(MachineLatest, MachineLatest.machine_id == Machine.id)
        .where(Machine.site_id == site_id)
    )
    rows = result.all()
    items: list[WasteRankItem] = []
    now = datetime.now(UTC)

    for machine, latest in rows:
        if latest is None:
            continue
        state = latest.state or "OFF"
        if state not in ("WASTE", "IDLE"):
            continue

        waste_kw = float(latest.waste_kw or 0.0)
        if state == "IDLE" and waste_kw <= 0:
            continue

        state_since = latest.state_since or latest.time
        if state_since and state_since.tzinfo is None:
            state_since = state_since.replace(tzinfo=UTC)
        duration_min = (
            max(0.0, (now - state_since).total_seconds() / 60.0) if state_since else 0.0
        )
        waste_kwh = waste_kw * (duration_min / 60.0)
        waste_inr = waste_kwh * machine.tariff_inr_per_kwh
        inr_per_hr = waste_kw * machine.tariff_inr_per_kwh
        eligible = bool(machine.eligible_autocut)
        autocut = (
            "eligible"
            if eligible and state == "WASTE"
            else ("denied_not_waste" if eligible else "denied_not_whitelisted")
        )

        items.append(
            WasteRankItem(
                machine_id=machine.id,
                name=machine.name,
                score=round(inr_per_hr, 2),
                waste_kwh=round(waste_kwh, 3),
                waste_inr=round(waste_inr, 2),
                waste_inr_per_hr=round(inr_per_hr, 2),
                duration_min=round(duration_min, 1),
                state=state,
                rank=0,
                primary_metric="waste_inr_per_hr",
                explain=_explain(machine.name, state, inr_per_hr, duration_min),
                reason_code=_reason_code(state, inr_per_hr, duration_min),
                suggested_action=_suggested_action(state, eligible),
                autocut_annotation=autocut,
                rule_version=RULE_VERSION,
            )
        )

    # CS VII.4: ₹/hr → duration → waste_kw → stable machine id
    items.sort(
        key=lambda x: (
            -x.waste_inr_per_hr,
            -x.duration_min,
            -x.waste_kwh,
            str(x.machine_id),
        )
    )
    for i, item in enumerate(items, start=1):
        item.rank = i
    return items
