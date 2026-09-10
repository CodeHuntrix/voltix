/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#0C5CAB",
          hover: "#0a4a8a",
        },
        success: "#10b981",
        warning: "#f59e0b",
        danger: "#ef4444",
        surface: {
          DEFAULT: "#07090c",
          elevated: "#10141a",
          muted: "#161b22",
        },
        ink: {
          DEFAULT: "#ffffff",
          muted: "#94a3b8",
        },
        line: {
          DEFAULT: "rgba(255, 255, 255, 0.08)",
          strong: "rgba(255, 255, 255, 0.16)",
        },
        state: {
          off: "#94a3b8",
          active: "#10b981",
          idle: "#f59e0b",
          waste: "#ef4444",
        },
        severity: {
          critical: "#ef4444",
          warning: "#f59e0b",
          info: "#0C5CAB",
        },
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 2px rgba(15, 23, 42, 0.06), 0 4px 12px rgba(15, 23, 42, 0.04)",
      },
    },
  },
  plugins: [],
};
