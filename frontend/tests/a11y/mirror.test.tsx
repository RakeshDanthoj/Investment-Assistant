/** @jest-environment jsdom */

import { render } from "@testing-library/react";
import { axe } from "jest-axe";

import { StatsStrip } from "@/app/(app)/mirror/_components/StatsStrip";
import { PredictionCard } from "@/app/(app)/mirror/_components/PredictionCard";

describe("Mirror a11y", () => {
  it("StatsStrip has no axe violations", async () => {
    const { container } = render(
      <StatsStrip
        stats={{
          total_predictions: 12,
          mechanism_accuracy_pct: 62.5,
          market_accuracy_pct: 55,
          reasoning_gaps_found: 2,
          mechanism_tone: "developing",
          market_tone: "developing",
        }}
      />,
    );
    expect(await axe(container)).toHaveNoViolations();
  });

  it("PredictionCard has no axe violations", async () => {
    const { container } = render(
      <PredictionCard
        prediction={{
          id: "p1",
          card_id: "c1",
          prediction_text: "Rates stay higher for longer than the market prices.",
          logged_at: "2026-05-01T10:00:00.000Z",
          mechanism_accuracy: "monitoring",
          business_accuracy: null,
          market_accuracy: null,
          gap_insight: null,
          card_title: "Sample headline",
          event_title: "RBI holds repo",
          event_category: "rbi_policy",
          lifecycle_state: "active",
          mirror_status: "active",
          linked_map_module_id: null,
          linked_map_module_name: null,
        }}
      />,
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
