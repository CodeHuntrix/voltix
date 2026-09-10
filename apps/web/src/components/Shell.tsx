import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { BrandMark } from "@/components/BrandMark";
import { useAuth } from "@/lib/auth";

const nav = [
  { to: "/dashboard", label: "Machines", icon: "M4 6h16M4 12h16M4 18h10" },
  { to: "/alerts", label: "Alerts", icon: "M15 17h5l-1.4-1.4A2 2 0 0 1 18 14V9a6 6 0 1 0-12 0v5a2 2 0 0 1-.6 1.4L4 17h5m6 0a3 3 0 1 1-6 0" },
  { to: "/autocut", label: "AutoCut", icon: "M13 10V3L4 14h7v7l9-11h-7z" },
  { to: "/mv", label: "M&V", icon: "M9 17v-6m4 6V7m4 10v-3M5 21h14" },
  { to: "/admin", label: "Admin", icon: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm7.4-4a7.1 7.1 0 0 0-.1-1l2-1.5-2-3.5-2.4 1a7 7 0 0 0-1.7-1L13 2h-4l-.3 2.5a7 7 0 0 0-1.7 1L4.6 5l-2 3.5L4.5 10a7.1 7.1 0 0 0 0 2l-2 1.5 2 3.5 2.4-1a7 7 0 0 0 1.7 1L9 20h4l.3-2.5a7 7 0 0 0 1.7-1l2.4 1 2-3.5-2-1.5z" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const path = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="ops-shell min-h-screen text-white">
      <div className="ops-shell-bg pointer-events-none fixed inset-0" aria-hidden="true" />
      <aside className="glass-rail fixed left-4 top-1/2 z-30 flex -translate-y-1/2 flex-col gap-2 rounded-full p-2">
        <nav aria-label="Ops" className="flex flex-col gap-2">
          {nav.map((item) => {
            const active = path.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                title={item.label}
                aria-label={item.label}
                aria-current={active ? "page" : undefined}
                className={`flex h-11 w-11 items-center justify-center rounded-full transition-colors ${
                  active ? "bg-primary text-white" : "text-white/55 hover:bg-white/10 hover:text-white"
                }`}
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
                </svg>
              </Link>
            );
          })}
        </nav>
        <button
          type="button"
          title="Sign out"
          aria-label="Sign out"
          onClick={() => {
            logout();
            void navigate({ to: "/login" });
          }}
          className="mt-2 flex h-11 w-11 items-center justify-center rounded-full text-white/40 hover:bg-white/10 hover:text-white"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H6a2 2 0 01-2-2V7a2 2 0 012-2h5a2 2 0 012 2v1"
            />
          </svg>
        </button>
      </aside>

      <div className="relative z-10 pl-20 pr-4 md:pl-24 md:pr-8">
        <header className="flex items-center justify-between gap-4 py-8">
          <BrandMark size="md" />
          <div className="glass-pill hidden items-center gap-3 px-4 py-2 text-sm text-white/70 sm:flex">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Live telemetry
          </div>
        </header>
        <main className="pb-10">{children}</main>
      </div>
    </div>
  );
}
