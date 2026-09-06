"""ARQ worker — offline scans, alert fanout stubs, push hooks."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models import Machine, MachineLatest, User
from app.services.alerts import maybe_create_offline_alert

logger = logging.getLogger("voltix.worker")
settings = get_settings()


async def scan_offline(ctx: dict) -> int:
    created = 0
    async with SessionLocal() as db:
        result = await db.execute(
            select(Machine, MachineLatest).outerjoin(
                MachineLatest, MachineLatest.machine_id == Machine.id
            )
        )
        for machine, latest in result.all():
            alert = await maybe_create_offline_alert(db, machine, latest)
            if alert:
                created += 1
                await _fanout_push_stub(db, alert.title)
        await db.commit()
    logger.info("offline_scan created=%s", created)
    return created


async def _fanout_push_stub(db, title: str) -> None:
    """Expo push hook placeholder — logs tokens that would receive a push."""
    result = await db.execute(select(User).where(User.push_token.is_not(None)))
    for user in result.scalars().all():
        logger.info(
            "expo_push_hook user=%s token=%s title=%s",
            user.email,
            (user.push_token or "")[:16],
            title,
        )


async def startup(ctx: dict) -> None:
    logger.info("voltix worker started")


async def shutdown(ctx: dict) -> None:
    logger.info("voltix worker stopped")


class WorkerSettings:
    functions = [scan_offline]
    cron_jobs = [cron(scan_offline, second={0, 30})]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
