/** Maps machine_type → illustration under /machines (drop ChatGPT PNGs here). */
export type MachineArtKey =
  | "compressor"
  | "cnc"
  | "press"
  | "conveyor"
  | "laptop"
  | "motor"
  | "generic";

export function artKeyFromType(machineType?: string | null): MachineArtKey {
  const t = (machineType ?? "generic").toLowerCase();
  if (t.includes("compress")) return "compressor";
  // Dedicated laptop/charger art — never reuse motor / generic factory assets
  if (t.includes("laptop") || t.includes("charger")) return "laptop";
  if (t.includes("cnc") || t.includes("lathe") || t.includes("mill"))
    return "cnc";
  if (t.includes("press")) return "press";
  if (t.includes("convey")) return "conveyor";
  if (
    t.includes("motor") ||
    t.includes("fan") ||
    t.includes("pump") ||
    t.includes("blower")
  )
    return "motor";
  return "generic";
}

/** Prefer PNG (ChatGPT export); SVG placeholders ship until PNGs arrive. */
export function machineArtCandidates(machineType?: string | null): {
  png: string;
  svg: string;
} {
  const key = artKeyFromType(machineType);
  return { png: `/machines/${key}.png`, svg: `/machines/${key}.svg` };
}

export function typeLabel(machineType?: string | null): string {
  switch (artKeyFromType(machineType)) {
    case "compressor":
      return "COMP";
    case "cnc":
      return "CNC";
    case "press":
      return "PRESS";
    case "conveyor":
      return "CONV";
    case "laptop":
      return "LAPTOP";
    case "motor":
      return "MOTOR";
    default:
      return "LOAD";
  }
}

export const MACHINE_STATES = ["ACTIVE", "IDLE", "WASTE", "OFF"] as const;
export type MachineState = (typeof MACHINE_STATES)[number];

/** Shared ACTIVE / IDLE / WASTE / OFF chrome — badges, rails, alert severity. */
export const STATE_TONES: Record<
  MachineState,
  { rail: string; badge: string }
> = {
  ACTIVE: {
    rail: "bg-state-active",
    badge: "bg-state-active/90 text-white",
  },
  IDLE: {
    rail: "bg-state-idle",
    badge: "bg-state-idle/90 text-black",
  },
  WASTE: {
    rail: "bg-state-waste",
    badge: "bg-state-waste/90 text-white",
  },
  OFF: {
    rail: "bg-state-off",
    badge: "bg-state-off/80 text-white",
  },
};

export function normalizeState(state?: string | null): MachineState {
  const key = (state ?? "OFF").toUpperCase();
  return MACHINE_STATES.includes(key as MachineState)
    ? (key as MachineState)
    : "OFF";
}

export function stateRailClass(state: string): string {
  return STATE_TONES[normalizeState(state)].rail;
}

export function stateBadgeClass(state: string): string {
  return STATE_TONES[normalizeState(state)].badge;
}

/** Alert severity shares the same state map: critical → WASTE, else IDLE. */
export function severityToState(severity?: string | null): MachineState {
  return (severity ?? "").toLowerCase() === "critical" ? "WASTE" : "IDLE";
}

export function severityBadgeClass(severity?: string | null): string {
  return stateBadgeClass(severityToState(severity));
}
