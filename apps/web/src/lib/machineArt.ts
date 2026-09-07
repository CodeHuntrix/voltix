/** Maps machine_type → illustration under /machines (drop ChatGPT PNGs here). */
export type MachineArtKey =
  | "compressor"
  | "cnc"
  | "press"
  | "conveyor"
  | "motor"
  | "generic";

export function artKeyFromType(machineType?: string | null): MachineArtKey {
  const t = (machineType ?? "generic").toLowerCase();
  if (t.includes("compress")) return "compressor";
  if (t.includes("laptop") || t.includes("charger")) return "motor";
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
    case "motor":
      return (machineType ?? "").toLowerCase().includes("laptop") ||
        (machineType ?? "").toLowerCase().includes("charger")
        ? "LAPTOP"
        : "MOTOR";
    default:
      return "LOAD";
  }
}

export function stateBadgeClass(state: string): string {
  switch (state) {
    case "ACTIVE":
      return "bg-emerald-500/90 text-white";
    case "IDLE":
      return "bg-amber-500/90 text-black";
    case "WASTE":
      return "bg-red-500/90 text-white";
    default:
      return "bg-slate-500/80 text-white";
  }
}
