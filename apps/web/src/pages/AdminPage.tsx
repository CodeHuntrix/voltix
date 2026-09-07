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
      <h1 className="mb-1 text-2xl font-semibold tracking-tight text-white">Admin</h1>
      <p className="mb-6 text-sm text-white/45">Machines · devices · policies</p>
      <div className="glass-card overflow-hidden rounded-2xl">
        <table className="w-full text-sm">
          <thead className="text-left text-white/45">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Device</th>
              <th className="px-4 py-3">Cut policy</th>
              <th className="px-4 py-3">AutoCut</th>
            </tr>
          </thead>
          <tbody>
            {(machines.data ?? []).map((m: any) => (
              <tr key={m.id} className="border-t border-white/10">
                <td className="px-4 py-2.5 font-medium text-white">{m.name}</td>
                <td className="px-4 py-2.5 text-white/70">{m.machine_type}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-white/50">{m.device_id ?? "—"}</td>
                <td className="px-4 py-2.5 text-white/70">{m.cut_policy}</td>
                <td className="px-4 py-2.5 text-white/70">{m.eligible_autocut ? "eligible ≤10A" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}
