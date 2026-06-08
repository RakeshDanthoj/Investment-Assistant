import { describeHttpFailure } from "@/lib/api";
import type { MapSectorListResponse, MapSectorSummaryDetail } from "@/lib/map/types";

import { getServerApiBaseUrl } from "./server";

export const MAP_REVALIDATE_SECONDS = 300;
export const MAP_STALE_TIME_MS = MAP_REVALIDATE_SECONDS * 1000;

async function fetchMapJson<T>(path: string, accessToken: string): Promise<T> {
  const endpoint = `${getServerApiBaseUrl()}${path}`;
  const response = await fetch(endpoint, {
    headers: { Authorization: `Bearer ${accessToken}` },
    next: { revalidate: MAP_REVALIDATE_SECONDS },
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(describeHttpFailure(response.status, text, "load The Map"));
  }
  return (await response.json()) as T;
}

export async function fetchMapSectorList(accessToken: string): Promise<MapSectorListResponse> {
  return fetchMapJson<MapSectorListResponse>("/api/map/sectors", accessToken);
}

export async function fetchMapSectorSummary(
  accessToken: string,
  slug: string,
): Promise<MapSectorSummaryDetail> {
  return fetchMapJson<MapSectorSummaryDetail>(
    `/api/map/sectors/${encodeURIComponent(slug)}`,
    accessToken,
  );
}

/** @deprecated Use fetchMapSectorSummary */
export async function fetchMapSectorDetail(
  accessToken: string,
  slug: string,
): Promise<MapSectorSummaryDetail> {
  return fetchMapSectorSummary(accessToken, slug);
}
