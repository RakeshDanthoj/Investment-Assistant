import {
  ConfidenceBreakdownFetchError,
  confidenceBreakdownUrl,
  fetchConfidenceBreakdown,
  type ConfidenceBreakdownResponse,
} from "./confidenceBreakdown";

const fixture: ConfidenceBreakdownResponse = {
  event_id: "evt-1",
  confidence_raw: 0.82,
  confidence_effective: 0.49,
  tier: "medium",
  fog_active: true,
  fog_dampener: 0.6,
  calibration_status: "provisional",
  scorer_version: "confidence_scorer.v1",
  is_major: false,
  force_editorial_review: false,
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

describe("confidenceBreakdownUrl", () => {
  it("builds the breakdown endpoint path", () => {
    expect(confidenceBreakdownUrl("abc-123", "https://api.example.com")).toBe(
      "https://api.example.com/api/events/abc-123/confidence-breakdown",
    );
  });
});

describe("fetchConfidenceBreakdown", () => {
  it("returns parsed breakdown payload", async () => {
    const fetchImpl = jest.fn(async () => ({
      ok: true,
      json: async () => fixture,
    })) as unknown as typeof fetch;

    const data = await fetchConfidenceBreakdown("evt-1", fetchImpl, "https://api.example.com");

    expect(data.confidence_raw).toBe(0.82);
    expect(data.inputs.source_count.detail).toBe("2 sources post-dedup");
    expect(data.sources[0]?.retrieved_at).toBe("2025-06-01T10:00:00+00:00");
    expect(fetchImpl).toHaveBeenCalledWith(
      "https://api.example.com/api/events/evt-1/confidence-breakdown",
      { cache: "no-store" },
    );
  });

  it("throws ConfidenceBreakdownFetchError on 404", async () => {
    const fetchImpl = jest.fn(async () => ({
      ok: false,
      status: 404,
      text: async () => '{"detail":"Event not found"}',
    })) as unknown as typeof fetch;

    await expect(
      fetchConfidenceBreakdown("missing", fetchImpl, "https://api.example.com"),
    ).rejects.toMatchObject({
      name: "ConfidenceBreakdownFetchError",
      status: 404,
    });
  });
});

describe("ConfidenceBreakdownFetchError", () => {
  it("preserves HTTP status", () => {
    const error = new ConfidenceBreakdownFetchError("fail", 503);
    expect(error).toBeInstanceOf(Error);
    expect(error.status).toBe(503);
  });
});
