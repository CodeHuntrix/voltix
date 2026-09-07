import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Shell } from "@/components/Shell";
import { visibleAlerts } from "@/lib/alerts";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export function AlertsPage() {
  const token = useAuth((s) => s.accessToken)!;
  const siteId = useAuth((s) => s.siteId)!;
  const qc = useQueryClient();
  const live = useQuery({
    queryKey: ["live", siteId],
    queryFn: () => api.live(token, siteId),
    refetchInterval: 4000,
  });
  const alerts = useQuery({
    queryKey: ["alerts", siteId],
    queryFn: () => api.alerts(token, siteId),
    refetchInterval: 5000,
  });
  const ack = useMutation({
    mutationFn: (id: string) => api.ackAlert(token, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts", siteId] }),
  });
  const open = visibleAlerts(alerts.data ?? [], live.data ?? []);

  return (
    <Shell>
      <h1 className="mb-1 text-2xl font-semibold tracking-tight text-white">Alerts</h1>
      <p className="mb-6 text-sm text-white/45">Waste · offline · drift</p>
      <ul className="space-y-3">
        {open.map((a: any) => (
          <li key={a.id} className="glass-card flex items-start gap-4 rounded-2xl p-4">
            <span
              className={`mt-0.5 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase text-white ${
                a.severity === "critical" ? "bg-danger" : "bg-warning text-black"
              }`}
            >
              {a.severity}
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-medium text-white">{a.title}</p>
              <p className="mt-0.5 text-sm text-white/50">{a.message}</p>
              <p className="mt-2 font-mono text-xs text-white/35">
                {new Date(a.created_at).toLocaleString()}
              </p>
            </div>
            {!a.acknowledged && (
              <button
                type="button"
                className="text-sm font-medium text-sky-300 hover:text-white"
                onClick={() => ack.mutate(a.id)}
              >
                Ack
              </button>
            )}
          </li>
        ))}
        {!open.length && (
          <li className="text-white/45">No open alerts — sustained WASTE will fire after ~10m.</li>
        )}
      </ul>
    </Shell>
  );
}
