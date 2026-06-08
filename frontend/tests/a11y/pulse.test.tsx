/** @jest-environment jsdom */

import { render } from "@testing-library/react";
import { axe } from "jest-axe";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ prefetch: jest.fn(), push: jest.fn() }),
}));

jest.mock("../../lib/perf/useIntentPrefetch", () => ({
  useIntentPrefetch: () => ({
    onPointerEnter: jest.fn(),
    onPointerLeave: jest.fn(),
  }),
}));

import type { PulseCard } from "@/lib/cards/pulseTypes";
import { EventCard } from "@/app/(app)/pulse/_components/EventCard";
import { InsightPanel } from "@/app/(app)/pulse/_components/InsightPanel";
import { Topbar } from "@/app/(app)/pulse/_components/Topbar";

const sampleCard: PulseCard = {
  id: "c1",
  headline: "Domestic producers gain while aviation faces pressure",
  event_context: "Brent moves after supply disruption headlines.",
  category: "macro",
  lifecycle_state: "active",
  direction_confidence: { tier: "high", label: "High" },
  magnitude_confidence: { tier: "moderate", label: "Moderate" },
  instruments: [{ instrument_id: "INDIGO", signal_type: "headwind signal" }],
  insight_excerpt: "Summary…",
  last_reviewed_at: "2026-05-01T10:00:00.000Z",
  created_at: "2026-05-01T09:00:00.000Z",
  event_id: "e1",
};

describe("Pulse a11y", () => {
  it("EventCard has no axe violations", async () => {
    const { container } = render(
      <EventCard card={sampleCard} selected={false} onSelect={() => undefined} />,
    );
    expect(await axe(container)).toHaveNoViolations();
  });

  it("InsightPanel with card has no axe violations", async () => {
    const { container } = render(<InsightPanel card={sampleCard} />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it("Topbar has no axe violations", async () => {
    const { container } = render(
      <Topbar
        counts={3}
        lastUpdated="2026-05-01T10:00:00.000Z"
        categoryOptions={[{ id: "macro", label: "Macro" }]}
        selectedCategories={[]}
        onCategoriesChange={() => undefined}
      />,
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
