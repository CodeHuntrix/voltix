import { Link } from "@tanstack/react-router";
import { BrandMark } from "@/components/BrandMark";
import { MachineArt } from "@/components/MachineArt";
import { formatInr } from "@/lib/money";

const SHOWCASE = [
  { type: "compressor", label: "Air compressor", blurb: "Load / unload waste", inr: 18 },
  { type: "cnc", label: "CNC / lathe", blurb: "Alert-only mid-cycle", inr: 24 },
  { type: "press", label: "Hydraulic press", blurb: "Cycle + idle energy", inr: 21 },
  { type: "conveyor", label: "Conveyor", blurb: "Utility AutoCut path", inr: 9 },
] as const;

const LOOP = [
  { id: "01", title: "Sense", line: "Clip-on CT per load" },
  { id: "02", title: "Verify", line: "OFF / ACTIVE / IDLE / WASTE" },
  { id: "03", title: "Decide", line: "Rank in rupees" },
  { id: "04", title: "Act", line: "Safe AutoCut or alert" },
  { id: "05", title: "Prove", line: "M&V export" },
] as const;

function ShowcaseArt({ type, label }: { type: string; label: string }) {
  return (
    <MachineArt
      machineType={type}
      alt={label}
      className="relative z-[1] mx-auto h-[96%] w-auto max-w-[94%] object-contain object-bottom"
    />
  );
}

export function LandingPage() {
  return (
    <div className="ops-shell min-h-screen text-white">
      <div className="ops-shell-bg pointer-events-none fixed inset-0" aria-hidden="true" />

      <header className="relative z-20 mx-auto flex max-w-6xl items-center justify-between px-6 py-8">
        <BrandMark to="/" size="lg" />
        <div className="flex items-center gap-4">
          <a href="#machines" className="hidden text-sm text-white/50 hover:text-white sm:inline">
            Machines
          </a>
          <Link
            to="/login"
            className="rounded-full bg-primary px-5 py-2 text-sm font-medium text-white hover:bg-primary-hover"
          >
            Open console
          </Link>
        </div>
      </header>

      <section className="relative z-10 mx-auto max-w-6xl px-6 pb-16 pt-10 md:pt-16">
        <p className="font-mono text-xs tracking-[0.25em] text-sky-300/80">SIH26219 · SMART AUTOMATION</p>
        <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight tracking-tight md:text-6xl">
          See the machine.
          <br />
          <span className="text-white/50">Stop the waste.</span>
        </h1>
        <p className="mt-5 max-w-xl text-base text-white/55 md:text-lg">
          Floor-ready energy ops for legacy MSME shops — live states, rupee ranking, safe AutoCut,
          and proof you can export.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            to="/login"
            className="rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white hover:bg-primary-hover"
          >
            Enter ops console
          </Link>
          <a
            href="#loop"
            className="rounded-full border border-white/15 px-6 py-3 text-sm text-white/80 hover:bg-white/5"
          >
            How it works
          </a>
        </div>
      </section>

      <section id="machines" className="relative z-10 mx-auto max-w-6xl px-6 pb-20">
        <div className="mb-6 flex items-end justify-between">
          <h2 className="text-2xl font-semibold tracking-tight">Machines</h2>
          <p className="text-xs text-white/40">Same cards you will see on the floor dashboard</p>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {SHOWCASE.map((m) => (
            <div key={m.type} className="machine-card rounded-2xl p-4 pt-5">
              <div className="machine-well relative flex h-52 items-end justify-center pb-3">
                <ShowcaseArt type={m.type} label={m.label} />
              </div>
              <p className="mt-2 text-sm font-semibold">{m.label}</p>
              <p className="mt-1 font-mono text-xl font-semibold">
                {formatInr(m.inr)}
                <span className="ml-1 text-sm font-medium text-white/40">/hr</span>
              </p>
              <p className="text-xs text-white/45">{m.blurb}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="loop" className="relative z-10 mx-auto max-w-6xl px-6 pb-24">
        <div className="glass-card rounded-3xl p-8 md:p-10">
          <h2 className="text-2xl font-semibold tracking-tight">Sense to Prove</h2>
          <p className="mt-2 max-w-2xl text-sm text-white/50">
            One closed loop for brownfield shops — no PLC rip-and-replace.
          </p>
          <ol className="mt-10 grid gap-6 sm:grid-cols-5">
            {LOOP.map((step) => (
              <li key={step.id}>
                <span className="font-mono text-xs text-primary">{step.id}</span>
                <p className="mt-2 font-semibold">{step.title}</p>
                <p className="mt-1 text-sm text-white/45">{step.line}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <footer className="relative z-10 border-t border-white/10 px-6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 text-xs text-white/35 sm:flex-row sm:justify-between">
          <span className="font-mono tracking-wider">VOLTIX · CODE HUNTRIX</span>
          <span>Demo · owner@voltix.demo</span>
        </div>
      </footer>
    </div>
  );
}
