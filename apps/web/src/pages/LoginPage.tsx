import { useMutation } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { BrandMark } from "@/components/BrandMark";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export function LoginPage() {
  const [email, setEmail] = useState("owner@voltix.demo");
  const [password, setPassword] = useState("voltix-demo");
  const [error, setError] = useState<string | null>(null);
  const setTokens = useAuth((s) => s.setTokens);
  const setContext = useAuth((s) => s.setContext);
  const navigate = useNavigate();

  const mutation = useMutation({
    mutationFn: async () => {
      const tokens = await api.login(email, password);
      setTokens(tokens.access_token, tokens.refresh_token);
      const orgs = await api.orgs(tokens.access_token);
      if (!orgs.length) throw new Error("No organization");
      const sites = await api.sites(tokens.access_token, orgs[0].id);
      if (!sites.length) throw new Error("No site");
      setContext(orgs[0].id, sites[0].id);
      return sites[0];
    },
    onSuccess: () => navigate({ to: "/dashboard" }),
    onError: (e: Error) => setError(e.message),
  });

  return (
    <div className="ops-shell flex min-h-screen items-center justify-center px-4 text-white">
      <div className="ops-shell-bg pointer-events-none fixed inset-0" aria-hidden="true" />
      <div className="glass-card relative z-10 w-full max-w-md rounded-3xl p-8">
        <Link to="/" className="text-sm text-white/40 hover:text-white">
          Back
        </Link>
        <div className="mt-5">
          <BrandMark to="/" size="md" />
        </div>
        <form
          className="mt-8 space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            setError(null);
            mutation.mutate();
          }}
        >
          <label className="block text-sm">
            <span className="text-white/45">Email</span>
            <input
              className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-primary"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="block text-sm">
            <span className="text-white/45">Password</span>
            <input
              type="password"
              className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-primary"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={mutation.isPending}
            className="w-full rounded-full bg-primary py-2.5 font-medium text-white hover:bg-primary-hover"
          >
            {mutation.isPending ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
