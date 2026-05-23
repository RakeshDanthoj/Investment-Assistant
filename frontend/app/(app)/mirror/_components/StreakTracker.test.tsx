/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";

import type { MirrorStreakResponse } from "@/lib/mirror/types";

import { StreakSummary } from "./StreakSummary";
import { StreakTracker } from "./StreakTracker";

const SAMPLE_CELLS: MirrorStreakResponse["cells"] = [
  { letter: "M", grade: "correct" },
  { letter: "P", grade: "partial" },
  { letter: "✗", grade: "incorrect" },
  { letter: "·", grade: "monitoring" },
  ...Array.from({ length: 10 }, () => ({ letter: "–" as const, grade: "empty" as const })),
];

describe("StreakTracker", () => {
  it("renders 14 cells with most recent grades first and transparent padding", () => {
    render(<StreakTracker cells={SAMPLE_CELLS} />);

    expect(screen.getByTestId("streak-cell-0")).toHaveAttribute("data-grade", "correct");
    expect(screen.getByTestId("streak-cell-0")).toHaveTextContent("M");
    expect(screen.getByTestId("streak-cell-3")).toHaveAttribute("data-grade", "monitoring");
    expect(screen.getByTestId("streak-cell-4")).toHaveAttribute("data-grade", "empty");
    expect(screen.getByTestId("streak-cell-13")).toHaveAttribute("data-grade", "empty");
    expect(screen.getByTestId("streak-legend")).toBeInTheDocument();
  });

  it("uses PRD colour tokens for correct and incorrect cells", () => {
    render(<StreakTracker cells={SAMPLE_CELLS} />);

    expect(screen.getByTestId("streak-cell-0").className).toMatch(/finnwise-green/);
    expect(screen.getByTestId("streak-cell-1").className).toMatch(/finnwise-amber/);
    expect(screen.getByTestId("streak-cell-2").className).toMatch(/finnwise-red/);
    expect(screen.getByTestId("streak-cell-4").className).toMatch(/bg-transparent/);
  });
});

describe("StreakSummary", () => {
  it("renders summary with mechanism and market percentages", () => {
    render(
      <StreakSummary
        streak={{
          cells: SAMPLE_CELLS,
          mechanism_accuracy_pct: 75,
          market_accuracy_pct: 50,
          summary:
            "Your mechanism accuracy (75%) is ahead of market reaction match (50%). That gap is normal.",
        }}
      />,
    );

    const summary = screen.getByTestId("streak-summary");
    expect(summary).toHaveTextContent("75%");
    expect(summary).toHaveTextContent("50%");
    expect(summary).toHaveTextContent("normal");
  });
});
