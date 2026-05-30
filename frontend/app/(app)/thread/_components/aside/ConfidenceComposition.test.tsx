/** @jest-environment jsdom */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ConfidenceComposition } from "./ConfidenceComposition";
import type { ConfidenceBreakdownResponse } from "@/lib/api/confidenceBreakdown";

const breakdownFixture: ConfidenceBreakdownResponse = {
  event_id: "evt-1",
  confidence_raw: 0.82,
  confidence_effective: 0.49,
  tier: "medium",
  fog_active: true,
  fog_dampener: 0.6,
  calibration_status: "provisional",
  scorer_version: "confidence_scorer.v1",
  is_major: false,
  force_editorial_review: true,
  inputs: {
    source_count: { value: 0.67, weight: 0.3, detail: "2 sources post-dedup" },
    source_quality: { value: 0.8, weight: 0.3, detail: "primary_source=rbi_rss" },
    factor_db_match: { value: 1, weight: 0.25, detail: "2 factors" },
    recency: { value: 1, weight: 0.05, detail: "first_seen=2025-06-01T10:00:00+00:00" },
    unique_publisher: { value: 0.67, weight: 0.1, detail: "2 publishers (domain-level)" },
  },
  sources: [
    {
      name: "rbi_rss",
      url: "https://example.com/story",
      retrieved_at: "2025-06-01T10:00:00+00:00",
    },
  ],
};

describe("ConfidenceComposition", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("renders breakdown fixture after expand", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => breakdownFixture,
    });

    render(
      <ConfidenceComposition measured={0.4} modelled={0.35} judged={0.25} eventId="evt-1" />,
    );

    expect(global.fetch).not.toHaveBeenCalled();

    await userEvent.click(screen.getByRole("button", { name: /why this confidence tier/i }));

    await waitFor(() => {
      expect(screen.getByTestId("confidence-breakdown-panel")).toBeInTheDocument();
    });

    expect(screen.getByText(/Medium tier/i)).toBeInTheDocument();
    expect(screen.getByText(/Source count/i)).toBeInTheDocument();
    expect(screen.getByText(/Source quality/i)).toBeInTheDocument();
    expect(screen.getByText(/Factor DB match/i)).toBeInTheDocument();
    expect(screen.getByText(/Recency/i)).toBeInTheDocument();
    expect(screen.getByText(/Unique publishers/i)).toBeInTheDocument();
    expect(screen.getByText(/2 sources post-dedup/i)).toBeInTheDocument();
    expect(screen.getByText(/primary_source=rbi_rss/i)).toBeInTheDocument();
    expect(screen.getByText(/2 factors/i)).toBeInTheDocument();
    expect(screen.getByText(/2 publishers \(domain-level\)/i)).toBeInTheDocument();
    expect(screen.getByTestId("confidence-escalation-badge")).toBeInTheDocument();
    expect(screen.getByTestId("confidence-fow-callout")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("shows error state on 404", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 404,
      text: async () => '{"detail":"Event not found"}',
    });

    render(
      <ConfidenceComposition measured={0.4} modelled={0.35} judged={0.25} eventId="missing" />,
    );

    await userEvent.click(screen.getByRole("button", { name: /why this confidence tier/i }));

    await waitFor(() => {
      expect(screen.getByTestId("confidence-breakdown-error")).toBeInTheDocument();
    });
  });
});
