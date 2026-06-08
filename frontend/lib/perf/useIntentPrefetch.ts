"use client";

import { useCallback, useEffect, useRef } from "react";

const DWELL_MS = 250;
const MAX_IN_FLIGHT = 2;
const LRU_SIZE = 10;

let inFlightCount = 0;
const recentKeys: string[] = [];

function touchLru(key: string): void {
  const existingIndex = recentKeys.indexOf(key);
  if (existingIndex >= 0) {
    recentKeys.splice(existingIndex, 1);
  }
  recentKeys.unshift(key);
  while (recentKeys.length > LRU_SIZE) {
    recentKeys.pop();
  }
}

function wasRecentlyPrefetched(key: string): boolean {
  return recentKeys.includes(key);
}

export type IntentPrefetchFetchFn = (signal: AbortSignal) => Promise<void>;

export function useIntentPrefetch() {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const focusedKeyRef = useRef<string | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const abortInFlight = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const onPointerLeave = useCallback(() => {
    clearTimer();
  }, [clearTimer]);

  const onPointerEnter = useCallback(
    (targetKey: string, fetchFn: IntentPrefetchFetchFn) => {
      clearTimer();
      abortInFlight();
      focusedKeyRef.current = targetKey;

      if (wasRecentlyPrefetched(targetKey)) {
        return;
      }

      timerRef.current = setTimeout(() => {
        timerRef.current = null;
        if (focusedKeyRef.current !== targetKey) {
          return;
        }
        if (inFlightCount >= MAX_IN_FLIGHT) {
          return;
        }

        const controller = new AbortController();
        abortRef.current = controller;
        inFlightCount += 1;

        fetchFn(controller.signal)
          .then(() => {
            if (focusedKeyRef.current === targetKey && !controller.signal.aborted) {
              touchLru(targetKey);
            }
          })
          .catch((error: unknown) => {
            if (error instanceof DOMException && error.name === "AbortError") {
              return;
            }
            if (error instanceof Error && error.name === "AbortError") {
              return;
            }
          })
          .finally(() => {
            inFlightCount = Math.max(0, inFlightCount - 1);
            if (abortRef.current === controller) {
              abortRef.current = null;
            }
          });
      }, DWELL_MS);
    },
    [abortInFlight, clearTimer],
  );

  useEffect(() => {
    return () => {
      clearTimer();
      abortInFlight();
    };
  }, [abortInFlight, clearTimer]);

  return { onPointerEnter, onPointerLeave };
}

/** Test-only reset for module-level prefetch state. */
export function resetIntentPrefetchStateForTests(): void {
  inFlightCount = 0;
  recentKeys.length = 0;
}
