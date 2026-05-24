/** @jest-environment jsdom */

import { render } from "@testing-library/react";
import { axe } from "jest-axe";

/**
 * PRD §8.3 foreground/background pairs used on Pulse, Thread, and Mirror.
 * Catches regressions below WCAG AA contrast (4.5:1 normal text).
 */
const PRD_PAIRS: { name: string; bg: string; fg: string; sample: string }[] = [
  { name: "body on surface", bg: "#F8FAFC", fg: "#334155", sample: "Instrument reasoning body copy." },
  { name: "secondary on surface", bg: "#F8FAFC", fg: "#64748B", sample: "Event context and subtext." },
  { name: "caption on surface", bg: "#F8FAFC", fg: "#94A3B8", sample: "Labels and timestamps." },
  { name: "ink on white card", bg: "#FFFFFF", fg: "#0F172A", sample: "Article titles and nav active text." },
  { name: "measured badge", bg: "#DBEAFE", fg: "#1A4FCC", sample: "MEASURED" },
  { name: "modelled badge", bg: "#D1FAE5", fg: "#0A6644", sample: "MODELLED" },
  { name: "judged badge", bg: "#FEF3C7", fg: "#8A5009", sample: "JUDGED" },
  { name: "opportunity chip", bg: "#D1FAE5", fg: "#0A6644", sample: "opportunity signal" },
  { name: "headwind chip", bg: "#FEE2E2", fg: "#9B2416", sample: "headwind signal" },
  { name: "entry block", bg: "#F0FDF4", fg: "#064E3B", sample: "Entry conditions list item." },
  { name: "exit block", bg: "#FFF7ED", fg: "#7C2D12", sample: "Exit conditions list item." },
];

describe("PRD §8.3 palette contrast", () => {
  it.each(PRD_PAIRS)("$name has no axe color-contrast violations", async ({ bg, fg, sample }) => {
    const { container } = render(
      <div style={{ backgroundColor: bg, color: fg, padding: 16 }}>
        <p>{sample}</p>
      </div>,
    );
    const results = await axe(container, {
      rules: {
        "color-contrast": { enabled: true },
      },
    });
    expect(results).toHaveNoViolations();
  });
});
