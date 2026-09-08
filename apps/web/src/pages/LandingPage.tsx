import React, { useEffect, useRef, useState } from "react";
import { Link } from "@tanstack/react-router";
import { MachineArt } from "@/components/MachineArt";

// ─── Data ────────────────────────────────────────────────────────────────────

const MACHINES = [
  {
    type: "compressor",
    label: "Air compressor",
    cost: "₹18",
    unit: "/hr",
    insight: "Load / unload waste",
  },
  {
    type: "cnc",
    label: "CNC / lathe",
    cost: "₹24",
    unit: "/hr",
    insight: "Alert-only mid-cycle",
  },
  {
    type: "press",
    label: "Hydraulic press",
    cost: "₹21",
    unit: "/hr",
    insight: "Cycle + idle energy",
  },
  {
    type: "conveyor",
    label: "Conveyor",
    cost: "₹9",
    unit: "/hr",
    insight: "Utility AutoCut path",
  },
] as const;

const STEPS = [
  {
    num: "01",
    title: "Sense",
    desc: "Clip-on CT per load",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth={1.6}>
        <circle cx="12" cy="12" r="3" />
        <path d="M6.3 6.3a8 8 0 0 0 0 11.4M17.7 6.3a8 8 0 0 1 0 11.4" />
        <path d="M3.5 3.5a14 14 0 0 0 0 17M20.5 3.5a14 14 0 0 1 0 17" />
      </svg>
    ),
  },
  {
    num: "02",
    title: "Verify",
    desc: "OFF / ACTIVE / IDLE / WASTE",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth={1.6}>
        <circle cx="11" cy="11" r="7" />
        <path d="m21 21-4.35-4.35" />
        <path d="M8 11h6M11 8v6" />
      </svg>
    ),
  },
  {
    num: "03",
    title: "Decide",
    desc: "Rank in rupees",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth={1.6}>
        <path d="M3 3v18h18" />
        <path d="m7 16 4-4 4 4 4-6" />
      </svg>
    ),
  },
  {
    num: "04",
    title: "Act",
    desc: "Safe AutoCut or alert",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth={1.6}>
        <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z" />
      </svg>
    ),
  },
  {
    num: "05",
    title: "Prove",
    desc: "M&V export",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth={1.6}>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
        <path d="M14 2v6h6M8 13h8M8 17h5" />
      </svg>
    ),
  },
] as const;

const VALUE_ITEMS = [
  { value: "20–40%", label: "Potential energy waste reduction" },
  { value: "₹ Lakhs", label: "Annual savings potential" },
  { value: "Plug & Play", label: "Retrofit in hours" },
  { value: "Safer Ops", label: "AI-driven alerts" },
] as const;

const DIFF_CARDS = [
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth={1.6}>
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <path d="M8 21h8M12 17v4" />
      </svg>
    ),
    title: "Legacy-ready",
    body: "Retrofit intelligence onto existing machines without replacing the shop floor. Clip-on sensing, no PLC changes.",
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth={1.6}>
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
      </svg>
    ),
    title: "Machine-level intelligence",
    body: "Understand machine state, energy behaviour, cost of waste, and electrical drift — per machine.",
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" stroke="currentColor" strokeWidth={1.6}>
        <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z" />
      </svg>
    ),
    title: "Safe action",
    body: "Eligible utility loads can receive AutoCut commands. Critical machines remain alert-only — safety by design.",
  },
] as const;

// ─── Animated mini chart ──────────────────────────────────────────────────────

