from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import (
    assert_role,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models import (
    Alert,
    AutocutCommand,
    AuditLog,
    Device,
    Machine,
    MachineLatest,
    MachineStateEvent,
    Membership,
    MvBaseline,
    MvReport,
    Organization,
    Site,
    Telemetry,
    User,
)
from app.schemas import (
    AlertOut,
    AutocutAck,
    AutocutCreate,
    AutocutDecision,
    AutocutOut,
    DeviceCreate,
    DeviceOut,
    DevicePairRequest,
    EdgeCommandOut,
    IngestBatch,
    LoginRequest,
    MachineCreate,
    MachineLiveSnapshot,
    MachineOut,
    MachineUpdate,
    MvBaselineCreate,
    MvBaselineOut,
    MvReportCreate,
    MvReportOut,
    OrgCreate,
    OrgOut,
    PushTokenUpdate,
    RefreshRequest,
    SiteCreate,
    SiteOut,
    StateEventOut,
    TokenPair,
    UserOut,
    WasteRankItem,
)
from app.services.alerts import maybe_create_offline_alert, maybe_create_waste_alert
from app.services.pulse import apply_pulse, residual_waste_kw
from app.services.ranker import rank_site_waste
from app.services.ws import ws_manager

router = APIRouter()
settings = get_settings()


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[{"org_id": str(m.org_id), "role": m.role} for m in user.memberships],
    )


async def _audit(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_id: UUID | None = None,
    org_id: UUID | None = None,
    detail: str | None = None,
) -> None:
    db.add(
        AuditLog(
            org_id=org_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=detail,
        )
    )


async def _site_or_404(db: AsyncSession, site_id: UUID) -> Site:
    site = await db.get(Site, site_id)
    if not site:
        raise HTTPException(404, "Site not found")
    return site


# ---- Auth ----
@router.post("/auth/login", response_model=TokenPair)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    result = await db.execute(
        select(User).where(User.email == body.email.lower()).options(selectinload(User.memberships))
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/auth/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Invalid token type")
        user_id = UUID(payload["sub"])
    except Exception as exc:
        raise HTTPException(401, "Invalid refresh token") from exc
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/auth/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)


