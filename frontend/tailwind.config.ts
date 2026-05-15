import type { Config } from "tailwindcss";

/** PRD §8.3 — FinnWise colour system */
const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        finnwise: {
          blue: "#1A4FCC",
          green: "#0A6644",
          amber: "#8A5009",
          red: "#9B2416",
          surface: "#F8FAFC",
          "blue-tint": "#EEF3FF",
          "measured-bg": "#DBEAFE",
          "modelled-bg": "#D1FAE5",
          "judged-bg": "#FEF3C7",
        },
        slate: {
          900: "#0F172A",
          700: "#334155",
          500: "#64748B",
          400: "#94A3B8",
          200: "#E2E8F0",
          100: "#F1F5F9",
        },
      },
      fontFamily: {
        display: ["var(--font-playfair)", "Georgia", "serif"],
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-dm-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
