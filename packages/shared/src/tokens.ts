/** Voltix design tokens — Enterprise retokened (light-first ops console). */
export const voltixTokens = {
  colors: {
    primary: "#0C5CAB",
    primaryHover: "#0a4a8a",
    secondary: "#0a4a8a",
    success: "#10b981",
    warning: "#f59e0b",
    danger: "#ef4444",
    // Light-first slate neutrals (plan: no purple / cream-terracotta)
    surface: "#f8fafc",
    surfaceElevated: "#ffffff",
    surfaceMuted: "#f1f5f9",
    border: "#e2e8f0",
    borderStrong: "#cbd5e1",
    text: "#0f172a",
    textMuted: "#64748b",
    textInverse: "#f8fafc",
    // Machine states
    stateOff: "#94a3b8",
    stateActive: "#10b981",
    stateIdle: "#f59e0b",
    stateWaste: "#ef4444",
  },
  typography: {
    fontSans: '"IBM Plex Sans", system-ui, sans-serif',
    fontMono: '"IBM Plex Mono", ui-monospace, monospace',
    scale: {
      xs: "0.75rem",
      sm: "0.875rem",
      md: "1rem",
      lg: "1.25rem",
      xl: "1.5rem",
      "2xl": "2rem",
    },
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    "2xl": 48,
  },
  radius: {
    sm: 4,
    md: 8,
    lg: 12,
  },
  shadow: {
    sm: "0 1px 2px rgba(15, 23, 42, 0.06)",
    md: "0 4px 12px rgba(15, 23, 42, 0.08)",
  },
} as const;

export type VoltixTokens = typeof voltixTokens;
