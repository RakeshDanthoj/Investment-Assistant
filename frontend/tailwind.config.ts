import type { Config } from "tailwindcss";
import plugin from "tailwindcss/plugin";

/** PRD §8.3 — FinnWise colour system */
const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        background: "var(--background)",
        foreground: "var(--foreground)",
        primary: {
          DEFAULT: "var(--primary)",
          foreground: "var(--primary-foreground)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          foreground: "var(--secondary-foreground)",
        },
        destructive: {
          DEFAULT: "var(--destructive)",
          foreground: "var(--destructive-foreground)",
        },
        muted: {
          DEFAULT: "var(--muted)",
          foreground: "var(--muted-foreground)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          foreground: "var(--accent-foreground)",
        },
        popover: {
          DEFAULT: "var(--popover)",
          foreground: "var(--popover-foreground)",
        },
        card: {
          DEFAULT: "var(--card)",
          foreground: "var(--card-foreground)",
        },
        sidebar: {
          DEFAULT: "var(--sidebar)",
          foreground: "var(--sidebar-foreground)",
          primary: "var(--sidebar-primary)",
          "primary-foreground": "var(--sidebar-primary-foreground)",
          accent: "var(--sidebar-accent)",
          "accent-foreground": "var(--sidebar-accent-foreground)",
          border: "var(--sidebar-border)",
          ring: "var(--sidebar-ring)",
        },
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
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [
    plugin(({ addVariant }) => {
      addVariant("data-horizontal", '&[data-orientation="horizontal"]');
      addVariant("data-vertical", '&[data-orientation="vertical"]');
      addVariant("data-open", [
        '&[data-state="open"]',
        '&[data-open]:not([data-open="false"])',
      ]);
      addVariant("data-closed", [
        '&[data-state="closed"]',
        '&[data-closed]:not([data-closed="false"])',
      ]);
      addVariant("data-active", [
        '&[data-state="active"]',
        '&[data-active]:not([data-active="false"])',
      ]);
      addVariant("data-checked", [
        '&[data-state="checked"]',
        '&[data-checked]:not([data-checked="false"])',
      ]);
      addVariant("data-unchecked", [
        '&[data-state="unchecked"]',
        '&[data-unchecked]:not([data-unchecked="false"])',
      ]);
      addVariant("data-selected", '&[data-selected="true"]');
      addVariant("data-disabled", [
        '&[data-disabled="true"]',
        '&[data-disabled]:not([data-disabled="false"])',
      ]);
      addVariant("group-data-horizontal", [
        ':merge(.group)[data-orientation="horizontal"] &',
        ':merge(.group\\/tabs)[data-orientation="horizontal"] &',
        ':merge(.group\\/toggle-group)[data-orientation="horizontal"] &',
      ]);
      addVariant("group-data-vertical", [
        ':merge(.group)[data-orientation="vertical"] &',
        ':merge(.group\\/tabs)[data-orientation="vertical"] &',
        ':merge(.group\\/toggle-group)[data-orientation="vertical"] &',
      ]);
    }),
  ],
};

export default config;
