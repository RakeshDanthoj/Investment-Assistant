"use client";

import { useCallback, useEffect, useState } from "react";

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
    void refresh();
    const onChange = () => {
      void refresh();
    };
    window.addEventListener(HOLDINGS_CHANGED_EVENT, onChange);
    return () => window.removeEventListener(HOLDINGS_CHANGED_EVENT, onChange);
  }, [refresh]);

  return { holdings, refresh, loading };
}
