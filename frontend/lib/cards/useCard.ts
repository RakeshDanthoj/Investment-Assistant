"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getApiBaseUrl } from "@/lib/api";
import type { CardDetailResponse } from "@/lib/cards/threadTypes";

export type CardDetailStatus = "idle" | "loading" | "success" | "error";

export type UseCardInitialState = {
  data?: CardDetailResponse | null;
  error?: string | null;
};

function isHydratedCurrentView(
  cardId: string,
  view: "current" | "original",
  initial?: UseCardInitialState,
): initial is { data: CardDetailResponse } {
  return (
    view === "current" &&
    initial?.data != null &&
    initial.data.card_id === cardId &&
    initial.data.view === "current"
  );
}

function isHydratedCurrentError(
  view: "current" | "original",
  initial?: UseCardInitialState,
): initial is { error: string } {
  return view === "current" && Boolean(initial?.error);
}

export function useCard(
  cardId: string,
  view: "current" | "original",
  initial?: UseCardInitialState,
) {
  const [status, setStatus] = useState<CardDetailStatus>(() => {
    if (isHydratedCurrentError(view, initial)) return "error";
    if (isHydratedCurrentView(cardId, view, initial)) return "success";
    return "idle";
  });
  const [data, setData] = useState<CardDetailResponse | null>(() => {
    if (isHydratedCurrentView(cardId, view, initial)) return initial.data;
    return null;
  });
  const [errorMessage, setErrorMessage] = useState<string | null>(() => {
    if (isHydratedCurrentError(view, initial)) return initial.error ?? null;
    return null;
  });
  const [contextRevealed, setContextRevealed] = useState(false);
  const initialRef = useRef(initial);
  initialRef.current = initial;

  useEffect(() => {
    setContextRevealed(false);
  }, [cardId, view]);

  const revealContext = useCallback(() => {
    setContextRevealed(true);
  }, []);

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
    const init = initialRef.current;

    if (isHydratedCurrentView(cardId, view, init)) {
      setData(init.data);
      setStatus("success");
      setErrorMessage(null);
      return;
    }

    if (isHydratedCurrentError(view, init)) {
      setData(null);
      setStatus("error");
      setErrorMessage(init.error ?? null);
      return;
    }

    void load();
  }, [cardId, view, load]);

  return { status, data, errorMessage, refetch: load, contextRevealed, revealContext };
}
