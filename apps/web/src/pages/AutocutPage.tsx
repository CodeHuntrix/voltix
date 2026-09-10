import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ListSkeleton } from "@/components/CardSkeleton";
import { EmptyState, InlineError } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
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

  const eligible = (live.data ?? []).filter((m: { eligible_autocut: boolean }) => m.eligible_autocut);

  return (
    <Shell>
      <PageHeader
        title="AutoCut"
        description="Eligible loads only (≤10A relay). Confirm the circuit before actuation."
      />

      <section className="mb-8">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/45">Suggest cut</h2>
        {live.isLoading && !eligible.length && <ListSkeleton rows={1} />}
        {live.isError && !eligible.length && <InlineError>Failed to load machines</InlineError>}
        <div className="flex flex-wrap gap-2">
          {eligible.map((m: { machine_id: string; name: string; state: string }) => (
            <button
              key={m.machine_id}
              type="button"
              className="glass-card rounded-full px-4 py-2 text-sm text-white hover:border-primary"
              onClick={() => create.mutate(m.machine_id)}
            >
              {m.name} · {m.state}
            </button>
          ))}
          {!live.isLoading && !live.isError && !eligible.length && (
            <EmptyState>No eligible machines on this site.</EmptyState>
          )}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/45">Command queue</h2>
        {cmds.isLoading && !(cmds.data ?? []).length && <ListSkeleton rows={2} />}
        {cmds.isError && !(cmds.data ?? []).length && <InlineError>Failed to load commands</InlineError>}
        <ul className="space-y-2">
          {(cmds.data ?? []).map((c: any) => (
            <li key={c.id} className="glass-card flex flex-wrap items-center gap-3 rounded-2xl px-4 py-3">
              <span className="font-mono text-xs text-white/35">{c.id.slice(0, 8)}</span>
              <span className="text-sm font-medium text-white">{c.status}</span>
              <span className="flex-1 text-sm text-white/50">{c.reason}</span>
              {c.status === "pending" && (
                <>
                  <button
                    type="button"
                    className="rounded-full bg-success px-3 py-1 text-sm text-white"
                    onClick={() => decide.mutate({ id: c.id, approve: true })}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    className="rounded-full bg-danger px-3 py-1 text-sm text-white"
                    onClick={() => decide.mutate({ id: c.id, approve: false })}
                  >
                    Deny
                  </button>
                </>
              )}
            </li>
          ))}
          {!cmds.isLoading && !cmds.isError && !(cmds.data ?? []).length && (
            <li>
              <EmptyState>No AutoCut commands yet.</EmptyState>
            </li>
          )}
        </ul>
      </section>
    </Shell>
  );
}
