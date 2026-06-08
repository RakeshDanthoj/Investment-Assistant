import { describeHttpFailure } from "@/lib/api";
import type { LensQueriesResponse } from "@/lib/lens/types";

import { getServerApiBaseUrl } from "./server";

export async function fetchLensHistory(accessToken: string): Promise<LensQueriesResponse> {
  const endpoint = `${getServerApiBaseUrl()}/api/lens/queries/me`;

  const response = await fetch(endpoint, {
    headers: { Authorization: `Bearer ${accessToken}` },
    next: { revalidate: 60 },
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(describeHttpFailure(response.status, text, "load Lens history"));
  }

  return (await response.json()) as LensQueriesResponse;
}
