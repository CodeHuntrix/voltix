"""Waste ranking: score by ₹ impact + kWh + duration."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Machine, MachineLatest, Site
from app.schemas import WasteRankItem


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
        waste_kw = latest.waste_kw or 0.0
        state_since = latest.state_since or latest.time
        if state_since and state_since.tzinfo is None:
            state_since = state_since.replace(tzinfo=UTC)
        duration_min = max(0.0, (now - state_since).total_seconds() / 60.0) if state_since else 0.0
        if state not in ("WASTE", "IDLE"):
            waste_kw = 0.0
            # still include low score for visibility when idle
            if state != "IDLE":
                continue

        waste_kwh = waste_kw * (duration_min / 60.0)
        waste_inr = waste_kwh * machine.tariff_inr_per_kwh
        # Score: prioritize ₹/hr + sustained duration
        inr_per_hr = waste_kw * machine.tariff_inr_per_kwh
        score = inr_per_hr * 10.0 + waste_kwh * 5.0 + min(duration_min, 120) * 0.5
        if state == "WASTE":
            score *= 1.5

        items.append(
            WasteRankItem(
                machine_id=machine.id,
                name=machine.name,
                score=round(score, 2),
                waste_kwh=round(waste_kwh, 3),
                waste_inr=round(waste_inr, 2),
                duration_min=round(duration_min, 1),
                state=state,
            )
        )

    items.sort(key=lambda x: x.score, reverse=True)
    return items
