import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link } from "@tanstack/react-router";
import { CardSkeleton } from "@/components/CardSkeleton";
import { EmptyState, InlineError } from "@/components/EmptyState";
import { MachineCard } from "@/components/MachineCard";
import { PageHeader } from "@/components/PageHeader";
import { Shell } from "@/components/Shell";
import { StatusBadge } from "@/components/StatusBadge";
import { visibleAlerts } from "@/lib/alerts";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
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
      <PageHeader title="Machines" description="Live spend on the floor" />

      <div className="grid gap-6 xl:grid-cols-[1fr_300px]">
        <div>
          {live.isLoading && !(live.data ?? []).length && (
            <div
              className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
              aria-busy="true"
              aria-label="Loading machines"
            >
              {Array.from({ length: 3 }, (_, i) => (
                <CardSkeleton key={i} />
              ))}
            </div>
          )}
          {live.isError && !(live.data ?? []).length && (
            <InlineError>Failed to load live data</InlineError>
          )}

          {!!(live.data ?? []).length && (
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
          )}

          {!live.isLoading && !live.isError && !(live.data ?? []).length && (
            <EmptyState>
              No machines yet —{" "}
              <Link to="/onboarding" className="text-sky-300 hover:text-white">
                add them in setup
              </Link>
              .
            </EmptyState>
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
                  {r.explain && (
                    <p className="mt-1 text-[11px] leading-snug text-white/35">{r.explain}</p>
                  )}
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
                <StatusBadge severity={a.severity} className="mt-0.5 rounded-full">
                  {a.alert_type}
                </StatusBadge>
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
