import { useQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { CardSkeleton, ListSkeleton } from "@/components/CardSkeleton";
import { EmptyState, InlineError } from "@/components/EmptyState";
import { MachineArt } from "@/components/MachineArt";
import { PageHeader } from "@/components/PageHeader";
import { Shell } from "@/components/Shell";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatInr, liveInrPerHr } from "@/lib/money";

export function MachinePage() {
  const { machineId } = useParams({ from: "/machines/$machineId" });
  const token = useAuth((s) => s.accessToken)!;
  const siteId = useAuth((s) => s.siteId)!;

  const live = useQuery({
    queryKey: ["live", siteId],
    queryFn: () => api.live(token, siteId),
    refetchInterval: 4000,
  });
  const telemetry = useQuery({
    queryKey: ["telemetry", machineId],
    queryFn: () => api.telemetry(token, machineId),
    refetchInterval: 4000,
  });
  const states = useQuery({
    queryKey: ["states", machineId],
    queryFn: () => api.states(token, machineId),
  });

  const m = (live.data ?? []).find(
    (x: { machine_id: string }) => x.machine_id === machineId,
  );
  const tariff = m?.tariff_inr_per_kwh ?? 8.5;
  const chart = (telemetry.data ?? []).map(
    (p: { time: string; kw_est: number }) => ({
      time: p.time,
      inr_hr: p.kw_est * tariff,
      kw_est: p.kw_est,
    }),
  );
  const burn = m
    ? liveInrPerHr({
        inr_per_hr: m.inr_per_hr,
        kw_est: m.kw_est,
        tariff_inr_per_kwh: m.tariff_inr_per_kwh,
      })
    : 0;

  return (
    <Shell>
      <PageHeader
        title={m?.name ?? "Machine"}
        description="Live floor spend · CT estimate, not a billing meter"
      />

      {live.isLoading && !m && (
        <div className="mb-6 max-w-xs" aria-busy="true" aria-label="Loading machine">
          <CardSkeleton />
        </div>
      )}
      {live.isError && !m && (
        <div className="mb-6">
          <InlineError>Failed to load machine</InlineError>
        </div>
      )}
      {!live.isLoading && !live.isError && !m && (
        <EmptyState className="mb-6">Machine not found on this site.</EmptyState>
      )}

      {m && (
        <div className="mb-6 grid items-center gap-5 sm:grid-cols-[200px_1fr]">
          <div className="machine-card overflow-hidden rounded-2xl p-3">
            <div className="machine-well flex h-40 items-end justify-center pb-2">
              <MachineArt
                machineType={m.machine_type}
                alt={m.name}
                className="relative z-[1] h-[96%] w-auto max-w-[94%] object-contain object-bottom"
              />
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge state={m.state} className="rounded-full px-2.5 py-1 text-xs">
              {m.state}
            </StatusBadge>
            <span className="font-mono text-2xl font-semibold text-white">
              {formatInr(
                m.state === "WASTE" && m.waste_inr_per_hr > 0
                  ? m.waste_inr_per_hr
                  : burn,
              )}
              <span className="ml-1 text-sm font-medium text-white/40">/hr</span>
            </span>
            <span className="text-sm text-white/45">
              {m.kw_est.toFixed(2)} kW · {m.i_rms_a.toFixed(1)} A
              {m.model_version ? ` · ${m.model_version}` : ""}
            </span>
          </div>
        </div>
      )}

      <div className="glass-card mb-6 h-72 rounded-3xl p-4">
        <h2 className="mb-3 text-sm font-semibold text-white/70">₹ / hour</h2>
        {telemetry.isLoading && !chart.length && (
          <div className="h-48 animate-pulse rounded-2xl bg-white/5" aria-busy="true" />
        )}
        {chart.length ? (
          <ResponsiveContainer width="100%" height="90%">
            <LineChart data={chart}>
              <CartesianGrid
                stroke="rgba(148,163,184,0.15)"
                strokeDasharray="3 3"
              />
              <XAxis
                dataKey="time"
                tickFormatter={(v) => new Date(v).toLocaleTimeString()}
                minTickGap={40}
                stroke="#94a3b8"
                fontSize={11}
              />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip
                labelFormatter={(v) => new Date(String(v)).toLocaleString()}
                formatter={(value: number) => [formatInr(value), "₹/hr"]}
                contentStyle={{
                  borderRadius: 12,
                  borderColor: "rgba(255,255,255,0.1)",
                  background: "#161b22",
                  color: "#fff",
                }}
              />
              <Line
                type="monotone"
                dataKey="inr_hr"
                stroke="#38bdf8"
                dot={false}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : !telemetry.isLoading ? (
          <EmptyState>No telemetry yet.</EmptyState>
        ) : null}
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/45">
          State timeline
        </h2>
        {states.isLoading && !(states.data ?? []).length && <ListSkeleton rows={3} />}
        <ul className="space-y-2">
          {(states.data ?? [])
            .slice(0, 12)
            .map(
              (s: {
                id: string;
                state: string;
                started_at: string;
                ended_at?: string | null;
              }) => (
                <li
                  key={s.id}
                  className="glass-card flex justify-between rounded-2xl px-4 py-2.5 text-sm"
                >
                  <span className="font-medium text-white">{s.state}</span>
                  <span className="font-mono text-white/45">
                    {new Date(s.started_at).toLocaleString()}
                    {s.ended_at
                      ? ` → ${new Date(s.ended_at).toLocaleTimeString()}`
                      : " · open"}
                  </span>
                </li>
              ),
            )}
          {!states.isLoading && !(states.data ?? []).length && (
            <li>
              <EmptyState>No state events yet.</EmptyState>
            </li>
          )}
        </ul>
      </section>
    </Shell>
  );
}
