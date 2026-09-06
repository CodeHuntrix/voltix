import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Shell } from "@/components/Shell";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export function AutocutPage() {
  const token = useAuth((s) => s.accessToken)!;
  const siteId = useAuth((s) => s.siteId)!;
  const qc = useQueryClient();

  const live = useQuery({
    queryKey: ["live", siteId],
    queryFn: () => api.live(token, siteId),
  });
  const cmds = useQuery({
    queryKey: ["autocut", siteId],
    queryFn: () => api.autocutList(token, siteId),
    refetchInterval: 4000,
  });

  const create = useMutation({
    mutationFn: (machineId: string) =>
      api.autocutCreate(token, machineId, "Ops console suggest — sustained waste"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["autocut", siteId] }),
  });
  const decide = useMutation({
    mutationFn: ({ id, approve }: { id: string; approve: boolean }) =>
      api.autocutDecide(token, id, approve),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["autocut", siteId] }),
  });

  const eligible = (live.data ?? []).filter((m) => m.eligible_autocut);

  return (
    <Shell>
      <h1 className="text-xl font-semibold mb-1">AutoCut</h1>
      <p className="text-sm text-ink-muted mb-2">
        Eligible loads only (≤10A relay). Confirm circuit before actuation.
      </p>

      <section className="mb-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-muted mb-3">
          Suggest cut
        </h2>
        <div className="flex flex-wrap gap-2">
          {eligible.map((m) => (
            <button
              key={m.machine_id}
              type="button"
              className="rounded-md border border-line bg-surface-elevated px-3 py-2 text-sm hover:border-primary"
              onClick={() => create.mutate(m.machine_id)}
            >
              {m.name} · {m.state}
            </button>
          ))}
          {!eligible.length && (
            <p className="text-sm text-ink-muted">No eligible machines on this site.</p>
          )}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-muted mb-3">
          Command queue
        </h2>
        <ul className="space-y-2">
          {(cmds.data ?? []).map((c) => (
            <li
              key={c.id}
              className="rounded-lg border border-line bg-surface-elevated px-4 py-3 flex flex-wrap items-center gap-3"
            >
              <span className="font-mono text-xs text-ink-muted">{c.id.slice(0, 8)}</span>
              <span className="text-sm font-medium">{c.status}</span>
              <span className="text-sm text-ink-muted flex-1">{c.reason}</span>
              {c.status === "pending" && (
                <>
                  <button
                    type="button"
                    className="text-sm bg-success text-white px-3 py-1 rounded-md"
                    onClick={() => decide.mutate({ id: c.id, approve: true })}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    className="text-sm bg-danger text-white px-3 py-1 rounded-md"
                    onClick={() => decide.mutate({ id: c.id, approve: false })}
                  >
                    Deny
                  </button>
                </>
              )}
            </li>
          ))}
          {!(cmds.data ?? []).length && (
            <li className="text-ink-muted text-sm">No AutoCut commands yet.</li>
          )}
        </ul>
      </section>
    </Shell>
  );
}
