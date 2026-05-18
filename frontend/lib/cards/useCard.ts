"use client";

import { useCallback, useEffect, useState } from "react";

import { getApiBaseUrl } from "@/lib/api";
import type { CardDetailResponse } from "@/lib/cards/threadTypes";

export type CardDetailStatus = "idle" | "loading" | "success" | "error";

export function useCard(cardId: string, view: "current" | "original") {
  const [status, setStatus] = useState<CardDetailStatus>("idle");
  const [data, setData] = useState<CardDetailResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setStatus("loading");
    setErrorMessage(null);
    try {
      const base = getApiBaseUrl();
      const params = new URLSearchParams({ view });
      const res = await fetch(`${base}/api/cards/${encodeURIComponent(cardId)}?${params}`, {
        cache: "no-store",
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `Card failed (${res.status})`);
      }
      const json = (await res.json()) as CardDetailResponse;
      setData(json);
      setStatus("success");
    } catch (e) {
      setStatus("error");
      setData(null);
      setErrorMessage(e instanceof Error ? e.message : "Could not load card.");
    }
  }, [cardId, view]);

  useEffect(() => {
    void load();
  }, [load]);

  return { status, data, errorMessage, refetch: load };
}
