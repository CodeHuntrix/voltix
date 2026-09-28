import { useMutation } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import "./auth.css";

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
    <div className="auth-page">
      <aside className="auth-story">
        <Link to="/" className="auth-brand" aria-label="VOLTIX home">
          <svg viewBox="0 0 40 40" fill="none" aria-hidden="true"><path d="M5 7h9l6 19L28 7h8L21 34h-6L5 7Z" fill="currentColor"/><path d="M28 7h8L21 34h-6l13-27Z" fill="#e6a17c"/></svg>
          <span>VOLTIX<span>.</span></span>
        </Link>
        <div className="auth-story-copy">
          <span className="auth-eyebrow">ENERGY INTELLIGENCE FOR LEGACY INDUSTRY</span>
          <h1>Know the floor<br />behind the meter.</h1>
          <p>A practical view of machine behavior, built for teams working with the equipment they already have.</p>
          <div className="auth-story-card">
            <span>PRODUCT PREVIEW</span>
            <strong>From a reading to a decision.</strong>
            <p>Review machine events, understand the signal, and record what happened next.</p>
            <small>ILLUSTRATIVE INTERFACE · SAMPLE DATA</small>
          </div>
        </div>
        <p className="auth-story-foot">IDEA ENGINEERS · SIH 2026</p>
      </aside>
      <main className="auth-main">
        <div className="auth-form-wrap">
          <Link to="/" className="vx-button vx-button--tertiary auth-back">Back to website</Link>
          <div className="auth-form-head">
            <span className="auth-eyebrow">YOUR WORKSPACE</span>
            <h2>{isSignup ? "Create your shop" : "Welcome back"}</h2>
            <p>{isSignup ? "Start with your team and site details. You can add machines next." : "Sign in to continue to your VOLTIX workspace."}</p>
          </div>
          <div className="auth-switch" role="group" aria-label="Account action">
            <button type="button" className={isSignup ? "" : "is-active"} onClick={() => switchMode("signin")}>Sign in</button>
            <button type="button" className={isSignup ? "is-active" : ""} onClick={() => switchMode("signup")}>Create account</button>
          </div>
        <form
          className="auth-form"
          onSubmit={(e) => {
            e.preventDefault();
            setError(null);
            if (isSignup) signUp.mutate();
            else signIn.mutate();
          }}
        >
          {isSignup && (
            <>
              <label>
                <span>Your name</span>
                <input
                  className="auth-input"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoComplete="name"
                  required
                />
              </label>
              <label>
                <span>Shop name</span>
                <input
                  className="auth-input"
                  value={shopName}
                  onChange={(e) => setShopName(e.target.value)}
                  autoComplete="organization"
                  required
                />
              </label>
            </>
          )}
          <label>
            <span>Email address</span>
            <input
              className="auth-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              type="email"
              required
            />
          </label>
          <label>
            <span>Password</span>
            <input
              type="password"
              className="auth-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={isSignup ? "new-password" : "current-password"}
              required
              minLength={isSignup ? 6 : undefined}
            />
          </label>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button
            type="submit"
            disabled={pending}
            className="vx-button vx-button--primary auth-submit"
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
        {!isSignup && <div className="auth-demo"><span>DEMO ACCESS</span><p>For the prototype, the demo account is filled in. Select <strong>Sign in</strong> to explore it.</p></div>}
        <p className="auth-alternate">
          {isSignup ? (
            <>
              Already have an account?{" "}
              <button
                type="button"
                className="vx-button vx-button--tertiary auth-inline-button"
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
                className="vx-button vx-button--tertiary auth-inline-button"
                onClick={() => switchMode("signup")}
              >
                Sign up
              </button>
            </>
          )}
        </p>
        </div>
      </main>
      </div>
  );
}
