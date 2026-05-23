import type { CardDetailResponse } from "@/lib/cards/threadTypes";
import type { PulseFeedResponse } from "@/lib/cards/pulseTypes";

/** Direct API origin for RSC fetches — bypasses the browser `/backend` rewrite. */
export function getServerApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, "");
  return configured || "http://127.0.0.1:8000";
}

export class CardDetailFetchError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "CardDetailFetchError";
  }
}

export type PulseFeedFetchOptions = {
  category?: string;
  sessionId?: string;
};

export async function fetchPulseFeed(options?: PulseFeedFetchOptions): Promise<PulseFeedResponse> {
  const params = new URLSearchParams();
  if (options?.category) params.set("category", options.category);
  if (options?.sessionId) params.set("session_id", options.sessionId);
  const qs = params.toString();
  const endpoint = `${getServerApiBaseUrl()}/api/feed${qs ? `?${qs}` : ""}`;

  let response: Response;
  try {
    response = await fetch(endpoint, { cache: "no-store" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not load feed.";
    throw new Error(message);
  }

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(text || `Feed failed (${response.status})`);
  }

  return (await response.json()) as PulseFeedResponse;
}

export async function fetchCardDetail(
  cardId: string,
  view: "current" | "original" = "current",
): Promise<CardDetailResponse> {
  const params = new URLSearchParams({ view });
  const endpoint = `${getServerApiBaseUrl()}/api/cards/${encodeURIComponent(cardId)}?${params}`;

  let response: Response;
  try {
    response = await fetch(endpoint, { cache: "no-store" });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not load card.";
    throw new CardDetailFetchError(message, 0);
  }

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new CardDetailFetchError(text || `Card failed (${response.status})`, response.status);
  }

  return (await response.json()) as CardDetailResponse;
}
