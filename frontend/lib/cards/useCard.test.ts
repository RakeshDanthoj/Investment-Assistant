/** @jest-environment jsdom */

import { renderHook, waitFor } from "@testing-library/react";

import type { CardDetailResponse } from "@/lib/cards/threadTypes";
import { useCard } from "@/lib/cards/useCard";

const baseCard: CardDetailResponse = {
  view: "current",
  card_id: "card-123",
  event_id: "event-1",
  title: "RBI holds rates steady",
  event_title: "Monetary policy unchanged",
  category: "macro",
  lifecycle_state: "active",
  lifecycle_tracker: [],
  week_number: 1,
  direction_confidence: { tier: "high", label: "High" },
  magnitude_confidence: { tier: "moderate", label: "Moderate" },
  event_confidence_score: 72,
  insight_layer: "Insight",
  context_layer: "Context",
  context_steps: [],
  evidence_layer: {},
  evidence_rows: [],
  evidence_markdown: "",
  evidence_macro_stub: "",
  dissenting_view: "",
  framework_behind_this: "",
  instruments: [],
  signals: [],
  confidence_composition: {
    measured: 0,
    modelled: 0,
    judged: 0,
    counts: { measured: 0, modelled: 0, judged: 0 },
  },
  bias_audit: { flags: [], monitored: [] },
  published_at: null,
};

describe("useCard SSR hydration", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("hydrates current view from initialData without calling fetch", async () => {
    const { result } = renderHook(() =>
      useCard("card-123", "current", { data: baseCard }),
    );

    expect(result.current.status).toBe("success");
    expect(result.current.data?.title).toBe("RBI holds rates steady");
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("hydrates current view error from initialError without calling fetch", async () => {
    const { result } = renderHook(() =>
      useCard("card-123", "current", { error: "Card not found" }),
    );

    expect(result.current.status).toBe("error");
    expect(result.current.errorMessage).toBe("Card not found");
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("client-fetches when toggling to original view", async () => {
    const originalCard = { ...baseCard, view: "original" as const, title: "Original headline" };
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => originalCard,
    });

    const { result, rerender } = renderHook(
      ({ view }: { view: "current" | "original" }) =>
        useCard("card-123", view, { data: baseCard }),
      { initialProps: { view: "current" as "current" | "original" } },
    );

    expect(global.fetch).not.toHaveBeenCalled();

    rerender({ view: "original" as "current" | "original" });

    await waitFor(() => {
      expect(result.current.status).toBe("success");
    });

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/cards/card-123"),
      expect.objectContaining({ cache: "no-store" }),
    );
    expect(result.current.data?.title).toBe("Original headline");
  });

  it("reuses initialData when toggling back to current without refetching", async () => {
    const originalCard = { ...baseCard, view: "original" as const, title: "Original headline" };
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => originalCard,
    });

    const { result, rerender } = renderHook(
      ({ view }: { view: "current" | "original" }) =>
        useCard("card-123", view, { data: baseCard }),
      { initialProps: { view: "current" as "current" | "original" } },
    );

    rerender({ view: "original" as "current" | "original" });
    await waitFor(() => {
      expect(result.current.data?.title).toBe("Original headline");
    });

    rerender({ view: "current" as "current" | "original" });

    expect(result.current.status).toBe("success");
    expect(result.current.data?.title).toBe("RBI holds rates steady");
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });
});
