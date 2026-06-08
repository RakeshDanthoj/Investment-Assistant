/** @jest-environment jsdom */

const mockPrefetch = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ prefetch: mockPrefetch, push: jest.fn() }),
}));

jest.mock("../../../../lib/perf/useIntentPrefetch", () => ({
  useIntentPrefetch: () => ({
    onPointerEnter: jest.fn(),
    onPointerLeave: jest.fn(),
  }),
}));

import { fireEvent, render, screen } from "@testing-library/react";

import type { PulseCard } from "@/lib/cards/pulseTypes";

import { EventCard } from "./EventCard";

const baseCard: PulseCard = {
  id: "c1",
  headline: "Domestic producers gain while aviation faces pressure",
  event_context: "Brent moves after supply disruption headlines.",
  category: "macro",
  lifecycle_state: "active",
  direction_confidence: { tier: "high", label: "High" },
  magnitude_confidence: { tier: "moderate", label: "Moderate" },
  instruments: [{ instrument_id: "INDIGO", signal_type: "headwind signal" }],
  insight_excerpt: "Summary…",
  last_reviewed_at: null,
  created_at: null,
  event_id: "e1",
};

describe("EventCard", () => {
  it("renders separate direction and magnitude confidence dots", () => {
    render(
      <EventCard
        card={baseCard}
        selected={false}
        onSelect={() => {
          /* noop */
        }}
      />,
    );
    expect(screen.getByText("Direction")).toBeInTheDocument();
    expect(screen.getByText("Magnitude")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Moderate")).toBeInTheDocument();
  });

  it("shows resolved pill without hiding card content", () => {
    let clicked = false;
    render(
      <EventCard
        card={{ ...baseCard, lifecycle_state: "resolved" }}
        selected={false}
        onSelect={() => {
          clicked = true;
        }}
      />,
    );
    expect(screen.getByText("Resolved")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button"));
    expect(clicked).toBe(true);
  });

  it("applies inset selection accent when selected", () => {
    render(
      <EventCard
        card={baseCard}
        selected
        onSelect={() => {
          /* noop */
        }}
      />,
    );
    const card = screen.getByRole("button");
    expect(card.firstElementChild?.className).toMatch(/bg-finnwise-blue-tint/);
    expect(card.firstElementChild?.className).toMatch(/box-shadow:inset_3px/);
  });
});
