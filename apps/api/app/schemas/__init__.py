from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    roles: list[dict]

    model_config = {"from_attributes": True}


class OrgCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=100)


class OrgOut(BaseModel):
    id: UUID
    name: str
    slug: str

    model_config = {"from_attributes": True}


class SiteCreate(BaseModel):
    name: str
    timezone: str = "Asia/Kolkata"


class SiteOut(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    timezone: str

    model_config = {"from_attributes": True}


class MachineCreate(BaseModel):
    name: str
    machine_type: str = "generic"
    v_nominal: float = 230.0
    pf_assumed: float = 0.85
    cut_policy: str = "require_ack"
    tariff_inr_per_kwh: float = 8.5
    device_id: str | None = None
    eligible_autocut: bool = False
    thr_off: float = 0.3
    thr_idle: float = 2.0
    thr_active: float = 5.0
    baseline_idle_kw: float = 0.4


class MachineUpdate(BaseModel):
    name: str | None = None
    cut_policy: str | None = None
    device_id: str | None = None
    eligible_autocut: bool | None = None
    tariff_inr_per_kwh: float | None = None
    thr_off: float | None = None
    thr_idle: float | None = None
    thr_active: float | None = None
    baseline_idle_kw: float | None = None


class MachineOut(BaseModel):
    id: UUID
    site_id: UUID
    name: str
    machine_type: str
    v_nominal: float
    pf_assumed: float
    cut_policy: str
    tariff_inr_per_kwh: float
    device_id: str | None
    eligible_autocut: bool

    model_config = {"from_attributes": True}


class DeviceCreate(BaseModel):
    esp32_id: str
    pairing_code: str | None = None


class DeviceOut(BaseModel):
    id: UUID
    site_id: UUID
    esp32_id: str
    pairing_code: str | None
    last_seen: datetime | None

    model_config = {"from_attributes": True}


class DevicePairRequest(BaseModel):
    esp32_id: str
    pairing_code: str
    machine_id: UUID | None = None


class IngestPoint(BaseModel):
    device_id: str
    machine_id: UUID
    ts: datetime
    i_rms_a: float
    v_nominal: float
    pf_assumed: float
    kw_est: float
    temp_c: float | None = None


class IngestBatch(BaseModel):
    points: list[IngestPoint]


class MachineLiveSnapshot(BaseModel):
    machine_id: UUID
    name: str
    machine_type: str = "generic"
    state: str
    state_confidence: float
    kw_est: float
    i_rms_a: float
    waste_kw: float
    waste_inr_per_hr: float
    inr_per_hr: float = 0.0
    tariff_inr_per_kwh: float = 8.5
    last_seen: datetime | None
    model_version: str
    eligible_autocut: bool
    cut_policy: str


class WasteRankItem(BaseModel):
    machine_id: UUID
    name: str
    score: float
    waste_kwh: float
    waste_inr: float
    waste_inr_per_hr: float = 0.0
    duration_min: float
    state: str


class AlertOut(BaseModel):
    id: UUID
    site_id: UUID
    machine_id: UUID | None
    alert_type: str
    severity: str
    title: str
    message: str
    acknowledged: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AutocutCreate(BaseModel):
    machine_id: UUID
    reason: str


class AutocutDecision(BaseModel):
    approve: bool


class AutocutOut(BaseModel):
    id: UUID
    machine_id: UUID
    site_id: UUID
    status: str
    reason: str
    requested_by: UUID | None
    created_at: datetime
    acked_at: datetime | None
    eligible_load_warning: str = (
        "AutoCut is for eligible loads only (≤10A relay). Verify circuit before actuation."
    )

    model_config = {"from_attributes": True}


class AutocutAck(BaseModel):
    command_id: UUID
    success: bool
    detail: str | None = None


class EdgeCommandOut(BaseModel):
    id: UUID
    machine_id: UUID
    device_id: str | None
    action: str = "cut"
    status: str


class MvBaselineCreate(BaseModel):
    name: str
    start_at: datetime
    end_at: datetime
    baseline_kwh: float | None = None
    notes: str | None = None


class MvBaselineOut(BaseModel):
    id: UUID
    site_id: UUID
    name: str
    start_at: datetime
    end_at: datetime
    baseline_kwh: float
    notes: str | None

    model_config = {"from_attributes": True}


class MvReportCreate(BaseModel):
    baseline_id: UUID
    intervention_start: datetime
    intervention_end: datetime
    tariff_inr_per_kwh: float = 8.5


class MvReportOut(BaseModel):
    id: UUID
    site_id: UUID
    baseline_id: UUID
    intervention_start: datetime
    intervention_end: datetime
    intervention_kwh: float
    savings_kwh: float
    savings_inr: float
    created_at: datetime

    model_config = {"from_attributes": True}


class PushTokenUpdate(BaseModel):
    push_token: str


class StateEventOut(BaseModel):
    id: UUID
    machine_id: UUID
    state: str
    confidence: float
    started_at: datetime
    ended_at: datetime | None
    model_version: str

    model_config = {"from_attributes": True}
