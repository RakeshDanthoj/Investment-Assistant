import { describeHttpFailure } from "@/lib/api";
import type { MapSectorDetailResponse, MapSectorListResponse } from "@/lib/map/types";

import { getServerApiBaseUrl } from "./server";

async function fetchMapJson<T>(path: string, accessToken: string): Promise<T> {
  const endpoint = `${getServerApiBaseUrl()}${path}`;
  const response = await fetch(endpoint, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
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

export async function fetchMapSectorDetail(
  accessToken: string,
  slug: string,
): Promise<MapSectorDetailResponse> {
  return fetchMapJson<MapSectorDetailResponse>(
    `/api/map/sectors/${encodeURIComponent(slug)}`,
    accessToken,
  );
}
