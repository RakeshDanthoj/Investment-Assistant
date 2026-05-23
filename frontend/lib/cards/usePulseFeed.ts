"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getApiBaseUrl } from "@/lib/api";
import type { PulseCard, PulseFeedResponse } from "@/lib/cards/pulseTypes";
import { getStoredSessionId } from "@/lib/sessionProfile";

export type PulseFeedStatus = "idle" | "loading" | "success" | "error";

export type UsePulseFeedOptions = {
  initialData?: PulseFeedResponse | null;
  initialCategoryQuery?: string;
};

export function usePulseFeed(selectedCategories: string[], options?: UsePulseFeedOptions) {
  const categoryQuery = useMemo(() => {
    if (!selectedCategories.length) return "";
    return selectedCategories.slice().sort().join(",");
  }, [selectedCategories]);

  const skipInitialFetchRef = useRef(
    options?.initialData != null &&
      (options.initialCategoryQuery ?? "") === categoryQuery,
  );

  const [status, setStatus] = useState<PulseFeedStatus>(() =>
    options?.initialData ? "success" : "idle",
  );
  const [data, setData] = useState<PulseFeedResponse | null>(options?.initialData ?? null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(() => {
    const cards = options?.initialData?.cards;
    if (!cards?.length) return null;
    return cards[0].id;
  });

  const load = useCallback(async () => {
    setStatus("loading");
    setErrorMessage(null);
    try {
      const base = getApiBaseUrl();
      const params = new URLSearchParams();
      if (categoryQuery) params.set("category", categoryQuery);
      const sid = getStoredSessionId();
      if (sid) params.set("session_id", sid);
      const url = `${base}/api/feed${params.toString() ? `?${params}` : ""}`;
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `Feed failed (${res.status})`);
      }
      const json = (await res.json()) as PulseFeedResponse;
      setData(json);
      setStatus("success");
      if (json.cards.length) {
        setSelectedId((prev) => {
          if (prev && json.cards.some((c) => c.id === prev)) return prev;
          return json.cards[0].id;
        });
      } else {
        setSelectedId(null);
      }
    } catch (e) {
      setStatus("error");
      setData(null);
      setErrorMessage(e instanceof Error ? e.message : "Could not load feed.");
    }
  }, [categoryQuery]);

  useEffect(() => {
    if (skipInitialFetchRef.current) {
      skipInitialFetchRef.current = false;
      return;
    }
    void load();
  }, [load]);

  const selectedCard: PulseCard | null = useMemo(() => {
    if (!data?.cards?.length) return null;
    if (selectedId) {
      const found = data.cards.find((c) => c.id === selectedId);
      if (found) return found;
    }
    return data.cards[0];
  }, [data, selectedId]);

  return {
    status,
    data,
    errorMessage,
    selectedId,
    setSelectedId,
    selectedCard,
    refetch: load,
  };
}
