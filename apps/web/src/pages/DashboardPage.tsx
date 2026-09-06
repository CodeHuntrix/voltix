import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Shell } from "@/components/Shell";
import { api, stateColor } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export function DashboardPage() {
  const token = useAuth((s) => s.accessToken)!;
  const siteId = useAuth((s) => s.siteId)!;
  const [wsNote, setWsNote] = useState("connecting…");

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

  useEffect(() => {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const host = import.meta.env.VITE_WS_HOST ?? location.host;
    const ws = new WebSocket(`${proto}://${host}/ws/sites/${siteId}?token=${token}`);
    ws.onopen = () => setWsNote("live");
    ws.onmessage = () => {
      live.refetch();
      rank.refetch();
    };
    ws.onclose = () => setWsNote("polling");
    return () => ws.close();
  }, [siteId, token]);

  return (
    <Shell>
      <div className="flex items-end justify-between gap-4 mb-6">
        <div>
          <h1 className="text-xl font-semibold">Site dashboard</h1>
          <p className="text-sm text-ink-muted">Machine strip · ranked waste · WS {wsNote}</p>
        </div>
      </div>

      {live.isLoading && <p className="text-ink-muted">Loading machines…</p>}
      {live.isError && <p className="text-danger">Failed to load live data</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3 mb-8">
        {(live.data ?? []).map((m) => (
          <Link
            key={m.machine_id}
            to="/machines/$machineId"
            params={{ machineId: m.machine_id }}
            className="rounded-lg border border-line bg-surface-elevated p-4 shadow-panel hover:border-primary/40 transition-colors"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium text-sm truncate">{m.name}</span>
              <span
                className={`text-[10px] font-semibold uppercase tracking-wide text-white px-2 py-0.5 rounded ${stateColor(m.state)}`}
              >
                {m.state}
              </span>
            </div>
            <p className="mt-3 font-mono text-lg">{m.kw_est.toFixed(2)} kW</p>
            <p className="text-xs text-ink-muted mt-1">
              {m.state === "WASTE"
                ? `₹${m.waste_inr_per_hr.toFixed(0)}/hr waste`
                : `${m.i_rms_a.toFixed(1)} A · CT est.`}
            </p>
          </Link>
        ))}
        {!live.isLoading && !(live.data ?? []).length && (
          <p className="text-ink-muted col-span-full">No machines — run seed + simulator.</p>
        )}
      </div>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-muted mb-3">
          Ranked waste
        </h2>
        <div className="rounded-lg border border-line bg-surface-elevated overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface-muted text-left text-ink-muted">
              <tr>
                <th className="px-4 py-2 font-medium">Machine</th>
                <th className="px-4 py-2 font-medium">State</th>
                <th className="px-4 py-2 font-medium">Duration</th>
                <th className="px-4 py-2 font-medium">Waste</th>
                <th className="px-4 py-2 font-medium">Score</th>
              </tr>
            </thead>
            <tbody>
              {(rank.data ?? []).map((r) => (
                <tr key={r.machine_id} className="border-t border-line">
                  <td className="px-4 py-2.5 font-medium">{r.name}</td>
                  <td className="px-4 py-2.5">{r.state}</td>
                  <td className="px-4 py-2.5 font-mono">{r.duration_min}m</td>
                  <td className="px-4 py-2.5 font-mono">
                    {r.waste_kwh} kWh · ₹{r.waste_inr}
                  </td>
                  <td className="px-4 py-2.5 font-mono">{r.score}</td>
                </tr>
              ))}
              {!(rank.data ?? []).length && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-ink-muted">
                    No waste ranked yet — wait for IDLE/WASTE telemetry.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </Shell>
  );
}
