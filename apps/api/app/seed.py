"""Seed demo tenant for SIH demo day."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.db import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models import (
    Device,
    Machine,
    MachineLatest,
    Membership,
    MvBaseline,
    Organization,
    Site,
    User,
)


DEMO_EMAIL = "owner@voltix.demo"
DEMO_PASSWORD = "voltix-demo"


async def seed() -> dict:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        if existing.scalar_one_or_none():
            org = (
                await db.execute(select(Organization).where(Organization.slug == "demo-msme"))
            ).scalar_one()
            site = (await db.execute(select(Site).where(Site.org_id == org.id))).scalar_one()
            await _ensure_laptop(db, site.id)
            await db.commit()
            return {
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD,
                "org_id": str(org.id),
                "site_id": str(site.id),
                "seeded": False,
            }

        org = Organization(name="Demo Auto Components", slug="demo-msme")
        db.add(org)
        await db.flush()

        user = User(
            email=DEMO_EMAIL,
            full_name="Demo Owner",
            hashed_password=hash_password(DEMO_PASSWORD),
        )
        db.add(user)
        await db.flush()
        db.add(Membership(user_id=user.id, org_id=org.id, role="owner"))

        tech = User(
            email="tech@voltix.demo",
            full_name="Floor Technician",
            hashed_password=hash_password(DEMO_PASSWORD),
        )
        db.add(tech)
        await db.flush()
        db.add(Membership(user_id=tech.id, org_id=org.id, role="technician"))

        site = Site(org_id=org.id, name="Plant A — Machining Bay", timezone="Asia/Kolkata")
        db.add(site)
        await db.flush()

        machines_spec = [
            ("CNC Lathe 1", "cnc", "esp32-cnc-01", False, 0.5, 3.0, 8.0, 0.6),
            ("CNC Mill 2", "cnc", "esp32-cnc-02", False, 0.5, 3.0, 8.0, 0.7),
            ("Compressor 2", "compressor", "esp32-comp-02", True, 0.4, 2.5, 12.0, 1.2),
            ("Hydraulic Press", "press", "esp32-press-01", False, 0.3, 2.0, 10.0, 0.5),
            ("Conveyor A", "conveyor", "esp32-conv-01", True, 0.2, 1.0, 4.0, 0.3),
            ("Laptop Demo", "laptop", "esp32-laptop-01", True, 0.02, 0.18, 0.25, 0.04),
        ]

        now = datetime.now(UTC)
        for name, mtype, did, eligible, thr_off, thr_idle, thr_active, baseline in machines_spec:
            m = Machine(
                site_id=site.id,
                name=name,
                machine_type=mtype,
                device_id=did,
                eligible_autocut=eligible,
                cut_policy="require_ack" if eligible else "suggest",
                thr_off=thr_off,
                thr_idle=thr_idle,
                thr_active=thr_active,
                baseline_idle_kw=baseline,
                tariff_inr_per_kwh=8.5,
            )
            db.add(m)
            await db.flush()
            db.add(
                MachineLatest(
                    machine_id=m.id,
                    time=now,
                    i_rms_a=0.0,
                    v_est=230.0,
                    kw_est=0.0,
                    temp_c=32.0,
                    device_id=did,
                    state="OFF",
                    state_since=now,
                )
            )
            db.add(
                Device(
                    site_id=site.id,
                    esp32_id=did,
                    pairing_code="PAIR01",
                    last_seen=now,
                )
            )

        db.add(
            MvBaseline(
                site_id=site.id,
                name="Pre-Voltix week",
                start_at=now - timedelta(days=14),
                end_at=now - timedelta(days=7),
                baseline_kwh=1850.0,
                notes="Fixture baseline for demo M&V",
            )
        )

        await db.commit()
        return {
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "org_id": str(org.id),
            "site_id": str(site.id),
            "seeded": True,
        }


async def _ensure_laptop(db, site_id) -> None:
    found = await db.execute(select(Machine).where(Machine.device_id == "esp32-laptop-01"))
    if found.scalar_one_or_none():
        return
    now = datetime.now(UTC)
    m = Machine(
        site_id=site_id,
        name="Laptop Demo",
        machine_type="laptop",
        device_id="esp32-laptop-01",
        eligible_autocut=True,
        cut_policy="require_ack",
        thr_off=0.02,
        thr_idle=0.18,
        thr_active=0.25,
        baseline_idle_kw=0.04,
        tariff_inr_per_kwh=8.5,
    )
    db.add(m)
    await db.flush()
    db.add(
        MachineLatest(
            machine_id=m.id,
            time=now,
            i_rms_a=0.0,
            v_est=230.0,
            kw_est=0.0,
            temp_c=32.0,
            device_id="esp32-laptop-01",
            state="OFF",
            state_since=now,
        )
    )
    db.add(
        Device(
            site_id=site_id,
            esp32_id="esp32-laptop-01",
            pairing_code="PAIR01",
            last_seen=now,
        )
    )


if __name__ == "__main__":
    info = asyncio.run(seed())
    print(info)
