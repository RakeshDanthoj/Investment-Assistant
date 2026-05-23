/** @jest-environment jsdom */

import { render, screen } from "@testing-library/react";

import { StatsStrip } from "./StatsStrip";

describe("StatsStrip", () => {
  it("colours strong accuracy green and developing accuracy amber", () => {
    render(
      <StatsStrip
        stats={{
          total_predictions: 5,
          mechanism_accuracy_pct: 80,
          market_accuracy_pct: 55,
          reasoning_gaps_found: 2,
          mechanism_tone: "strong",
          market_tone: "developing",
        }}
      />,
    );

    expect(screen.getByText("80%").className).toMatch(/finnwise-green/);
    expect(screen.getByText("55%").className).toMatch(/finnwise-amber/);
  });
});
