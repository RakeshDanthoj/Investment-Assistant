"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { describeFetchFailure, describeHttpFailure, getApiBaseUrl } from "@/lib/api";
import type { PulseCard, PulseFeedResponse } from "@/lib/cards/pulseTypes";
import {
  getPersonalisationToken,
  HOLDINGS_CHANGED_EVENT,
} from "@/lib/personalisation/sessionHoldings";
import { getStoredSessionId } from "@/lib/sessionProfile";

export type PulseFeedStatus = "idle" | "loading" | "success" | "error";

export type UsePulseFeedOptions = {
  initialData?: PulseFeedResponse | null;
  initialCategoryQuery?: string;
  initialSessionId?: string | null;
  initialPersonalisationToken?: string | null;
};

const STALE_MS = 60_000;
const VERY_OLD_MS = 24 * 60 * 60 * 1000;

export function pulseFeedQueryKey(
  categoryQuery: string,
  sessionId: string | null,
  personalisationToken: string | null,
) {
  return ["pulse-feed", categoryQuery, sessionId ?? "", personalisationToken ?? ""] as const;
}

function feedAgeMs(lastUpdated: string | null | undefined): number | null {
  if (!lastUpdated) return null;
  const parsed = Date.parse(lastUpdated);
  if (Number.isNaN(parsed)) return null;
  return Date.now() - parsed;
}

function isFeedStale(lastUpdated: string | null | undefined): boolean {
  const age = feedAgeMs(lastUpdated);
  return age === null || age > STALE_MS;
}

export function isFeedVeryOld(lastUpdated: string | null | undefined): boolean {
  const age = feedAgeMs(lastUpdated);
  return age !== null && age > VERY_OLD_MS;
}

async function fetchPulseFeedClient(categoryQuery: string): Promise<PulseFeedResponse> {
  const base = getApiBaseUrl();
  const params = new URLSearchParams();
  if (categoryQuery) params.set("category", categoryQuery);
  const sid = getStoredSessionId();
  if (sid) params.set("session_id", sid);
  const token = await getPersonalisationToken();
  if (token) params.set("personalisation_token", token);
  const url = `${base}/api/feed${params.toString() ? `?${params}` : ""}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(describeHttpFailure(res.status, t, "load the feed"));
  }
  return (await res.json()) as PulseFeedResponse;
}

export function usePulseFeed(selectedCategories: string[], options?: UsePulseFeedOptions) {
  const queryClient = useQueryClient();

  const categoryQuery = useMemo(() => {
    if (!selectedCategories.length) return "";
    return selectedCategories.slice().sort().join(",");
  }, [selectedCategories]);

  const ssrSessionId = options?.initialSessionId ?? null;
  const ssrToken = options?.initialPersonalisationToken ?? null;
  const ssrCategory = options?.initialCategoryQuery ?? "";

  const hydratedFromServer =
    options?.initialData != null && ssrCategory === categoryQuery;

  const [selectedId, setSelectedId] = useState<string | null>(() => {
    const cards = options?.initialData?.cards;
    if (!cards?.length) return null;
    return cards[0].id;
  });

  const [tokenMismatch, setTokenMismatch] = useState(false);
  const checkedTokenRef = useRef(false);

  useEffect(() => {
    if (!hydratedFromServer || checkedTokenRef.current) return;
    checkedTokenRef.current = true;
    void (async () => {
      const clientToken = await getPersonalisationToken();
      if (clientToken && clientToken !== (ssrToken ?? null)) {
        setTokenMismatch(true);
      }
    })();
  }, [hydratedFromServer, ssrToken]);

  const queryKey = pulseFeedQueryKey(categoryQuery, ssrSessionId, ssrToken);

  const query = useQuery({
    queryKey,
    queryFn: () => fetchPulseFeedClient(categoryQuery),
    initialData: hydratedFromServer ? (options?.initialData ?? undefined) : undefined,
    staleTime: STALE_MS,
    refetchOnWindowFocus: false,
    refetchOnMount: (q) => {
      if (tokenMismatch) return true;
      if (!hydratedFromServer) return true;
      return isFeedStale(q.state.data?.last_updated);
    },
  });

  useEffect(() => {
    if (!tokenMismatch) return;
    void query.refetch();
  }, [tokenMismatch, query]);

  const load = useCallback(async () => {
    await query.refetch();
  }, [query]);

  useEffect(() => {
    const onHoldingsChanged = () => {
      void queryClient.invalidateQueries({ queryKey: ["pulse-feed"] });
    };
    window.addEventListener(HOLDINGS_CHANGED_EVENT, onHoldingsChanged);
    return () => window.removeEventListener(HOLDINGS_CHANGED_EVENT, onHoldingsChanged);
  }, [queryClient]);

  useEffect(() => {
    const cards = query.data?.cards;
    if (!cards?.length) {
      if (query.data && cards?.length === 0) setSelectedId(null);
      return;
    }
    setSelectedId((prev) => {
      if (prev && cards.some((c) => c.id === prev)) return prev;
      return cards[0].id;
    });
  }, [query.data]);

  const status: PulseFeedStatus = useMemo(() => {
    if (query.isPending && !query.data) return "loading";
    if (query.isError && !query.data) return "error";
    if (query.data) return "success";
    return "idle";
  }, [query.data, query.isError, query.isPending]);

  const errorMessage = useMemo(() => {
    if (!query.isError) return null;
    const message = describeFetchFailure(query.error, "load the feed");
    if (query.data?.cards?.length) return null;
    return message;
  }, [query.data?.cards?.length, query.error, query.isError]);

  const selectedCard: PulseCard | null = useMemo(() => {
    const cards = query.data?.cards;
    if (!cards?.length) return null;
    if (selectedId) {
      const found = cards.find((c) => c.id === selectedId);
      if (found) return found;
    }
    return cards[0];
  }, [query.data, selectedId]);

  const showStaleBanner = isFeedVeryOld(query.data?.last_updated);

  return {
    status,
    data: query.data ?? null,
    errorMessage,
    selectedId,
    setSelectedId,
    selectedCard,
    refetch: load,
    showStaleBanner,
    isFetching: query.isFetching,
  };
}