function MiniChart() {
  const [offset, setOffset] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setOffset((o) => (o + 1) % 40), 80);
    return () => clearInterval(id);
  }, []);

  const pts = [
    [0, 48], [25, 43], [48, 50], [70, 31], [95, 38],
    [120, 27], [143, 34], [165, 22], [190, 35], [215, 26], [240, 30],
  ]
    .map(([x, y]) => `${x},${y}`)
    .join(" ");

  return (
    <svg viewBox="0 0 240 70" className="h-full w-full">
      <defs>
        <linearGradient id="chartLine" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#1688ff" />
          <stop offset="100%" stopColor="#20d7c7" />
        </linearGradient>
      </defs>
      <polyline
        points={pts}
        fill="none"
        stroke="url(#chartLine)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ transform: `translateX(-${offset * 0.5}px)` }}
      />
    </svg>
  );
}

// ─── Logo / SVG ───────────────────────────────────────────────────────────────

function VoltixLogo({ className = "h-9 w-9" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <defs>
        <linearGradient id="vg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1688FF" />
          <stop offset="100%" stopColor="#20D7C7" />
        </linearGradient>
      </defs>
      <path d="M10 8 L26 8 L36 30 L46 8 L56 8 L38 48 L30 48 Z" fill="url(#vg)" />
      <path d="M33 18 L25 35 H32 L28 50 L43 30 H36 Z" fill="white" opacity="0.92" />
    </svg>
  );
}

// ─── Navbar ───────────────────────────────────────────────────────────────────

function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`sticky top-4 z-50 mx-auto max-w-7xl px-4 transition-all duration-300`}
    >
      <nav
        className={`flex items-center gap-6 rounded-2xl border px-5 py-3 transition-all duration-300 ${
          scrolled
            ? "border-white/15 bg-[#02070d]/90 shadow-2xl backdrop-blur-2xl"
            : "border-white/10 bg-[#04101a]/70 backdrop-blur-xl"
        }`}
      >
        {/* Brand */}
        <Link to="/" className="flex shrink-0 items-center gap-3 hover:opacity-90">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#1688ff]/30 bg-gradient-to-br from-[#1688ff]/20 to-[#20d7c7]/10">
            <VoltixLogo className="h-7 w-7" />
          </span>
          <span>
            <span className="block text-lg font-bold tracking-tight text-white">Voltix</span>
            <span className="block text-[10px] text-white/40">Energy ops for the shop floor</span>
          </span>
        </Link>

        {/* Desktop links */}
        <div className="ml-auto hidden items-center gap-7 lg:flex">
          {["#home", "#machines", "#how-it-works", "#impact", "#about"].map(
            (href, i) => {
              const labels = ["Home", "Machines", "How it works", "Impact", "About"];
              return (
                <a
                  key={href}
                  href={href}
                  className="text-sm text-white/50 transition-colors hover:text-white"
                >
                  {labels[i]}
                </a>
              );
            }
          )}
        </div>

        {/* CTA */}
        <div className="ml-6 hidden items-center gap-3 lg:flex">
          <Link
            to="/login"
            className="rounded-full border border-white/12 px-4 py-2 text-sm text-white/70 transition-all hover:border-white/25 hover:bg-white/5 hover:text-white"
          >
            Sign in
          </Link>
          <Link
            to="/dashboard"
            className="group flex items-center gap-2 rounded-full bg-gradient-to-r from-[#147df2] to-[#0870d9] px-5 py-2.5 text-sm font-semibold text-white shadow-[0_8px_24px_rgba(22,136,255,0.25)] transition-all hover:shadow-[0_10px_30px_rgba(22,136,255,0.4)] hover:-translate-y-0.5"
          >
            Open console
            <span className="transition-transform group-hover:translate-x-1">→</span>
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          className="ml-auto flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 text-white/60 lg:hidden"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
        >
          {menuOpen ? (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
              <path d="M3 12h18M3 6h18M3 18h18" />
            </svg>
          )}
        </button>
      </nav>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="mt-2 rounded-2xl border border-white/10 bg-[#050d16]/95 px-5 py-4 backdrop-blur-2xl lg:hidden">
          <div className="flex flex-col gap-4">
            {["#home", "#machines", "#how-it-works", "#impact", "#about"].map((href, i) => {
              const labels = ["Home", "Machines", "How it works", "Impact", "About"];
              return (
                <a
                  key={href}
                  href={href}
                  onClick={() => setMenuOpen(false)}
                  className="text-sm text-white/60 hover:text-white"
                >
                  {labels[i]}
                </a>
              );
            })}
            <div className="mt-2 flex flex-col gap-2 border-t border-white/10 pt-4">
              <Link to="/login" className="rounded-xl border border-white/12 py-2.5 text-center text-sm text-white/70">
                Sign in
              </Link>
              <Link
                to="/dashboard"
                className="rounded-xl bg-gradient-to-r from-[#147df2] to-[#0870d9] py-2.5 text-center text-sm font-semibold text-white"
              >
                Open console →
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

