import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Shell } from "@/components/Shell";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatInr } from "@/lib/money";

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
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-white">M&V</h1>
          <p className="text-sm text-white/45">Baseline vs intervention · savings in rupees</p>
          {createReport.isError && (
            <p className="mt-1 text-sm text-red-400">{(createReport.error as Error).message}</p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded-full bg-primary px-4 py-2 text-sm text-white hover:bg-primary-hover disabled:opacity-50"
            disabled={createReport.isPending}
            onClick={() => createReport.mutate()}
          >
            {createReport.isPending ? "Generating…" : "Generate report"}
          </button>
          <button
            type="button"
            className="glass-card rounded-full px-4 py-2 text-sm text-white"
            onClick={() => exportCsv.mutate()}
          >
            Export CSV
          </button>
        </div>
      </div>

      <section className="mb-8">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/45">Baselines</h2>
        <ul className="space-y-2">
          {(baselines.data ?? []).map((b: any) => (
            <li key={b.id} className="glass-card rounded-2xl px-4 py-3 text-sm">
              <span className="font-medium text-white">{b.name}</span>
              <span className="ml-3 font-mono text-white/45">{b.baseline_kwh} kWh</span>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-white/45">Reports</h2>
        <div className="glass-card overflow-hidden rounded-2xl">
          <table className="w-full text-sm">
            <thead className="text-left text-white/45">
              <tr>
                <th className="px-4 py-3">Period</th>
                <th className="px-4 py-3">Intervention kWh</th>
                <th className="px-4 py-3">Savings kWh</th>
                <th className="px-4 py-3">Savings</th>
              </tr>
            </thead>
            <tbody>
              {(reports.data ?? []).map((r: any) => (
                <tr key={r.id} className="border-t border-white/10">
                  <td className="px-4 py-3 font-mono text-xs text-white/70">
                    {new Date(r.intervention_start).toLocaleDateString()} –{" "}
                    {new Date(r.intervention_end).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 font-mono text-white">{r.intervention_kwh.toFixed(1)}</td>
                  <td className="px-4 py-3 font-mono text-white">{r.savings_kwh.toFixed(1)}</td>
                  <td className="px-4 py-3 font-mono text-emerald-400">{formatInr(r.savings_inr)}</td>
                </tr>
              ))}
              {!(reports.data ?? []).length && (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-white/45">
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
