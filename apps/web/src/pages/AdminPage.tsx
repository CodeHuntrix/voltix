import { useQuery } from "@tanstack/react-query";
import { Shell } from "@/components/Shell";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export function AdminPage() {
  const token = useAuth((s) => s.accessToken)!;
  const siteId = useAuth((s) => s.siteId)!;
  const machines = useQuery({
    queryKey: ["machines", siteId],
    queryFn: () => api.machines(token, siteId),
  });

  return (
    <Shell>
      <h1 className="text-xl font-semibold mb-1">Admin</h1>
      <p className="text-sm text-ink-muted mb-6">Machines · devices · policies</p>
      <div className="rounded-lg border border-line bg-surface-elevated overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-surface-muted text-left text-ink-muted">
            <tr>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Type</th>
              <th className="px-4 py-2">Device</th>
              <th className="px-4 py-2">Cut policy</th>
              <th className="px-4 py-2">AutoCut</th>
            </tr>
          </thead>
          <tbody>
            {(machines.data ?? []).map((m) => (
              <tr key={m.id} className="border-t border-line">
                <td className="px-4 py-2.5 font-medium">{m.name}</td>
                <td className="px-4 py-2.5">{m.machine_type}</td>
                <td className="px-4 py-2.5 font-mono text-xs">{m.device_id ?? "—"}</td>
                <td className="px-4 py-2.5">{m.cut_policy}</td>
                <td className="px-4 py-2.5">{m.eligible_autocut ? "eligible ≤10A" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}
