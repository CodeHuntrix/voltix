import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Shell } from "@/components/Shell";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export function MvPage() {
  const token = useAuth((s) => s.accessToken)!;
  const siteId = useAuth((s) => s.siteId)!;
  const qc = useQueryClient();

  const baselines = useQuery({
    queryKey: ["mv-bl", siteId],
    queryFn: () => api.mvBaselines(token, siteId),
  });
  const reports = useQuery({
    queryKey: ["mv-rp", siteId],
    queryFn: () => api.mvReports(token, siteId),
  });

  const createReport = useMutation({
    mutationFn: async () => {
      const bl = baselines.data?.[0];
      if (!bl) throw new Error("No baseline");
      const end = new Date();
      const start = new Date(end.getTime() - 7 * 24 * 3600 * 1000);
      return api.mvReportCreate(token, siteId, {
        baseline_id: bl.id,
        intervention_start: start.toISOString(),
        intervention_end: end.toISOString(),
        tariff_inr_per_kwh: 8.5,
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mv-rp", siteId] }),
  });

  const exportCsv = useMutation({
    mutationFn: () => api.mvExport(token, siteId),
    onSuccess: (csv) => {
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `voltix-mv-${siteId.slice(0, 8)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  return (
    <Shell>
      <div className="flex items-end justify-between gap-4 mb-6">
        <div>
          <h1 className="text-xl font-semibold">M&V</h1>
          <p className="text-sm text-ink-muted">Baseline vs intervention · CT-estimated kWh</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded-md bg-primary text-white px-3 py-2 text-sm"
            onClick={() => createReport.mutate()}
          >
            Generate report
          </button>
          <button
            type="button"
            className="rounded-md border border-line px-3 py-2 text-sm"
            onClick={() => exportCsv.mutate()}
          >
            Export CSV
          </button>
        </div>
      </div>

      <section className="mb-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-muted mb-3">
          Baselines
        </h2>
        <ul className="space-y-2">
          {(baselines.data ?? []).map((b) => (
            <li key={b.id} className="rounded-md border border-line bg-surface-elevated px-4 py-3 text-sm">
              <span className="font-medium">{b.name}</span>
              <span className="ml-3 font-mono text-ink-muted">{b.baseline_kwh} kWh</span>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-muted mb-3">
          Reports
        </h2>
        <div className="rounded-lg border border-line overflow-hidden bg-surface-elevated">
          <table className="w-full text-sm">
            <thead className="bg-surface-muted text-ink-muted text-left">
              <tr>
                <th className="px-4 py-2">Period</th>
                <th className="px-4 py-2">Intervention kWh</th>
                <th className="px-4 py-2">Savings kWh</th>
                <th className="px-4 py-2">Savings ₹</th>
              </tr>
            </thead>
            <tbody>
              {(reports.data ?? []).map((r) => (
                <tr key={r.id} className="border-t border-line">
                  <td className="px-4 py-2 font-mono text-xs">
                    {new Date(r.intervention_start).toLocaleDateString()} –{" "}
                    {new Date(r.intervention_end).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-2 font-mono">{r.intervention_kwh.toFixed(1)}</td>
                  <td className="px-4 py-2 font-mono">{r.savings_kwh.toFixed(1)}</td>
                  <td className="px-4 py-2 font-mono">₹{r.savings_inr.toFixed(0)}</td>
                </tr>
              ))}
              {!(reports.data ?? []).length && (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-ink-muted">
                    No reports yet.
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
