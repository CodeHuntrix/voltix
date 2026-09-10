import { useMutation } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { BrandMark } from "@/components/BrandMark";
import { InlineError } from "@/components/EmptyState";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { fieldClass } from "@/lib/form";

const DEMO_EMAIL = "owner@voltix.demo";
const DEMO_PASSWORD = "voltix-demo";

export function LoginPage() {
  const [mode, setMode] = useState<"signin" | "signup">(() =>
    new URLSearchParams(window.location.search).has("signup") ? "signup" : "signin",
  );
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [fullName, setFullName] = useState("");
  const [shopName, setShopName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const setTokens = useAuth((s) => s.setTokens);
  const setContext = useAuth((s) => s.setContext);
  const navigate = useNavigate();

  function switchMode(next: "signin" | "signup") {
    setError(null);
    setMode(next);
    if (next === "signin") {
      setEmail(DEMO_EMAIL);
      setPassword(DEMO_PASSWORD);
    } else {
      setEmail("");
      setPassword("");
    }
  }

  async function afterTokens(access: string, refresh: string, forceOnboarding: boolean) {
    setTokens(access, refresh);
    const orgs = await api.orgs(access);
    if (!orgs.length) throw new Error("No organization");
    const sites = await api.sites(access, orgs[0].id);
    if (!sites.length) throw new Error("No site");
    setContext(orgs[0].id, sites[0].id);
    if (forceOnboarding) {
      await navigate({ to: "/onboarding" });
      return;
    }
    const machines = await api.machines(access, sites[0].id);
    await navigate({ to: machines.length ? "/dashboard" : "/onboarding" });
  }

  const signIn = useMutation({
    mutationFn: async () => {
      const tokens = await api.login(email, password);
      await afterTokens(tokens.access_token, tokens.refresh_token, false);
    },
    onError: (e: Error) => setError(e.message),
  });

  const signUp = useMutation({
    mutationFn: async () => {
      if (password.length < 6) throw new Error("Password must be at least 6 characters");
      const tokens = await api.signup({
        email,
        password,
        full_name: fullName.trim(),
        shop_name: shopName.trim(),
      });
      await afterTokens(tokens.access_token, tokens.refresh_token, true);
    },
    onError: (e: Error) => setError(e.message),
  });

  const pending = signIn.isPending || signUp.isPending;
  const isSignup = mode === "signup";

  return (
    <div className="ops-shell flex min-h-screen items-center justify-center px-4 py-10 text-white">
      <div className="ops-shell-bg pointer-events-none fixed inset-0" aria-hidden="true" />
      <div className="glass-card relative z-10 w-full max-w-md rounded-3xl p-8">
        <Link to="/" className="text-sm text-white/40 hover:text-white">
          Back
        </Link>
        <div className="mt-5">
          <BrandMark to="/" size="md" />
        </div>
        <p className="mt-6 text-lg font-semibold">{isSignup ? "Create your shop" : "Sign in"}</p>
        <p className="mt-1 text-sm text-white/45">
          {isSignup
            ? "Then pick the machines on your floor."
            : "Judges: use the demo account, or create a shop."}
        </p>
        <form
          className="mt-6 space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            setError(null);
            if (isSignup) signUp.mutate();
            else signIn.mutate();
          }}
        >
          {isSignup && (
            <>
              <label className="block text-sm">
                <span className="text-white/45">Your name</span>
                <input
                  className={fieldClass}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoComplete="name"
                  required
                />
              </label>
              <label className="block text-sm">
                <span className="text-white/45">Shop name</span>
                <input
                  className={fieldClass}
                  value={shopName}
                  onChange={(e) => setShopName(e.target.value)}
                  autoComplete="organization"
                  required
                />
              </label>
            </>
          )}
          <label className="block text-sm">
            <span className="text-white/45">Email</span>
            <input
              className={fieldClass}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              type="email"
              required
            />
          </label>
          <label className="block text-sm">
            <span className="text-white/45">Password</span>
            <input
              type="password"
              className={fieldClass}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={isSignup ? "new-password" : "current-password"}
              required
              minLength={isSignup ? 6 : undefined}
            />
          </label>
          {error && <InlineError>{error}</InlineError>}
          <button
            type="submit"
            disabled={pending}
            className="w-full rounded-full bg-primary py-2.5 font-medium text-white hover:bg-primary-hover disabled:opacity-50"
          >
            {pending
              ? isSignup
                ? "Creating shop…"
                : "Signing in…"
              : isSignup
                ? "Create shop"
                : "Sign in"}
          </button>
        </form>
        <p className="mt-5 text-center text-sm text-white/45">
          {isSignup ? (
            <>
              Already have an account?{" "}
              <button
                type="button"
                className="font-medium text-sky-300 hover:text-white"
                onClick={() => switchMode("signin")}
              >
                Sign in
              </button>
            </>
          ) : (
            <>
              Don&apos;t have an account?{" "}
              <button
                type="button"
                className="font-medium text-sky-300 hover:text-white"
                onClick={() => switchMode("signup")}
              >
                Sign up
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
