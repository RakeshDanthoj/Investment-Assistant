import { renderHook, waitFor } from "@testing-library/react";

import type { PulseFeedResponse } from "@/lib/cards/pulseTypes";
import { usePulseFeed } from "@/lib/cards/usePulseFeed";

const sampleFeed: PulseFeedResponse = {
  cards: [
    {
      id: "card-1",
      headline: "RBI holds rates",
      event_context: "Policy",
      category: "rbi_policy",
      lifecycle_state: "active",
      direction_confidence: { tier: "high", label: "High" },
      magnitude_confidence: { tier: "medium", label: "Medium" },
      instruments: [],
      insight_excerpt: "Rates unchanged.",
      last_reviewed_at: null,
      created_at: "2026-05-01T00:00:00Z",
      event_id: "evt-1",
    },
  ],
  fog_of_war: false,
  profile: null,
  last_updated: "2026-05-01T00:00:00Z",
  counts: 1,
};

describe("usePulseFeed", () => {
  const fetchMock = jest.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    global.fetch = fetchMock as typeof fetch;
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000";
  });

  it("skips the initial client fetch when hydrated from SSR data", async () => {
    const { result } = renderHook(() =>
      usePulseFeed([], { initialData: sampleFeed, initialCategoryQuery: "" }),
    );

    await waitFor(() => {
      expect(result.current.status).toBe("success");
    });

    expect(fetchMock).not.toHaveBeenCalled();
    expect(result.current.data).toEqual(sampleFeed);
  });

  it("refetches when category filters change after SSR hydration", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ ...sampleFeed, counts: 0, cards: [] }),
    });

    const { result, rerender } = renderHook(
      ({ categories }: { categories: string[] }) =>
        usePulseFeed(categories, { initialData: sampleFeed, initialCategoryQuery: "" }),
      { initialProps: { categories: [] as string[] } },
    );

    await waitFor(() => {
      expect(result.current.status).toBe("success");
    });
    expect(fetchMock).not.toHaveBeenCalled();

    rerender({ categories: ["macro"] });

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toContain("category=macro");
  });

  it("fetches on mount when SSR data is unavailable", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => sampleFeed,
    });

    renderHook(() => usePulseFeed([]));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });
  });
});
