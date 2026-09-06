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
import { Shell } from "@/components/Shell";
import { api, stateColor } from "@/lib/api";
import { useAuth } from "@/lib/auth";

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

  const m = (live.data ?? []).find((x) => x.machine_id === machineId);

  return (
    <Shell>
      <div className="mb-6">
        <h1 className="text-xl font-semibold">{m?.name ?? "Machine"}</h1>
        <p className="text-sm text-ink-muted">
          Live CT estimate · not billing-grade metering
        </p>
      </div>

      {m && (
        <div className="flex flex-wrap gap-3 mb-6">
          <span
            className={`text-xs font-semibold uppercase text-white px-2.5 py-1 rounded ${stateColor(m.state)}`}
          >
            {m.state}
          </span>
          <span className="text-sm font-mono">{m.kw_est.toFixed(2)} kW</span>
          <span className="text-sm text-ink-muted font-mono">{m.i_rms_a.toFixed(2)} A</span>
          {m.waste_kw > 0 && (
            <span className="text-sm text-danger font-mono">
              waste ₹{m.waste_inr_per_hr.toFixed(0)}/hr
            </span>
          )}
        </div>
      )}

      <div className="rounded-lg border border-line bg-surface-elevated p-4 shadow-panel mb-6 h-72">
        <h2 className="text-sm font-semibold text-ink-muted mb-3">kW estimate</h2>
        {(telemetry.data ?? []).length ? (
          <ResponsiveContainer width="100%" height="90%">
            <LineChart data={telemetry.data}>
              <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tickFormatter={(v) => new Date(v).toLocaleTimeString()}
                minTickGap={40}
                stroke="#64748b"
                fontSize={11}
              />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip
                labelFormatter={(v) => new Date(String(v)).toLocaleString()}
                contentStyle={{ borderRadius: 8, borderColor: "#e2e8f0" }}
              />
              <Line type="monotone" dataKey="kw_est" stroke="#0C5CAB" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-ink-muted text-sm">No telemetry yet.</p>
        )}
      </div>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-muted mb-3">
          State timeline
        </h2>
        <ul className="space-y-2">
          {(states.data ?? []).map((s) => (
            <li
              key={s.id}
              className="rounded-md border border-line bg-surface-elevated px-4 py-2 flex justify-between text-sm"
            >
              <span className="font-medium">{s.state}</span>
              <span className="font-mono text-ink-muted">
                {new Date(s.started_at).toLocaleString()}
                {s.ended_at ? ` → ${new Date(s.ended_at).toLocaleTimeString()}` : " · open"}
              </span>
            </li>
          ))}
          {!(states.data ?? []).length && (
            <li className="text-ink-muted text-sm">No state events yet.</li>
          )}
        </ul>
      </section>
    </Shell>
  );
}
