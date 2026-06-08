"use client";

import { useQuery } from "@tanstack/react-query";
import { useRef } from "react";

import { describeFetchFailure, describeHttpFailure, getApiBaseUrl } from "@/lib/api";
import type { MirrorInitialPayload } from "@/lib/api/mirrorServer";
import type {
  MirrorPredictionsResponse,
  MirrorReasoningGapsResponse,
  MirrorStatsResponse,
  MirrorStreakResponse,
  MirrorUnreadNotification,
  MirrorUnreadNotificationsResponse,
} from "@/lib/mirror/types";

export const MIRROR_STALE_MS = 60_000;
export const MIRROR_STALE_BANNER_MS = 24 * 60 * 60 * 1000;

export type MirrorDashboardData = MirrorInitialPayload & {
  fetchedAt: number;
};

type DashboardApiResponse = {
  stats: MirrorStatsResponse;
  predictions: MirrorPredictionsResponse;
  streak: MirrorStreakResponse;
  gaps: MirrorReasoningGapsResponse;
  unread_notifications: MirrorUnreadNotificationsResponse;
};

function toDashboardData(body: DashboardApiResponse, fetchedAt: number): MirrorDashboardData {
  return {
    stats: body.stats,
    predictions: body.predictions,
    streak: body.streak,
    gaps: body.gaps,
    unreadNotifications: body.unread_notifications.items ?? [],
    fetchedAt,
  };
}

export type UseMirrorDashboardOptions = {
  accessToken: string | null;
  initialPayload?: MirrorInitialPayload | null;
  initialStatusFilter?: string | null;
  enabled?: boolean;
};

export function useMirrorDashboard(options: UseMirrorDashboardOptions) {
  const {
    accessToken,
    initialPayload = null,
    initialStatusFilter = null,
    enabled = true,
  } = options;

  const hydratedFromServer = initialPayload != null;
  const ssrFetchedAt = initialPayload?.fetchedAt ?? Date.now();
  const skipInitialRefetchRef = useRef(hydratedFromServer);

  const placeholder: MirrorDashboardData | undefined = initialPayload
    ? {
        ...initialPayload,
        fetchedAt: initialPayload.fetchedAt ?? ssrFetchedAt,
      }
    : undefined;

  const query = useQuery({
    queryKey: ["mirror", "dashboard", initialStatusFilter ?? null] as const,
    queryFn: async (): Promise<MirrorDashboardData> => {
      if (!accessToken) {
        throw new Error("Sign in to view your prediction history.");
      }
      const base = getApiBaseUrl();
      const statusQuery =
        initialStatusFilter != null && initialStatusFilter !== ""
          ? `?status=${encodeURIComponent(initialStatusFilter)}`
          : "";
      const res = await fetch(`${base}/api/mirror/dashboard${statusQuery}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
        cache: "no-store",
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(describeHttpFailure(res.status, text, "load The Mirror"));
      }
      const body = (await res.json()) as DashboardApiResponse;
      return toDashboardData(body, Date.now());
    },
    enabled: enabled && Boolean(accessToken),
    staleTime: MIRROR_STALE_MS,
    placeholderData: placeholder,
    refetchOnMount: (q) => {
      if (skipInitialRefetchRef.current) {
        skipInitialRefetchRef.current = false;
        return Date.now() - ssrFetchedAt > MIRROR_STALE_MS;
      }
      const updatedAt = q.state.dataUpdatedAt;
      if (!updatedAt) return true;
      return Date.now() - updatedAt > MIRROR_STALE_MS;
    },
    meta: {
      parseError: (error: unknown) => describeFetchFailure(error, "load The Mirror"),
    },
  });

  const lastSuccessfulFetchAt = query.dataUpdatedAt || query.data?.fetchedAt || ssrFetchedAt;
  const showStaleBanner = Date.now() - lastSuccessfulFetchAt > MIRROR_STALE_BANNER_MS;

  return {
    data: query.data ?? null,
    isLoading: query.isLoading && !query.data,
    isFetching: query.isFetching,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
    showStaleBanner,
    isHydratedFromServer: hydratedFromServer,
  };
}
