import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ListSkeleton } from "@/components/CardSkeleton";
import { EmptyState, InlineError } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { Shell } from "@/components/Shell";
import { StatusBadge } from "@/components/StatusBadge";
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
      <PageHeader title="Alerts" description="Waste · offline · drift" />
      {alerts.isLoading && !open.length && <ListSkeleton rows={3} />}
      {alerts.isError && !open.length && <InlineError>Failed to load alerts</InlineError>}
      <ul className="space-y-3">
        {open.map((a: any) => (
          <li key={a.id} className="glass-card flex items-start gap-4 rounded-2xl p-4">
            <StatusBadge severity={a.severity} className="mt-0.5 rounded-full">
              {a.severity}
            </StatusBadge>
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
        {!alerts.isLoading && !alerts.isError && !open.length && (
          <li>
            <EmptyState>No open alerts — sustained WASTE will fire after ~10m.</EmptyState>
          </li>
        )}
      </ul>
    </Shell>
  );
}
