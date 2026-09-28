import { useState } from "react";
import "./landing.css";

const Mark = () => (
  <span className="vx-mark" aria-hidden="true">
    <svg viewBox="0 0 40 40" fill="none"><path d="M5 7h9l6 19L28 7h8L21 34h-6L5 7Z" fill="currentColor"/><path d="M28 7h8L21 34h-6l13-27Z" fill="#4cc7ff"/></svg>
  </span>
);

const Logo = () => <span className="vx-logo"><Mark /><span>VOLTIX<span className="vx-logo-dot">.</span></span></span>;

const navItems = [
  { href: "#problem", label: "The problem" },
  { href: "#approach", label: "How it works" },
  { href: "#prototype", label: "Prototype" },
];

function Header() {
  const [open, setOpen] = useState(false);
  return <header className="vx-header">
    <div className="vx-container vx-header-inner">
      <a href="#top" className="vx-logo-link" aria-label="VOLTIX home"><Logo /></a>
      <nav className={`vx-nav ${open ? "is-open" : ""}`} aria-label="Main navigation">
        {navItems.map(item => <a key={item.href} href={item.href} onClick={() => setOpen(false)}>{item.label}</a>)}
        <a href="/login" className="vx-nav-mobile-signin" onClick={() => setOpen(false)}>Sign in</a>
        <a href="#dashboard-preview" className="vx-button vx-button--primary vx-nav-mobile-cta" onClick={() => setOpen(false)}>View preview</a>
      </nav>
      <div className="vx-header-actions"><a href="/login" className="vx-button vx-button--tertiary vx-header-signin">Sign in</a><a href="#dashboard-preview" className="vx-button vx-button--primary vx-header-cta">View preview</a></div>
      <button className="vx-menu" type="button" aria-label={open ? "Close menu" : "Open menu"} aria-expanded={open} onClick={() => setOpen(!open)}><span /><span /></button>
    </div>
  </header>;
}

function SignalChart() {
  return <svg className="vx-chart" viewBox="0 0 560 230" role="img" aria-label="Illustrative electrical load chart showing a prolonged unloaded operating period">
    <defs><linearGradient id="chart-fill" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#e19470" stopOpacity=".2"/><stop offset="1" stopColor="#e19470" stopOpacity="0"/></linearGradient></defs>
    {[34,84,134,184].map(y => <line key={y} x1="0" y1={y} x2="560" y2={y} stroke="#2a3544" strokeDasharray="3 6" />)}
    <rect x="308" y="0" width="180" height="184" fill="#d5a06b" opacity=".1" />
    <path d="M0 159 L22 155 L37 160 L54 55 L76 52 L97 57 L119 49 L140 55 L160 57 L179 52 L197 56 L218 50 L237 55 L257 58 L277 61 L296 105 L315 115 L335 112 L355 118 L375 112 L395 116 L416 111 L435 115 L456 113 L478 109 L495 55 L516 52 L538 58 L560 53 L560 184 L0 184Z" fill="url(#chart-fill)" />
    <path d="M0 159 L22 155 L37 160 L54 55 L76 52 L97 57 L119 49 L140 55 L160 57 L179 52 L197 56 L218 50 L237 55 L257 58 L277 61 L296 105 L315 115 L335 112 L355 118 L375 112 L395 116 L416 111 L435 115 L456 113 L478 109 L495 55 L516 52 L538 58 L560 53" fill="none" stroke="#e9b397" strokeWidth="3" strokeLinejoin="round" />
    <line x1="309" x2="309" y1="0" y2="185" stroke="#d4a06e" strokeDasharray="5 5" />
    <line x1="488" x2="488" y1="0" y2="185" stroke="#d4a06e" strokeDasharray="5 5" />
    <text x="0" y="220">09:00</text><text x="170" y="220">09:30</text><text x="342" y="220">10:00</text><text x="505" y="220">10:30</text>
  </svg>;
}

