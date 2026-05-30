import { describeHttpFailure, getApiBaseUrl } from "@/lib/api";

export type ConfidenceInputBreakdown = {
  value: number;
  weight: number;
  detail: string;
};

export type ConfidenceBreakdownSource = {
  name: string;
  url: string;
  retrieved_at: string | null;
};

export type ConfidenceBreakdownInputs = {
  source_count: ConfidenceInputBreakdown;
  source_quality: ConfidenceInputBreakdown;
  factor_db_match: ConfidenceInputBreakdown;
  recency: ConfidenceInputBreakdown;
  unique_publisher: ConfidenceInputBreakdown;
};

export type ConfidenceBreakdownResponse = {
  event_id: string;
  confidence_raw: number;
  confidence_effective: number;
  tier: "high" | "medium" | "low";
  fog_active: boolean;
  fog_dampener: number | null;
  calibration_status: string;
  scorer_version: string;
  is_major: boolean;
  force_editorial_review: boolean;
  inputs: ConfidenceBreakdownInputs;
  sources: ConfidenceBreakdownSource[];
};

export class ConfidenceBreakdownFetchError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ConfidenceBreakdownFetchError";
  }
}

export function confidenceBreakdownUrl(eventId: string, apiBase?: string): string {
  const base = (apiBase ?? getApiBaseUrl()).replace(/\/$/, "");
  return `${base}/api/events/${encodeURIComponent(eventId)}/confidence-breakdown`;
}

export async function fetchConfidenceBreakdown(
  eventId: string,
  fetchImpl: typeof fetch = fetch,
  apiBase?: string,
): Promise<ConfidenceBreakdownResponse> {
  const endpoint = confidenceBreakdownUrl(eventId, apiBase);

  let response: Response;
  try {
    response = await fetchImpl(endpoint, { cache: "no-store" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not load confidence breakdown.";
    throw new ConfidenceBreakdownFetchError(message, 0);
  }

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new ConfidenceBreakdownFetchError(
      describeHttpFailure(response.status, text, "load the confidence breakdown"),
      response.status,
    );
  }

  return (await response.json()) as ConfidenceBreakdownResponse;
}
