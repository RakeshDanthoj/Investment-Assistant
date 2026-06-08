import { describeHttpFailure, getApiBaseUrl } from "@/lib/api";
import type { MapSectorMatrixResponse, MapSectorSummaryDetail } from "@/lib/map/types";

export const MAP_STALE_TIME_MS = 300_000;

export const mapQueryKeys = {
  sectorSummary: (slug: string) => ["map", "sector", slug] as const,
  sectorMatrix: (slug: string) => ["map", "sector", slug, "matrix"] as const,
};

export async function fetchMapSectorSummaryClient(
  accessToken: string,
  slug: string,
  signal?: AbortSignal,
): Promise<MapSectorSummaryDetail> {
  const base = getApiBaseUrl().replace(/\/$/, "");
  const response = await fetch(`${base}/api/map/sectors/${encodeURIComponent(slug)}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    signal,
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(describeHttpFailure(response.status, text, "load sector summary"));
  }
  return (await response.json()) as MapSectorSummaryDetail;
}

export async function fetchMapSectorMatrixClient(
  accessToken: string,
  slug: string,
  signal?: AbortSignal,
): Promise<MapSectorMatrixResponse> {
  const base = getApiBaseUrl().replace(/\/$/, "");
  const response = await fetch(
    `${base}/api/map/sectors/${encodeURIComponent(slug)}/matrix`,
    {
      headers: { Authorization: `Bearer ${accessToken}` },
      signal,
    },
  );
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(describeHttpFailure(response.status, text, "load sector matrix"));
  }
  return (await response.json()) as MapSectorMatrixResponse;
}