function ProductPreview() {
  return <div className="vx-dashboard" aria-label="Illustrative VOLTIX dashboard with sample data">
    <aside className="vx-dash-sidebar">
      <div className="vx-dash-brand"><Logo /></div>
      <div className="vx-dash-nav"><span className="active">▦ <b>Overview</b></span><span>◫ <b>Machines</b></span><span>◉ <b>Opportunities</b></span><span>▥ <b>Reports</b></span></div>
      <div className="vx-dash-side-foot">SIH 2026<br />Idea Engineers</div>
    </aside>
    <div className="vx-dash-main">
      <div className="vx-dash-top"><div><span className="vx-dash-overline">SHOP FLOOR / OVERVIEW</span><h3>Energy overview</h3><p>Machine signals, operating states, and opportunities in one place.</p></div><span className="vx-dash-sample">SAMPLE DATA</span></div>
      <div className="vx-dash-metrics">
        <div><span>Machines observed</span><strong>04</strong><small>Demo workspace</small></div>
        <div><span>Needs review</span><strong className="vx-orange">01</strong><small>Potential unloaded run</small></div>
        <div><span>Estimated event cost</span><strong>₹24.60</strong><small>Illustrative only</small></div>
        <div><span>Last reading</span><strong>10:32</strong><small>Sample timeline</small></div>
      </div>
      <div className="vx-dash-content">
        <section className="vx-dash-chart-panel"><div className="vx-dash-panel-head"><div><span className="vx-dash-overline">COMPRESSOR 01</span><h4>Electrical load pattern</h4></div><span className="vx-dash-state"><i /> Unloaded interval</span></div><SignalChart /><div className="vx-dash-chart-footer"><span><i /> Current signature</span><span>Operator review suggested</span></div></section>
        <aside className="vx-dash-insight"><span className="vx-dash-overline">PRIORITY 01 / 01</span><div className="vx-dash-insight-icon">!</div><h4>Check compressor demand</h4><p>Extended unloaded operation may be avoidable. Confirm site conditions before recording an action.</p><div><span>Duration</span><strong>18 min</strong></div><div><span>Estimated impact</span><strong>₹24.60</strong></div><span className="vx-dash-review">REVIEW SUGGESTED</span></aside>
      </div>
      <div className="vx-dash-bottom"><span><i /> COMPRESSOR 01</span><span>ACTIVE / UNLOADED</span><span>10:13 – 10:31</span><span>EVENT LOGGED</span></div>
    </div>
  </div>;
}

function Hero() {
  return <section className="vx-hero" id="top">
    <div className="vx-hero-bg" aria-hidden="true" />
    <div className="vx-container vx-hero-inner"><div className="vx-hero-copy">
      <div className="vx-eyebrow"><span className="vx-eyebrow-line" /> ENERGY INTELLIGENCE FOR LEGACY INDUSTRY</div>
      <h1>Know what your machines are doing.<br /><em>See where energy goes.</em></h1>
      <p className="vx-hero-sub">Machine-level energy visibility for legacy factories, starting with unloaded air compressors.</p>
      <div className="vx-hero-actions"><a href="#dashboard-preview" className="vx-button vx-button--primary">View dashboard preview</a><a href="#approach" className="vx-button vx-button--secondary">See how it works</a></div>
      <p className="vx-demo-note">PROTOTYPE STAGE · DASHBOARD PREVIEW USES SAMPLE DATA</p>
    </div></div>
  </section>;
}

function DashboardShowcase() {
  return <section className="vx-showcase" id="dashboard-preview" aria-label="Dashboard preview"><div className="vx-container"><div className="vx-hero-visual"><ProductPreview /><div className="vx-hero-caption"><span>VOLTIX / OPERATIONS CONSOLE</span><span>ILLUSTRATIVE PRODUCT VIEW</span></div></div></div></section>;
}

