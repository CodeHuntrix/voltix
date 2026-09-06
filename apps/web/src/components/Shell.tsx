import { Link, useRouterState } from "@tanstack/react-router";
import { useAuth } from "@/lib/auth";

const nav = [
  { to: "/dashboard", label: "Site" },
  { to: "/alerts", label: "Alerts" },
  { to: "/autocut", label: "AutoCut" },
  { to: "/mv", label: "M&V" },
  { to: "/admin", label: "Admin" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const { logout } = useAuth();
  const path = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-surface-elevated/90 backdrop-blur-sm sticky top-0 z-20">
        <div className="mx-auto max-w-7xl px-4 h-14 flex items-center gap-6">
          <Link to="/dashboard" className="font-semibold text-primary tracking-tight text-lg">
            Voltix
          </Link>
          <nav className="flex gap-1 text-sm">
            {nav.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`px-3 py-1.5 rounded-md ${
                  path.startsWith(item.to)
                    ? "bg-primary text-white"
                    : "text-ink-muted hover:bg-surface-muted hover:text-ink"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <button
            type="button"
            onClick={logout}
            className="ml-auto text-sm text-ink-muted hover:text-ink"
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}
