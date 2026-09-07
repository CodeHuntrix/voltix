export type AlertRow = {
  id: string;
  acknowledged?: boolean;
  alert_type?: string;
  machine_id?: string;
  created_at: string;
  title?: string;
  message?: string;
  severity?: string;
};

export function visibleAlerts<T extends AlertRow>(
  alerts: T[],
  live: { machine_id: string; last_seen?: string | null; state?: string }[],
  limit?: number,
): T[] {
  const onlineIds = new Set(
    live
      .filter((m) => {
        if (!m.last_seen) return false;
        return Date.now() - new Date(m.last_seen).getTime() < 45_000;
      })
      .map((m) => m.machine_id),
  );
  const liveById = new Map(live.map((m) => [m.machine_id, m]));
  const seen = new Set<string>();
  const out = alerts
    .slice()
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .filter((a) => {
      if (a.acknowledged) return false;
      const machine = a.machine_id ? liveById.get(a.machine_id) : undefined;
      if (a.alert_type === "offline" && a.machine_id && onlineIds.has(a.machine_id)) {
        return false;
      }
      if (a.alert_type === "waste" && machine && machine.state !== "WASTE") {
        return false;
      }
      if (a.alert_type === "drift" && machine && machine.state !== "ACTIVE") {
        return false;
      }
      const key = `${a.alert_type}:${a.machine_id ?? "site"}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  return typeof limit === "number" ? out.slice(0, limit) : out;
}
