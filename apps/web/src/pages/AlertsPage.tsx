import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Shell } from "@/components/Shell";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export function AlertsPage() {
  const token = useAuth((s) => s.accessToken)!;
  const siteId = useAuth((s) => s.siteId)!;
  const qc = useQueryClient();
  const alerts = useQuery({
    queryKey: ["alerts", siteId],
    queryFn: () => api.alerts(token, siteId),
    refetchInterval: 5000,
  });
  const ack = useMutation({
    mutationFn: (id: string) => api.ackAlert(token, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts", siteId] }),
  });

  return (
    <Shell>
      <h1 className="text-xl font-semibold mb-1">Alerts</h1>
      <p className="text-sm text-ink-muted mb-6">Waste · offline · drift</p>
      <ul className="space-y-3">
        {(alerts.data ?? []).map((a) => (
          <li
            key={a.id}
            className="rounded-lg border border-line bg-surface-elevated p-4 shadow-panel flex gap-4 items-start"
          >
            <span
              className={`mt-0.5 text-[10px] uppercase font-semibold px-2 py-0.5 rounded text-white ${
                a.severity === "critical" ? "bg-danger" : "bg-warning"
              }`}
            >
              {a.severity}
            </span>
            <div className="flex-1 min-w-0">
              <p className="font-medium">{a.title}</p>
              <p className="text-sm text-ink-muted mt-0.5">{a.message}</p>
              <p className="text-xs font-mono text-ink-muted mt-2">
                {new Date(a.created_at).toLocaleString()}
              </p>
            </div>
            {!a.acknowledged && (
              <button
                type="button"
                className="text-sm text-primary font-medium"
                onClick={() => ack.mutate(a.id)}
              >
                Ack
              </button>
            )}
          </li>
        ))}
        {!(alerts.data ?? []).length && (
          <li className="text-ink-muted">No alerts — sustained WASTE will fire after ~10m.</li>
        )}
      </ul>
    </Shell>
  );
}
