import { describeHttpFailure } from "@/lib/api";
import type {
  MirrorPredictionsResponse,
  MirrorReasoningGapsResponse,
  MirrorStatsResponse,
  MirrorStreakResponse,
  MirrorUnreadNotification,
  MirrorUnreadNotificationsResponse,
} from "@/lib/mirror/types";

import { getServerApiBaseUrl } from "./server";

export type MirrorInitialPayload = {
  stats: MirrorStatsResponse;
  predictions: MirrorPredictionsResponse;
  streak: MirrorStreakResponse;
  gaps: MirrorReasoningGapsResponse;
  unreadNotifications: MirrorUnreadNotification[];
};

async function fetchMirrorJson<T>(
  path: string,
  accessToken: string,
): Promise<T> {
  const endpoint = `${getServerApiBaseUrl()}${path}`;
  const response = await fetch(endpoint, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(describeHttpFailure(response.status, text, "load The Mirror"));
  }
  return (await response.json()) as T;
}

export async function fetchMirrorInitialData(
  accessToken: string,
  statusFilter: string | null,
): Promise<MirrorInitialPayload> {
  const statusQuery = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";

  const [stats, predictions, streak, gaps, unread] = await Promise.all([
    fetchMirrorJson<MirrorStatsResponse>("/api/mirror/stats", accessToken),
    fetchMirrorJson<MirrorPredictionsResponse>(
      `/api/mirror/predictions${statusQuery}`,
      accessToken,
    ),
    fetchMirrorJson<MirrorStreakResponse>("/api/mirror/streak", accessToken),
    fetchMirrorJson<MirrorReasoningGapsResponse>("/api/mirror/gaps", accessToken),
    fetchMirrorJson<MirrorUnreadNotificationsResponse>(
      "/api/mirror/notifications/unread",
      accessToken,
    ),
  ]);

  return {
    stats,
    predictions,
    streak,
    gaps,
    unreadNotifications: unread.items ?? [],
  };
}
