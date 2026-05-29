"use client";

import { useCallback, useEffect, useState } from "react";

import { deferAfterPaint } from "@/lib/deferAfterPaint";
import {
  HOLDINGS_CHANGED_EVENT,
  getSessionHoldings,
  type SessionHolding,
} from "@/lib/personalisation/sessionHoldings";

export function useSessionHoldings(): {
  holdings: SessionHolding[];
  refresh: () => Promise<void>;
  loading: boolean;
} {
  const [holdings, setHoldings] = useState<SessionHolding[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setHoldings(await getSessionHoldings());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    void deferAfterPaint(() => {
      if (!cancelled) void refresh();
    });
    const onChange = () => {
      void refresh();
    };
    window.addEventListener(HOLDINGS_CHANGED_EVENT, onChange);
    return () => {
      cancelled = true;
      window.removeEventListener(HOLDINGS_CHANGED_EVENT, onChange);
    };
  }, [refresh]);

  return { holdings, refresh, loading };
}
