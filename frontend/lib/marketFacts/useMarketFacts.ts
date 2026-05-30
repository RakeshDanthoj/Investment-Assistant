"use client";

import { useCallback, useEffect, useState } from "react";

import { describeFetchFailure, describeHttpFailure, getApiBaseUrl } from "@/lib/api";

import type { MarketFactsResponse } from "./types";

export type MarketFactsStatus = "idle" | "loading" | "success" | "error";

export function useMarketFacts() {
  const [status, setStatus] = useState<MarketFactsStatus>("idle");
  const [data, setData] = useState<MarketFactsResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setStatus("loading");
    setErrorMessage(null);
    try {
      const base = getApiBaseUrl().replace(/\/$/, "");
      const res = await fetch(`${base}/api/market-facts`, { cache: "no-store" });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(describeHttpFailure(res.status, text, "load market facts"));
      }
      const body = (await res.json()) as MarketFactsResponse;
      setData(body);
      setStatus("success");
    } catch (error) {
      setData(null);
      setStatus("error");
      setErrorMessage(describeFetchFailure(error));
    }
  }, []);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { status, data, errorMessage, refetch };
}
