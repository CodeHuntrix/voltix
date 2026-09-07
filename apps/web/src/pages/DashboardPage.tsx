import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Shell } from "@/components/Shell";
import { MachineCard } from "@/components/MachineCard";
import { visibleAlerts } from "@/lib/alerts";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { stateBadgeClass } from "@/lib/machineArt";
import { formatInr, formatMinutes } from "@/lib/money";

export function DashboardPage() {
  const token = useAuth((s) => s.accessToken)!;
  const siteId = useAuth((s) => s.siteId)!;

  const live = useQuery({
    queryKey: ["live", siteId],
    queryFn: () => api.live(token, siteId),
    refetchInterval: 4000,
  });
  const rank = useQuery({
    queryKey: ["rank", siteId],
    queryFn: () => api.rank(token, siteId),
    refetchInterval: 5000,
  });
  const alerts = useQuery({
    queryKey: ["alerts", siteId],
    queryFn: () => api.alerts(token, siteId),
    refetchInterval: 8000,
  });

  useEffect(() => {
    let opened = false;
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const host = import.meta.env.VITE_WS_HOST ?? location.host;
    const ws = new WebSocket(
      `${proto}://${host}/ws/sites/${siteId}?token=${token}`,
    );
    ws.onopen = () => {
      opened = true;
    };
    ws.onmessage = () => {
      live.refetch();
      rank.refetch();
      alerts.refetch();
    };
    return () => {
      if (opened || ws.readyState === WebSocket.OPEN) {
        ws.close();
        return;
      }
      ws.addEventListener("open", () => ws.close());
    };
  }, [siteId, token]);

  const openAlerts = visibleAlerts(alerts.data ?? [], live.data ?? [], 5);

  return (
    <Shell>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-white">
            Machines
          </h1>
          <p className="mt-1 text-sm text-white/45">Live spend on the floor</p>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_300px]">
        <div>
          {live.isLoading && <p className="text-white/50">Loading machines…</p>}
          {live.isError && !(live.data ?? []).length && (
            <p className="text-red-400">Failed to load live data</p>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {(live.data ?? []).map((m: any) => (
              <MachineCard
                key={m.machine_id}
                machineId={m.machine_id}
                name={m.name}
                machineType={m.machine_type}
                state={m.state}
                kwEst={m.kw_est}
                iRmsA={m.i_rms_a}
                wasteInrPerHr={m.waste_inr_per_hr}
                inrPerHr={m.inr_per_hr}
                tariffInrPerKwh={m.tariff_inr_per_kwh}
                eligibleAutocut={m.eligible_autocut}
                modelVersion={m.model_version}
              />
            ))}
          </div>

          {!live.isLoading && !(live.data ?? []).length && (
            <p className="mt-6 text-white/45">
              No machines yet — add them from setup.
            </p>
          )}
        </div>

        <aside className="space-y-4">
          <div className="glass-card rounded-3xl p-5">
            <p className="mb-3 text-sm font-semibold text-white">Waste rank</p>
            {(rank.data ?? []).slice(0, 3).map((r: any) => {
              const perHr =
                typeof r.waste_inr_per_hr === "number"
                  ? r.waste_inr_per_hr
                  : r.duration_min > 0
                    ? r.waste_inr / (r.duration_min / 60)
                    : 0;
              return (
                <div
                  key={r.machine_id}
                  className="border-t border-white/10 py-3 first:border-t-0 first:pt-0"
                >
                  <p className="text-sm font-medium text-white">{r.name}</p>
                  <p className="mt-1 text-xs text-white/45">
                    {r.state} · {formatMinutes(r.duration_min)} ·{" "}
                    {formatInr(perHr)}/hr
                  </p>
                </div>
              );
            })}
            {!(rank.data ?? []).length && (
              <p className="text-xs text-white/40">
                No ranked waste yet — wait for IDLE/WASTE.
              </p>
            )}
          </div>

          <div className="glass-card rounded-3xl p-5">
            <p className="mb-3 text-sm font-semibold text-white">Alerts</p>
            {openAlerts.map((a: any) => (
              <div
                key={a.id}
                className="flex items-start gap-2 border-t border-white/10 py-3 first:border-t-0 first:pt-0"
              >
                <span
                  className={`mt-0.5 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${stateBadgeClass(a.severity === "critical" ? "WASTE" : "IDLE")}`}
                >
                  {a.alert_type}
                </span>
                <p className="text-xs text-white/70">{a.title}</p>
              </div>
            ))}
            {!openAlerts.length && (
              <p className="text-xs text-white/40">No open alerts.</p>
            )}
          </div>
        </aside>
      </div>
    </Shell>
  );
}
