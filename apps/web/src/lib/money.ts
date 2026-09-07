export function formatInr(value: number, fractionDigits = 0): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: 0,
  }).format(Number.isFinite(value) ? value : 0);
}

export function liveInrPerHr(m: {
  inr_per_hr?: number;
  kw_est?: number;
  tariff_inr_per_kwh?: number;
}): number {
  if (typeof m.inr_per_hr === "number") return m.inr_per_hr;
  return (m.kw_est ?? 0) * (m.tariff_inr_per_kwh ?? 8.5);
}

export function formatMinutes(min: number): string {
  if (min < 1) return "<1 min";
  if (min < 60) return `${Math.round(min)} min`;
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  return m ? `${h}h ${m}m` : `${h}h`;
}
