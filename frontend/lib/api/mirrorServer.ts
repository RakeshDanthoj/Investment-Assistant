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
  /** Epoch ms when SSR payload was fetched (PI-S2 stale banner). */
  fetchedAt?: number;
};

type MirrorDashboardResponse = MirrorInitialPayload & {
  unread_notifications: MirrorUnreadNotificationsResponse;
};

export async function fetchMirrorInitialData(
  accessToken: string,
  statusFilter: string | null,
): Promise<MirrorInitialPayload> {
  const statusQuery = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";
  const endpoint = `${getServerApiBaseUrl()}/api/mirror/dashboard${statusQuery}`;

  const response = await fetch(endpoint, {
    headers: { Authorization: `Bearer ${accessToken}` },
    next: { revalidate: 60 },
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(describeHttpFailure(response.status, text, "load The Mirror"));
  }

  const body = (await response.json()) as MirrorDashboardResponse;
  return {
    stats: body.stats,
    predictions: body.predictions,
    streak: body.streak,
    gaps: body.gaps,
    unreadNotifications: body.unread_notifications.items ?? [],
    fetchedAt: Date.now(),
  };
}