@router.put("/auth/push-token")
async def update_push_token(
    body: PushTokenUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user.push_token = body.push_token
    await db.commit()
    return {"ok": True}


# ---- Orgs / sites / machines ----
@router.post("/orgs", response_model=OrgOut)
async def create_org(
    body: OrgCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    existing = await db.execute(select(Organization).where(Organization.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Slug taken")
    org = Organization(name=body.name, slug=body.slug)
    db.add(org)
    await db.flush()
    db.add(Membership(user_id=user.id, org_id=org.id, role="owner"))
    await _audit(db, "org.create", "organization", str(org.id), user.id, org.id)
    await db.commit()
    await db.refresh(org)
    return org


@router.get("/orgs", response_model=list[OrgOut])
async def list_orgs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Organization]:
    result = await db.execute(
        select(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(Membership.user_id == user.id)
    )
    return list(result.scalars().all())


@router.post("/orgs/{org_id}/sites", response_model=SiteOut)
async def create_site(
    org_id: UUID,
    body: SiteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Site:
    assert_role(user, org_id, "owner")
    site = Site(org_id=org_id, name=body.name, timezone=body.timezone)
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return site


@router.get("/orgs/{org_id}/sites", response_model=list[SiteOut])
async def list_sites(
    org_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Site]:
    assert_role(user, org_id, "technician")
    result = await db.execute(select(Site).where(Site.org_id == org_id))
    return list(result.scalars().all())


@router.get("/sites/{site_id}", response_model=SiteOut)
async def get_site(
    site_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Site:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "technician")
    return site


@router.post("/sites/{site_id}/machines", response_model=MachineOut)
async def create_machine(
    site_id: UUID,
    body: MachineCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Machine:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "supervisor")
    machine = Machine(site_id=site_id, **body.model_dump())
    db.add(machine)
    await db.flush()
    db.add(
        MachineLatest(
            machine_id=machine.id,
            time=datetime.now(UTC),
            i_rms_a=0.0,
            v_est=machine.v_nominal,
            kw_est=0.0,
            temp_c=None,
            device_id=machine.device_id or "unpaired",
            state="OFF",
            state_since=datetime.now(UTC),
        )
    )
    await db.commit()
    await db.refresh(machine)
    return machine


@router.get("/sites/{site_id}/machines", response_model=list[MachineOut])
async def list_machines(
    site_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Machine]:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "technician")
    result = await db.execute(select(Machine).where(Machine.site_id == site_id))
    return list(result.scalars().all())


@router.patch("/machines/{machine_id}", response_model=MachineOut)
async def update_machine(
    machine_id: UUID,
    body: MachineUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Machine:
    machine = await db.get(Machine, machine_id)
    if not machine:
        raise HTTPException(404, "Machine not found")
    site = await _site_or_404(db, machine.site_id)
    assert_role(user, site.org_id, "supervisor")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(machine, k, v)
    await db.commit()
    await db.refresh(machine)
    return machine


@router.post("/sites/{site_id}/devices", response_model=DeviceOut)
async def create_device(
    site_id: UUID,
    body: DeviceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Device:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "supervisor")
    device = Device(site_id=site_id, esp32_id=body.esp32_id, pairing_code=body.pairing_code)
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.post("/sites/{site_id}/devices/pair", response_model=DeviceOut)
async def pair_device(
    site_id: UUID,
    body: DevicePairRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Device:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "supervisor")
    result = await db.execute(
        select(Device).where(Device.site_id == site_id, Device.esp32_id == body.esp32_id)
    )
    device = result.scalar_one_or_none()
    if not device or device.pairing_code != body.pairing_code:
        raise HTTPException(400, "Invalid pairing")
    if body.machine_id:
        machine = await db.get(Machine, body.machine_id)
        if not machine or machine.site_id != site_id:
            raise HTTPException(400, "Machine not on site")
        machine.device_id = body.esp32_id
    device.last_seen = datetime.now(UTC)
    await _audit(db, "device.pair", "device", str(device.id), user.id, site.org_id)
    await db.commit()
    await db.refresh(device)
    return device


# ---- Ingest ----
async def _verify_edge_key(x_api_key: str | None = Header(default=None)) -> None:
    if x_api_key != settings.edge_ingest_api_key:
        raise HTTPException(401, "Invalid edge API key")


@router.post("/ingest/telemetry")
async def ingest_telemetry(
    body: IngestBatch,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_verify_edge_key),
) -> dict:
    accepted = 0
    site_broadcasts: dict[UUID, list[dict]] = {}

    for point in body.points:
        machine = await db.get(Machine, point.machine_id)
        if not machine:
            continue
        ts = point.ts if point.ts.tzinfo else point.ts.replace(tzinfo=UTC)
        db.add(
            Telemetry(
                time=ts,
                machine_id=point.machine_id,
                i_rms_a=point.i_rms_a,
                v_est=point.v_nominal,
                kw_est=point.kw_est,
                temp_c=point.temp_c,
                device_id=point.device_id,
            )
        )

        result = await db.execute(
            select(MachineLatest).where(MachineLatest.machine_id == point.machine_id)
        )
        latest = result.scalar_one_or_none()
        if latest is None:
            latest = MachineLatest(
                machine_id=point.machine_id,
                time=ts,
                i_rms_a=point.i_rms_a,
                v_est=point.v_nominal,
                kw_est=point.kw_est,
                temp_c=point.temp_c,
                device_id=point.device_id,
                state="OFF",
                state_since=ts,
            )
            db.add(latest)
            await db.flush()

        latest.time = ts
        latest.i_rms_a = point.i_rms_a
        latest.v_est = point.v_nominal
        latest.kw_est = point.kw_est
        latest.temp_c = point.temp_c
        latest.device_id = point.device_id

        state, confidence, changed = await apply_pulse(db, machine, point.i_rms_a, point.kw_est, ts)
        waste = residual_waste_kw(point.kw_est, state, machine)
        latest.waste_kw = waste
        latest.state = state
        latest.state_confidence = confidence

        # Device last_seen
        dev = await db.execute(select(Device).where(Device.esp32_id == point.device_id))
        device = dev.scalar_one_or_none()
        if device:
            device.last_seen = ts

        duration_min = 0.0
        if latest.state_since:
            ss = latest.state_since if latest.state_since.tzinfo else latest.state_since.replace(tzinfo=UTC)
            duration_min = max(0.0, (ts - ss).total_seconds() / 60.0)
        waste_inr_hr = waste * machine.tariff_inr_per_kwh
        await maybe_create_waste_alert(db, machine, state, duration_min, waste_inr_hr)

        site_broadcasts.setdefault(machine.site_id, []).append(
            {
                "type": "telemetry",
                "machine_id": str(machine.id),
                "state": state,
                "kw_est": point.kw_est,
                "i_rms_a": point.i_rms_a,
                "waste_kw": waste,
                "changed": changed,
                "ts": ts.isoformat(),
            }
        )
        accepted += 1

    await db.commit()
    for site_id, events in site_broadcasts.items():
        await ws_manager.broadcast(site_id, {"type": "batch", "events": events})
    return {"accepted": accepted}


# ---- Live / intelligence ----
@router.get("/sites/{site_id}/live", response_model=list[MachineLiveSnapshot])
async def site_live(
    site_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MachineLiveSnapshot]:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "technician")
    result = await db.execute(
        select(Machine, MachineLatest)
        .outerjoin(MachineLatest, MachineLatest.machine_id == Machine.id)
        .where(Machine.site_id == site_id)
    )
    out: list[MachineLiveSnapshot] = []
    for machine, latest in result.all():
        await maybe_create_offline_alert(db, machine, latest)
        waste = latest.waste_kw if latest else 0.0
        out.append(
            MachineLiveSnapshot(
                machine_id=machine.id,
                name=machine.name,
                state=(latest.state if latest else "OFF"),
                state_confidence=(latest.state_confidence if latest else 1.0),
                kw_est=(latest.kw_est if latest else 0.0),
                i_rms_a=(latest.i_rms_a if latest else 0.0),
                waste_kw=waste,
                waste_inr_per_hr=waste * machine.tariff_inr_per_kwh,
                last_seen=(latest.time if latest else None),
                model_version=(latest.model_version if latest else settings.model_version),
                eligible_autocut=machine.eligible_autocut,
                cut_policy=machine.cut_policy,
            )
        )
    await db.commit()
    return out


@router.get("/sites/{site_id}/rank", response_model=list[WasteRankItem])
async def site_rank(
    site_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WasteRankItem]:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "technician")
    return await rank_site_waste(db, site_id)


@router.get("/machines/{machine_id}/telemetry")
async def machine_telemetry(
    machine_id: UUID,
    limit: int = 120,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    machine = await db.get(Machine, machine_id)
    if not machine:
        raise HTTPException(404, "Machine not found")
    site = await _site_or_404(db, machine.site_id)
    assert_role(user, site.org_id, "technician")
    result = await db.execute(
        select(Telemetry)
        .where(Telemetry.machine_id == machine_id)
        .order_by(Telemetry.time.desc())
        .limit(min(limit, 1000))
    )
    rows = list(reversed(result.scalars().all()))
    return [
        {
            "time": r.time.isoformat(),
            "i_rms_a": r.i_rms_a,
            "kw_est": r.kw_est,
            "temp_c": r.temp_c,
        }
        for r in rows
    ]


@router.get("/machines/{machine_id}/states", response_model=list[StateEventOut])
async def machine_states(
    machine_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MachineStateEvent]:
    machine = await db.get(Machine, machine_id)
    if not machine:
        raise HTTPException(404, "Machine not found")
    site = await _site_or_404(db, machine.site_id)
    assert_role(user, site.org_id, "technician")
    result = await db.execute(
        select(MachineStateEvent)
        .where(MachineStateEvent.machine_id == machine_id)
        .order_by(MachineStateEvent.started_at.desc())
        .limit(50)
    )
    return list(result.scalars().all())


# ---- Alerts ----
@router.get("/sites/{site_id}/alerts", response_model=list[AlertOut])
async def list_alerts(
    site_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Alert]:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "technician")
    result = await db.execute(
        select(Alert).where(Alert.site_id == site_id).order_by(Alert.created_at.desc()).limit(100)
    )
    return list(result.scalars().all())


@router.post("/alerts/{alert_id}/ack", response_model=AlertOut)
async def ack_alert(
    alert_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Alert:
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    site = await _site_or_404(db, alert.site_id)
    assert_role(user, site.org_id, "technician")
    alert.acknowledged = True
    await db.commit()
    await db.refresh(alert)
    return alert


# ---- AutoCut ----
@router.post("/autocut", response_model=AutocutOut)
async def create_autocut(
    body: AutocutCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AutocutCommand:
    machine = await db.get(Machine, body.machine_id)
    if not machine:
        raise HTTPException(404, "Machine not found")
    site = await _site_or_404(db, machine.site_id)
    assert_role(user, site.org_id, "supervisor")
    if not machine.eligible_autocut:
        raise HTTPException(400, "Machine not eligible for AutoCut (≤10A relay loads only)")

    status_val = "pending"
    if machine.cut_policy == "auto":
        status_val = "approved"
    elif machine.cut_policy == "suggest":
        status_val = "pending"

    cmd = AutocutCommand(
        machine_id=machine.id,
        site_id=machine.site_id,
        status=status_val,
        reason=body.reason,
        requested_by=user.id,
        decided_by=user.id if status_val == "approved" else None,
        decided_at=datetime.now(UTC) if status_val == "approved" else None,
    )
    db.add(cmd)
    await _audit(db, "autocut.create", "autocut", "pending", user.id, site.org_id, body.reason)
    await db.commit()
    await db.refresh(cmd)
    await ws_manager.broadcast(
        machine.site_id,
        {"type": "autocut", "id": str(cmd.id), "status": cmd.status, "machine_id": str(machine.id)},
    )
    return AutocutOut.model_validate(cmd)


@router.get("/sites/{site_id}/autocut", response_model=list[AutocutOut])
async def list_autocut(
    site_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AutocutOut]:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "technician")
    result = await db.execute(
        select(AutocutCommand)
        .where(AutocutCommand.site_id == site_id)
        .order_by(AutocutCommand.created_at.desc())
        .limit(50)
    )
    return [AutocutOut.model_validate(c) for c in result.scalars().all()]


@router.post("/autocut/{command_id}/decide", response_model=AutocutOut)
async def decide_autocut(
    command_id: UUID,
    body: AutocutDecision,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AutocutOut:
    cmd = await db.get(AutocutCommand, command_id)
    if not cmd:
        raise HTTPException(404, "Command not found")
    site = await _site_or_404(db, cmd.site_id)
    assert_role(user, site.org_id, "supervisor")
    if cmd.status not in ("pending",):
        raise HTTPException(400, f"Cannot decide status={cmd.status}")
    cmd.status = "approved" if body.approve else "denied"
    cmd.decided_by = user.id
    cmd.decided_at = datetime.now(UTC)
    await _audit(
        db,
        "autocut.decide",
        "autocut",
        str(cmd.id),
        user.id,
        site.org_id,
        "approved" if body.approve else "denied",
    )
    await db.commit()
    await db.refresh(cmd)
    await ws_manager.broadcast(
        cmd.site_id, {"type": "autocut", "id": str(cmd.id), "status": cmd.status}
    )
    return AutocutOut.model_validate(cmd)


@router.get("/edge/commands", response_model=list[EdgeCommandOut])
async def edge_poll_commands(
    site_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_verify_edge_key),
) -> list[EdgeCommandOut]:
    q = select(AutocutCommand).where(AutocutCommand.status == "approved")
    if site_id:
        q = q.where(AutocutCommand.site_id == site_id)
    result = await db.execute(q.order_by(AutocutCommand.created_at.asc()).limit(20))
    cmds = list(result.scalars().all())
    out: list[EdgeCommandOut] = []
    for cmd in cmds:
        machine = await db.get(Machine, cmd.machine_id)
        cmd.status = "sent"
        cmd.sent_at = datetime.now(UTC)
        out.append(
            EdgeCommandOut(
                id=cmd.id,
                machine_id=cmd.machine_id,
                device_id=machine.device_id if machine else None,
                action="cut",
                status="sent",
            )
        )
    await db.commit()
    return out


@router.post("/edge/commands/ack")
async def edge_ack_command(
    body: AutocutAck,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_verify_edge_key),
) -> dict:
    cmd = await db.get(AutocutCommand, body.command_id)
    if not cmd:
        raise HTTPException(404, "Command not found")
    cmd.status = "acked" if body.success else "failed"
    cmd.acked_at = datetime.now(UTC)
    cmd.edge_payload = body.detail
    await _audit(db, "autocut.ack", "autocut", str(cmd.id), None, None, body.detail)
    await db.commit()
    await ws_manager.broadcast(
        cmd.site_id, {"type": "autocut", "id": str(cmd.id), "status": cmd.status}
    )
    return {"ok": True}


# ---- M&V ----
async def _sum_kwh(db: AsyncSession, site_id: UUID, start: datetime, end: datetime) -> float:
    # Approximate energy from telemetry avg kw * hours (honest CT estimate)
    result = await db.execute(
        text(
            """
            SELECT COALESCE(AVG(t.kw_est), 0) AS avg_kw,
                   EXTRACT(EPOCH FROM (:end_ts - :start_ts)) / 3600.0 AS hours
            FROM telemetry t
            JOIN machines m ON m.id = t.machine_id
            WHERE m.site_id = :site_id
              AND t.time >= :start_ts AND t.time < :end_ts
            """
        ),
        {"site_id": site_id, "start_ts": start, "end_ts": end},
    )
    row = result.mappings().one()
    return float(row["avg_kw"] or 0) * float(row["hours"] or 0)


@router.post("/sites/{site_id}/mv/baselines", response_model=MvBaselineOut)
async def create_baseline(
    site_id: UUID,
    body: MvBaselineCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MvBaseline:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "supervisor")
    kwh = body.baseline_kwh
    if kwh is None:
        kwh = await _sum_kwh(db, site_id, body.start_at, body.end_at)
    bl = MvBaseline(
        site_id=site_id,
        name=body.name,
        start_at=body.start_at,
        end_at=body.end_at,
        baseline_kwh=kwh,
        notes=body.notes,
    )
    db.add(bl)
    await db.commit()
    await db.refresh(bl)
    return bl


@router.get("/sites/{site_id}/mv/baselines", response_model=list[MvBaselineOut])
async def list_baselines(
    site_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MvBaseline]:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "technician")
    result = await db.execute(select(MvBaseline).where(MvBaseline.site_id == site_id))
    return list(result.scalars().all())


@router.post("/sites/{site_id}/mv/reports", response_model=MvReportOut)
async def create_mv_report(
    site_id: UUID,
    body: MvReportCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MvReport:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "supervisor")
    bl = await db.get(MvBaseline, body.baseline_id)
    if not bl or bl.site_id != site_id:
        raise HTTPException(404, "Baseline not found")
    intervention_kwh = await _sum_kwh(db, site_id, body.intervention_start, body.intervention_end)
    # Normalize baseline to intervention duration
    bl_hours = max((bl.end_at - bl.start_at).total_seconds() / 3600.0, 0.001)
    int_hours = max(
        (body.intervention_end - body.intervention_start).total_seconds() / 3600.0, 0.001
    )
    expected = bl.baseline_kwh * (int_hours / bl_hours)
    savings = max(0.0, expected - intervention_kwh)
    report = MvReport(
        site_id=site_id,
        baseline_id=bl.id,
        intervention_start=body.intervention_start,
        intervention_end=body.intervention_end,
        intervention_kwh=intervention_kwh,
        savings_kwh=savings,
        savings_inr=savings * body.tariff_inr_per_kwh,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/sites/{site_id}/mv/reports", response_model=list[MvReportOut])
async def list_mv_reports(
    site_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MvReport]:
    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "technician")
    result = await db.execute(
        select(MvReport).where(MvReport.site_id == site_id).order_by(MvReport.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/sites/{site_id}/mv/export.csv")
async def export_mv_csv(
    site_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi.responses import PlainTextResponse

    site = await _site_or_404(db, site_id)
    assert_role(user, site.org_id, "technician")
    result = await db.execute(select(MvReport).where(MvReport.site_id == site_id))
    lines = [
        "report_id,baseline_id,intervention_start,intervention_end,intervention_kwh,savings_kwh,savings_inr"
    ]
    for r in result.scalars().all():
        lines.append(
            ",".join(
                [
                    str(r.id),
                    str(r.baseline_id),
                    r.intervention_start.isoformat(),
                    r.intervention_end.isoformat(),
                    f"{r.intervention_kwh:.4f}",
                    f"{r.savings_kwh:.4f}",
                    f"{r.savings_inr:.2f}",
                ]
            )
        )
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/csv")
