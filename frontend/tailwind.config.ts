import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        ink: "var(--ink)",
        muted: "var(--ink-muted)",
        border: "var(--border)",
        brand: "var(--brand)",
        positive: "var(--positive)",
        warning: "var(--warning)",
        danger: "var(--danger)",
      },
      fontFamily: {
        ui: "var(--font-ui)",
        display: "var(--font-display)",
        mono: "var(--font-mono)",
      },
    },
  },
  plugins: [],
};

export default config;
