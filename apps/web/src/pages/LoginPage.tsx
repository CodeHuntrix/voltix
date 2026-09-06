import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";
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
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md rounded-lg border border-line bg-surface-elevated shadow-panel p-8">
        <h1 className="text-2xl font-semibold text-primary">Voltix</h1>
        <p className="mt-1 text-sm text-ink-muted">Ops console · CT-estimated energy waste</p>
        <form
          className="mt-8 space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            setError(null);
            mutation.mutate();
          }}
        >
          <label className="block text-sm">
            <span className="text-ink-muted">Email</span>
            <input
              className="mt-1 w-full rounded-md border border-line px-3 py-2"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="block text-sm">
            <span className="text-ink-muted">Password</span>
            <input
              type="password"
              className="mt-1 w-full rounded-md border border-line px-3 py-2"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          {error && <p className="text-sm text-danger">{error}</p>}
          <button
            type="submit"
            disabled={mutation.isPending}
            className="w-full rounded-md bg-primary hover:bg-primary-hover text-white py-2.5 font-medium"
          >
            {mutation.isPending ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