function Problem() {
  return <section className="vx-section vx-problem" id="problem"><div className="vx-container vx-problem-grid"><div className="vx-section-heading"><span className="vx-kicker">01 / THE PROBLEM</span><h2>The bill tells you <em>how much.</em><br />It doesn’t tell you <em>why.</em></h2></div><div className="vx-problem-copy"><p>In a legacy workshop, one electricity total can hide hours of unnecessary machine operation. A compressor may continue drawing power while unloaded, even when nobody needs compressed air.</p><p>Finding that pattern takes more than a meter reading. Teams need a machine-level timeline, an explainable alert, and a way to record what happened after they acted.</p><div className="vx-problem-callout"><span>INITIAL FOCUS</span><strong>Prolonged unloaded operation on air compressors</strong></div></div></div></section>;
}

const steps = [
  { no: "01", title: "Sense", text: "A clamp-on current sensor observes the electrical signature of a selected machine." },
  { no: "02", title: "Understand", text: "Machine-specific patterns help separate active, unloaded and unavailable readings." },
  { no: "03", title: "Prioritize", text: "Potential waste appears as a time-stamped event with an estimated cost for review." },
  { no: "04", title: "Verify", text: "Operators record the action. Before-and-after readings help evaluate the outcome." },
];

function Approach() {
  return <section className="vx-section vx-approach" id="approach"><div className="vx-container"><div className="vx-approach-head"><div><span className="vx-kicker">02 / THE APPROACH</span><h2>From a power signal<br />to a practical decision.</h2></div><p>Designed as a retrofit workflow for machines that were never built to report their own operating data.</p></div><div className="vx-steps">{steps.map((step) => <div className="vx-step" key={step.no}><div className="vx-step-top"><span>{step.no}</span></div><h3>{step.title}</h3><p>{step.text}</p></div>)}</div><div className="vx-approach-foot"><span>ALERT FIRST</span><p>Any future control integration requires machine-specific approval and safety validation.</p></div></div></section>;
}

function Prototype() {
  return <section className="vx-section vx-prototype" id="prototype"><div className="vx-container vx-prototype-grid"><div><span className="vx-kicker">03 / WHERE WE ARE</span><h2>A working direction.<br /><em>An honest starting point.</em></h2><p>We’ve built a sensing-to-software prototype using a laptop charger as the first machine proxy. The next meaningful proof is a documented compressor session with reference measurements and operator-confirmed events.</p><a href="#dashboard-preview" className="vx-button vx-button--tertiary vx-prototype-link">View dashboard preview</a></div><div className="vx-status-card"><div className="vx-status-head"><span>VALIDATION STATUS</span><span>SEPTEMBER 2026</span></div><div className="vx-status-row"><span className="vx-status-symbol done">✓</span><div><strong>Bench sensing loop</strong><small>Physical current input through the software workflow</small></div><span className="vx-status-tag">PROTOTYPE</span></div><div className="vx-status-row"><span className="vx-status-symbol next">·</span><div><strong>Compressor use case</strong><small>Machine sessions and independent operating labels</small></div><span className="vx-status-tag future">NEXT</span></div><div className="vx-status-row"><span className="vx-status-symbol next">·</span><div><strong>Savings verification</strong><small>Reference energy readings and comparable conditions</small></div><span className="vx-status-tag future">NEXT</span></div><p className="vx-status-foot">Interface examples are illustrative; no percentage savings claim is presented as measured field impact.</p></div></div></section>;
}

function FinalCta() {
  return <section className="vx-final"><div className="vx-container vx-final-inner"><div><span className="vx-kicker">SEE THE WORKFLOW</span><h2>Less guesswork on<br />the shop floor.</h2><p>Explore how VOLTIX turns machine readings into an event an operator can review and act on.</p></div><a href="#dashboard-preview" className="vx-button vx-button--primary">View dashboard preview</a></div></section>;
}

export function LandingPage() {
  return <div className="vx-page"><Header /><main><Hero /><DashboardShowcase /><Problem /><Approach /><Prototype /><FinalCta /></main><footer className="vx-footer"><div className="vx-container vx-footer-inner"><Logo /><p>Machine-level energy intelligence for legacy MSMEs.</p><span>IDEA ENGINEERS · SIH 2026 · SIH26219</span></div></footer></div>;
}

export default LandingPage;
