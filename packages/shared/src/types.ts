/** Shared enums and DTOs aligned with API Pydantic models. */

export type Role = "owner" | "supervisor" | "technician";

export type MachineState = "OFF" | "ACTIVE" | "IDLE" | "WASTE";

export type CutPolicy = "suggest" | "require_ack" | "auto";

export type AlertSeverity = "info" | "warning" | "critical";

export type AlertType = "waste" | "offline" | "drift";

export type AutocutStatus =
  | "pending"
  | "approved"
  | "denied"
  | "sent"
  | "acked"
  | "failed"
  | "cancelled";

export interface Organization {
  id: string;
  name: string;
  slug: string;
}

export interface Site {
  id: string;
  org_id: string;
  name: string;
  timezone: string;
}

export interface Machine {
  id: string;
  site_id: string;
  name: string;
  machine_type: string;
  v_nominal: number;
  pf_assumed: number;
  cut_policy: CutPolicy;
  tariff_inr_per_kwh: number;
  device_id: string | null;
  eligible_autocut: boolean;
}

export interface TelemetryPoint {
  time: string;
  machine_id: string;
  i_rms_a: number;
  v_est: number;
  kw_est: number;
  temp_c: number | null;
  device_id: string;
}

export interface IngestPayload {
  device_id: string;
  machine_id: string;
  ts: string;
  i_rms_a: number;
  v_nominal: number;
  pf_assumed: number;
  kw_est: number;
  temp_c?: number | null;
}

export interface MachineLiveSnapshot {
  machine_id: string;
  name: string;
  state: MachineState;
  state_confidence: number;
  kw_est: number;
  i_rms_a: number;
  waste_kw: number;
  waste_inr_per_hr: number;
  last_seen: string | null;
  model_version: string;
}

export interface WasteRankItem {
  machine_id: string;
  name: string;
  score: number;
  waste_kwh: number;
  waste_inr: number;
  duration_min: number;
  state: MachineState;
}

export interface Alert {
  id: string;
  site_id: string;
  machine_id: string | null;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  acknowledged: boolean;
  created_at: string;
}

export interface AutocutCommand {
  id: string;
  machine_id: string;
  status: AutocutStatus;
  reason: string;
  requested_by: string | null;
  created_at: string;
  acked_at: string | null;
}

export const MACHINE_STATES: MachineState[] = ["OFF", "ACTIVE", "IDLE", "WASTE"];
export const ROLES: Role[] = ["owner", "supervisor", "technician"];
