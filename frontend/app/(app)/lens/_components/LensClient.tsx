"use client";

import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { getApiBaseUrl, describeFetchFailure } from "@/lib/api";
import { deferAfterPaint } from "@/lib/deferAfterPaint";
import type { Horizon } from "@/lib/onboarding/state";
import type {
  LensQueryItem,
  LensQueriesResponse,
  LensQueryCreateResponse,
} from "@/lib/lens/types";
import {
  initialLensState,
  lensHashForState,
  lensReducer,
} from "@/lib/lens/useLensState";
import { createClient } from "@/lib/supabase/client";

import { ExampleGrid } from "./ExampleGrid";
import { LoadingCard } from "./LoadingCard";
import { QueryHistory } from "./QueryHistory";
import { QueryInput } from "./QueryInput";
import { ResultCard } from "./ResultCard";

type LensClientProps = {
  signedIn?: boolean;
  initialHistory?: LensQueryItem[] | null;
};

export default function LensClient({
  signedIn = true,
  initialHistory = null,
}: LensClientProps) {
  const hydratedFromServer = signedIn && initialHistory !== null;

  const [state, dispatch] = useReducer(lensReducer, undefined, initialLensState);
  const [history, setHistory] = useState<LensQueriesResponse["items"]>(
    () => initialHistory ?? [],
  );
  const [historyLoading, setHistoryLoading] = useState(
    () => signedIn && !hydratedFromServer,
  );
  const [historyError, setHistoryError] = useState<string | null>(null);
  const skipInitialHistoryRef = useRef(hydratedFromServer);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError(null);

    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      setHistoryLoading(false);
      setHistoryError("Sign in to use The Lens.");
      return;
    }

    try {
      const base = getApiBaseUrl();
      const res = await fetch(`${base}/api/lens/queries/me`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
        cache: "no-store",
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `Request failed (${res.status})`);
      }
      const json = (await res.json()) as LensQueriesResponse;
      setHistory(json.items);
    } catch (error) {
      setHistoryError(describeFetchFailure(error, "load query history"));
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!signedIn) {
      setHistoryLoading(false);
      setHistoryError("Sign in to use The Lens.");
      return;
    }
    if (skipInitialHistoryRef.current) {
      skipInitialHistoryRef.current = false;
      return;
    }
    let cancelled = false;
    void deferAfterPaint(async () => {
      if (!cancelled) {
        await loadHistory();
      }
    });
    return () => {
      cancelled = true;
    };
  }, [loadHistory, signedIn]);

  useEffect(() => {
    if (historyLoading) return;
    dispatch({ type: "HYDRATE_FROM_HASH", hash: window.location.hash, history });
  }, [historyLoading, history]);

  useEffect(() => {
    const nextHash = lensHashForState(state);
    const current = window.location.hash;
    if (nextHash !== current) {
      const path = window.location.pathname + window.location.search + nextHash;
      window.history.replaceState(null, "", path);
    }
  }, [state]);

  const submitQuery = useCallback(async () => {
    dispatch({ type: "SUBMIT_START" });

    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      dispatch({ type: "SUBMIT_ERROR", message: "Sign in to generate a card." });
      return;
    }

    try {
      const base = getApiBaseUrl();
      const res = await fetch(`${base}/api/lens/queries`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: state.queryText.trim(),
          sector: state.sector,
          horizon: state.horizon,
        }),
        cache: "no-store",
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `Request failed (${res.status})`);
      }

      const json = (await res.json()) as LensQueryCreateResponse;
      dispatch({ type: "SUBMIT_SUCCESS", queryId: json.id });
      void loadHistory();
    } catch (error) {
      dispatch({
        type: "SUBMIT_ERROR",
        message: describeFetchFailure(error, "start card generation"),
      });
    }
  }, [loadHistory, state.horizon, state.queryText, state.sector]);

  function onSectorChange(sector: string | null) {
    dispatch({ type: "SET_SECTOR", sector });
  }

  function onHorizonChange(horizon: Horizon | null) {
    dispatch({ type: "SET_HORIZON", horizon });
  }

  const showInput = state.view === "idle" || state.view === "submitting" || state.view === "error";

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
      <div
        className={
          state.view === "result"
            ? "w-full flex-1"
            : "mx-auto w-full max-w-[680px] flex-1 px-4 py-6"
        }
      >
        {showInput ? (
          <>
            <QueryInput
              queryText={state.queryText}
              sector={state.sector}
              horizon={state.horizon}
              submitting={state.view === "submitting"}
              onQueryChange={(text) => dispatch({ type: "SET_QUERY_TEXT", text })}
              onSectorChange={onSectorChange}
              onHorizonChange={onHorizonChange}
              onSubmit={() => void submitQuery()}
            />
            {state.view === "error" && state.errorMessage ? (
              <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
                {state.errorMessage}
              </div>
            ) : null}
            <div className="mt-8">
              <ExampleGrid
                onSelect={(text, sector) =>
                  dispatch({ type: "FILL_EXAMPLE", text, sector })
                }
              />
            </div>
            {historyError ? (
              <div className="mt-6 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-center text-sm text-destructive">
                {historyError}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  onClick={() => void loadHistory()}
                >
                  Try again
                </Button>
              </div>
            ) : (
              <QueryHistory
                items={history}
                loading={historyLoading}
                onSelect={(item) => dispatch({ type: "OPEN_HISTORY", item })}
              />
            )}
          </>
        ) : null}

        {state.view === "loading" && state.activeQueryId ? (
          <LoadingCard
            queryId={state.activeQueryId}
            queryText={state.queryText}
            onComplete={(cardId, generationSeconds) =>
              dispatch({ type: "STREAM_COMPLETE", cardId, generationSeconds })
            }
            onError={(message) => dispatch({ type: "STREAM_ERROR", message })}
          />
        ) : null}

        {state.view === "result" && state.activeQuery?.card_id ? (
          <ResultCard
            cardId={state.activeQuery.card_id}
            queryText={state.queryText}
            sector={state.sector}
            horizon={state.horizon}
            generationSeconds={state.generationSeconds}
            generatedAt={state.activeQuery.created_at}
            onNewQuery={() => dispatch({ type: "RESET_TO_IDLE" })}
          />
        ) : null}
        {state.view === "result" && !state.activeQuery?.card_id ? (
          <div className="rounded-lg border border-border bg-card p-6 text-sm text-muted-foreground">
            Card is not ready yet. Return to your query history when generation completes.
          </div>
        ) : null}
      </div>
    </div>
  );
}
