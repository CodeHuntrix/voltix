export const colors = {
  primary: "#0C5CAB",
  primaryHover: "#0a4a8a",
  success: "#10b981",
  warning: "#f59e0b",
  danger: "#ef4444",
  surface: "#f8fafc",
  elevated: "#ffffff",
  muted: "#f1f5f9",
  border: "#e2e8f0",
  text: "#0f172a",
  textMuted: "#64748b",
  off: "#94a3b8",
  active: "#10b981",
  idle: "#f59e0b",
  waste: "#ef4444",
};

export function stateColor(state: string): string {
  switch (state) {
    case "ACTIVE":
      return colors.active;
    case "IDLE":
      return colors.idle;
    case "WASTE":
      return colors.waste;
    default:
      return colors.off;
  }
}