// ─── Hero telemetry overlay ───────────────────────────────────────────────────

function LiveDot() {
  return (
    <span className="relative flex h-2 w-2">
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
      <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
    </span>
  );
}

function HeroVisual() {
  return (
    <div className="relative flex min-h-[560px] items-center justify-center">
      {/* Glow */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="h-[380px] w-[380px] rounded-full bg-[#1688ff]/14 blur-[80px]" />
      </div>

      {/* Machine image */}
      <div className="relative z-10 w-[68%] transition-transform duration-500 hover:scale-[1.025]">
        <MachineArt
          machineType="cnc"
          alt="CNC machine monitored by Voltix"
          className="machine-art w-full drop-shadow-[0_30px_50px_rgba(0,0,0,0.7)]"
        />
      </div>

      {/* Top-left: main telemetry card */}
      <div className="lp-telemetry-card absolute left-[2%] top-[12%] z-20 w-[230px]">
        <div className="flex items-center justify-between">
          <span className="text-[13px] font-semibold text-white">CNC-01</span>
          <span className="flex items-center gap-1.5 text-[10px] font-medium text-emerald-400">
            <LiveDot />
            ACTIVE
          </span>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-2">
          {[
            ["Power", "4.2 kW"],
            ["Today's cost", "₹182"],
            ["Status", "Healthy"],
          ].map(([k, v]) => (
            <div key={k}>
              <p className="text-[9px] text-white/40">{k}</p>
              <p className="mt-1 text-[11px] font-semibold text-white">{v}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Top-right: live chart card */}
      <div className="lp-telemetry-card absolute right-[1%] top-[6%] z-20 w-[210px]">
        <div className="flex items-center justify-between text-[10px] text-white/50">
          <span>Live power (kW)</span>
          <span className="font-semibold text-white">4.2 kW</span>
        </div>
        <div className="mt-2 h-[58px]">
          <MiniChart />
        </div>
      </div>

      {/* Right side: intelligence stack */}
      <div className="absolute right-[-1%] top-[42%] z-20 flex w-[160px] flex-col gap-2">
        {[
          { icon: "✦", label: "Pulse", sub: "Machine state" },
          { icon: "◌", label: "Condition", sub: "Drift detection" },
          { icon: "↗", label: "Waste", sub: "₹ loss in real time" },
          { icon: "ϟ", label: "Action", sub: "AutoCut / safe" },
        ].map((item) => (
          <div
            key={item.label}
            className="flex cursor-default items-center gap-2.5 rounded-xl border border-white/8 bg-[#040c14]/88 px-3 py-2.5 backdrop-blur-xl transition-all hover:-translate-x-1 hover:border-[#1688ff]/40"
          >
            <span className="flex h-[28px] w-[28px] shrink-0 items-center justify-center rounded-lg bg-[#1688ff]/12 text-[14px] text-[#29a7ff]">
              {item.icon}
            </span>
            <div>
              <p className="text-[11px] font-semibold text-white">{item.label}</p>
              <p className="text-[9px] text-white/40">{item.sub}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Hero ─────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section id="home" className="relative z-10 mx-auto max-w-7xl px-6 pb-12 pt-16 md:pt-24">
      <div className="grid items-center gap-10 lg:grid-cols-2">
        {/* Copy */}
        <div className="lp-fade-up">
          <span className="inline-flex items-center rounded-full border border-[#1688ff]/35 bg-[#1688ff]/8 px-3 py-1.5 text-[10px] font-bold tracking-[0.2em] text-[#29a7ff]">
            SMART AUTOMATION FOR MSMEs
          </span>

          <h1 className="mt-6 text-[clamp(48px,6.5vw,80px)] font-bold leading-[0.94] tracking-[-0.055em] text-white">
            See the machine.
            <span className="block bg-gradient-to-r from-[#1688ff] to-[#20d7c7] bg-clip-text text-transparent">
              Stop the waste.
            </span>
          </h1>

          <p className="mt-6 text-xl font-medium text-white/80">
            Real-time energy operations for the shop floor.
          </p>

          <p className="mt-3 max-w-[560px] text-[15px] leading-relaxed text-white/50">
            Voltix helps MSME manufacturers monitor machine states, detect energy
            waste, detect condition drift, and take safe action — without
            expensive retrofits.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              to="/dashboard"
              className="group flex items-center gap-2 rounded-full bg-gradient-to-r from-[#147df2] to-[#0870d9] px-7 py-3.5 text-sm font-semibold text-white shadow-[0_10px_32px_rgba(22,136,255,0.22)] transition-all hover:-translate-y-0.5 hover:shadow-[0_14px_40px_rgba(22,136,255,0.38)]"
            >
              Enter ops console
              <span className="transition-transform group-hover:translate-x-1">→</span>
            </Link>
            <a
              href="#how-it-works"
              className="flex items-center gap-2 rounded-full border border-white/12 bg-white/[0.025] px-7 py-3.5 text-sm text-white/75 transition-all hover:border-white/22 hover:bg-white/[0.05] hover:text-white"
            >
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[#1688ff]/16 text-[9px]">
                ▶
              </span>
              Watch demo
            </a>
          </div>

          <div className="mt-7 flex flex-wrap gap-5 text-[12px] text-white/45">
            {["◈ No PLC changes", "◉ Retrofit-friendly", "◆ Built for MSMEs"].map((t) => (
              <span key={t} className="flex items-center gap-1.5">
                {t}
              </span>
            ))}
          </div>
        </div>

        {/* Visual */}
        <div className="lp-fade-up" style={{ animationDelay: "120ms" }}>
          <HeroVisual />
        </div>
      </div>
    </section>
  );
}

// ─── Value strip ─────────────────────────────────────────────────────────────

function ValueStrip() {
  return (
    <section className="relative z-10 mx-auto max-w-7xl px-6 pb-28">
      <div className="grid grid-cols-2 divide-x divide-white/8 overflow-hidden rounded-2xl border border-[#46a0e6]/18 bg-[#07111b]/72 backdrop-blur-xl lg:grid-cols-4">
        {VALUE_ITEMS.map(({ value, label }, i) => (
          <div
            key={value}
            className={`flex items-center gap-4 px-7 py-6 ${
              i !== VALUE_ITEMS.length - 1 ? "" : ""
            }`}
          >
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#1688ff]/12 text-[18px] text-[#1688ff]">
              ϟ
            </span>
            <div>
              <p className="text-xl font-bold text-white">{value}</p>
              <p className="mt-0.5 text-[11px] text-white/40">{label}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ─── Machines section ────────────────────────────────────────────────────────

function MachinesSection() {
  return (
    <section id="machines" className="relative z-10 mx-auto max-w-7xl px-6 pb-28">
      {/* Header */}
      <div className="mb-10 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="mb-2 text-[10px] font-bold tracking-[0.2em] text-[#29a7ff]">
            COMMON MACHINES
          </p>
          <h2 className="text-[clamp(30px,4vw,50px)] font-bold leading-none tracking-tight text-white">
            Built for the real shop floor.
          </h2>
        </div>
        <p className="max-w-[280px] text-right text-[13px] text-white/35 sm:max-w-[240px]">
          Different machines. Same waste. One solution.
        </p>
      </div>

      {/* Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {MACHINES.map((m) => (
          <article
            key={m.type}
            className="group relative overflow-hidden rounded-[18px] border border-white/8 bg-[#090f19]/82 p-3 transition-all duration-300 hover:-translate-y-1.5 hover:border-[#1688ff]/35 hover:bg-[#0e1924]/95 hover:shadow-[0_20px_50px_rgba(0,0,0,0.4)]"
          >
            {/* Image well */}
            <div className="machine-well relative flex h-[190px] items-center justify-center overflow-hidden rounded-[12px] bg-[#05090e]">
              <MachineArt
                machineType={m.type}
                alt={m.label}
                className="machine-art h-[90%] w-auto max-w-[90%] object-contain transition-transform duration-300 group-hover:scale-[1.06]"
              />
            </div>

            {/* Content */}
            <div className="px-2 pb-2 pt-4">
              <h3 className="text-[13px] font-semibold text-white">{m.label}</h3>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="text-[20px] font-bold text-white">{m.cost}</span>
                <span className="text-[11px] text-white/35">{m.unit}</span>
              </div>
              <p className="mt-1 text-[10px] text-white/40">{m.insight}</p>
            </div>

            {/* Arrow button */}
            <button className="absolute bottom-4 right-4 flex h-[30px] w-[30px] items-center justify-center rounded-full border border-white/10 bg-[#1688ff]/10 text-[13px] text-white/60 transition-all hover:border-[#1688ff]/40 hover:text-white">
              →
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

// ─── How it works ────────────────────────────────────────────────────────────

function HowItWorks() {
  return (
    <section id="how-it-works" className="relative z-10 mx-auto max-w-7xl px-6 pb-28">
      <p className="mb-2 text-[10px] font-bold tracking-[0.2em] text-[#29a7ff]">
        HOW VOLTIX WORKS
      </p>
      <h2 className="mb-10 text-[clamp(30px,4vw,50px)] font-bold leading-none tracking-tight text-white">
        From data to decisions — in real time.
      </h2>

      <div className="overflow-hidden rounded-3xl border border-white/8 bg-[#07111b]/75 p-5">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-5">
          {STEPS.map((step, idx) => (
            <div key={step.num} className="relative">
              <div className="min-h-[175px] rounded-2xl border border-white/8 bg-white/[0.018] p-5 transition-all hover:border-[#1688ff]/30 hover:bg-white/[0.03]">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#1688ff]/10 text-[#29a7ff]">
                  {step.icon}
                </span>
                <p className="mt-4 font-mono text-[9px] tracking-[0.15em] text-[#258fe8]">
                  {step.num}
                </p>
                <h3 className="mt-1 text-[15px] font-semibold text-white">{step.title}</h3>
                <p className="mt-1 text-[10px] leading-relaxed text-white/40">{step.desc}</p>
              </div>

              {/* Arrow between steps */}
              {idx < STEPS.length - 1 && (
                <div className="absolute -right-1.5 top-1/2 z-10 hidden -translate-y-1/2 text-[22px] text-[#1688ff]/60 sm:block">
                  →
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Differentiation ─────────────────────────────────────────────────────────

function Differentiation() {
  return (
    <section id="product" className="relative z-10 mx-auto max-w-7xl px-6 pb-28">
      <p className="mb-2 text-[10px] font-bold tracking-[0.2em] text-[#29a7ff]">WHY VOLTIX</p>
      <h2 className="mb-10 text-[clamp(30px,4vw,50px)] font-bold leading-none tracking-tight text-white">
        Built for legacy shops.
        <br />
        <span className="text-white/45">Not just new factories.</span>
      </h2>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {DIFF_CARDS.map((card) => (
          <article
            key={card.title}
            className="rounded-[20px] border border-white/8 bg-[#090f19]/75 p-7 transition-all duration-200 hover:border-[#1688ff]/25 hover:bg-[#0d1a27]/90"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#1688ff]/10 text-[#1688ff]">
              {card.icon}
            </span>
            <h3 className="mt-6 text-[17px] font-semibold text-white">{card.title}</h3>
            <p className="mt-2 text-[13px] leading-relaxed text-white/50">{card.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

// ─── Impact section ───────────────────────────────────────────────────────────

function ImpactSection() {
  return (
    <section id="impact" className="relative z-10 mx-auto max-w-7xl px-6 pb-28">
      <div className="overflow-hidden rounded-[30px] border border-white/8 bg-[radial-gradient(circle_at_85%_20%,rgba(22,136,255,0.09),transparent_35%),rgba(7,16,25,0.82)] p-10 md:p-16">
        <p className="mb-3 text-[10px] font-bold tracking-[0.2em] text-[#29a7ff]">
          THE VOLTIX DIFFERENCE
        </p>
        <h2 className="text-[clamp(28px,4vw,48px)] font-bold leading-tight tracking-tight text-white">
          Energy becomes visible.
          <br />
          Waste becomes measurable.
          <br />
          Action becomes safer.
        </h2>

        <div className="mt-12 grid grid-cols-1 gap-4 md:grid-cols-3">
          {[
            {
              tag: "₹ / hour",
              title: "Understand the cost",
              body: "Translate avoidable machine consumption into money your team can act on.",
            },
            {
              tag: "Machine state",
              title: "Know what's happening",
              body: "Distinguish OFF, IDLE, ACTIVE and WASTE behaviour from real telemetry.",
            },
            {
              tag: "Drift score",
              title: "Spot abnormal behaviour early",
              body: "Compare active electrical behaviour against the machine's own learned baseline.",
            },
          ].map((c) => (
            <div
              key={c.title}
              className="rounded-[18px] border border-white/8 bg-white/[0.018] p-6"
            >
              <p className="text-[11px] font-bold text-[#29a7ff]">{c.tag}</p>
              <h3 className="mt-7 text-[18px] font-semibold text-white">{c.title}</h3>
              <p className="mt-2 text-[12px] leading-relaxed text-white/50">{c.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Final CTA ────────────────────────────────────────────────────────────────

function FinalCTA() {
  return (
    <section className="relative z-10 mx-auto max-w-7xl overflow-hidden px-6 pb-24">
      <div className="relative flex flex-col items-start justify-between gap-10 overflow-hidden rounded-[30px] border border-[#1688ff]/28 bg-[#06111d] p-10 md:flex-row md:items-center md:p-14">
        {/* Blue glow */}
        <div className="pointer-events-none absolute right-0 top-0 h-full w-1/2 bg-[radial-gradient(circle_at_75%_50%,rgba(22,136,255,0.12),transparent_55%)]" />

        <div className="relative z-10 max-w-xl">
          <p className="mb-3 text-[10px] font-bold tracking-[0.2em] text-[#29a7ff]">
            READY TO SEE THE DIFFERENCE?
          </p>
          <h2 className="text-[clamp(38px,5.5vw,64px)] font-bold leading-[0.96] tracking-[-0.055em] text-white">
            Make every unit count.
          </h2>
          <p className="mt-5 max-w-[480px] text-[15px] leading-relaxed text-white/50">
            Give legacy machines the intelligence to operate more efficiently,
            safely, and measurably.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              to="/dashboard"
              className="group flex items-center gap-2 rounded-full bg-gradient-to-r from-[#147df2] to-[#0870d9] px-7 py-3.5 text-sm font-semibold text-white shadow-[0_10px_30px_rgba(22,136,255,0.22)] transition-all hover:-translate-y-0.5 hover:shadow-[0_14px_38px_rgba(22,136,255,0.38)]"
            >
              Open console
              <span className="transition-transform group-hover:translate-x-1">→</span>
            </Link>
            <button className="rounded-full border border-white/12 bg-white/[0.025] px-7 py-3.5 text-sm text-white/70 transition-all hover:border-white/22 hover:text-white">
              Talk to us
            </button>
          </div>
        </div>

        {/* Energy visual */}
        <div className="relative z-10 flex h-[250px] w-[250px] shrink-0 items-center justify-center">
          <div className="absolute h-[210px] w-[210px] animate-[spin_18s_linear_infinite] rounded-full border border-[#1688ff]/25 shadow-[0_0_60px_rgba(22,136,255,0.12)]" />
          <div className="absolute h-[155px] w-[155px] animate-[spin_12s_linear_infinite_reverse] rounded-full border border-[#20d7c7]/15" />
          <div className="flex h-[76px] w-[76px] items-center justify-center rounded-full bg-gradient-to-br from-[#1688ff] to-[#20d7c7] text-[34px] font-bold text-white shadow-[0_0_60px_rgba(22,136,255,0.4)]">
            ϟ
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Footer ───────────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer id="about" className="relative z-10 border-t border-white/8">
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-6 px-6 py-10 sm:flex-row sm:items-center">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-[#1688ff]/30 bg-gradient-to-br from-[#1688ff]/20 to-[#20d7c7]/10">
            <VoltixLogo className="h-6 w-6" />
          </span>
          <div>
            <p className="text-sm font-bold text-white">Voltix</p>
            <p className="text-[10px] text-white/35">Energy ops for the shop floor</p>
          </div>
        </div>

        {/* Links */}
        <div className="flex flex-wrap gap-6">
          {[
            ["#product", "Product"],
            ["#machines", "Machines"],
            ["#how-it-works", "How it works"],
            ["#impact", "Impact"],
          ].map(([href, label]) => (
            <a key={href} href={href} className="text-[13px] text-white/40 hover:text-white">
              {label}
            </a>
          ))}
        </div>

        {/* Meta */}
        <p className="flex items-center gap-2 text-[10px] text-white/30">
          <span>SIH26219</span>
          <span>•</span>
          <span>Code Huntrix</span>
        </p>
      </div>
    </footer>
  );
}

// ─── Intersection observer fade-in ───────────────────────────────────────────

function useSectionFade() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.style.opacity = "1";
          el.style.transform = "translateY(0)";
          obs.disconnect();
        }
      },
      { threshold: 0.08 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return ref;
}

function FadeSection({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const ref = useSectionFade();
  return (
    <div
      ref={ref}
      style={{
        opacity: 0,
        transform: "translateY(32px)",
        transition: `opacity 0.65s ease ${delay}ms, transform 0.65s ease ${delay}ms`,
      }}
    >
      {children}
    </div>
  );
}

// ─── Main export ─────────────────────────────────────────────────────────────

export function LandingPage() {
  return (
    <div className="lp-root min-h-screen overflow-x-hidden text-white">
      {/* Background */}
      <div className="lp-bg pointer-events-none fixed inset-0" aria-hidden="true" />

      <Navbar />

      <main>
        <FadeSection>
          <Hero />
        </FadeSection>

        <FadeSection delay={60}>
          <ValueStrip />
        </FadeSection>

        <FadeSection delay={80}>
          <MachinesSection />
        </FadeSection>

        <FadeSection delay={60}>
          <HowItWorks />
        </FadeSection>

        <FadeSection delay={60}>
          <Differentiation />
        </FadeSection>

        <FadeSection delay={60}>
          <ImpactSection />
        </FadeSection>

        <FadeSection delay={60}>
          <FinalCTA />
        </FadeSection>
      </main>

      <Footer />
    </div>
  );
}
