"use client";

import { useRouter } from "next/navigation";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { MarketFactsBanner } from "@/components/market-facts/MarketFactsBanner";
import { getApiBaseUrl } from "@/lib/api";
import { requestDraftFromEvent } from "@/lib/editorial/draftFromEvent";
import { useMarketFacts } from "@/lib/marketFacts/useMarketFacts";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";

import { QueueEventsTable, type QueueEventRow } from "./QueueEventsTable";

const SOURCES_ALL = "__all_src__";

const CATEGORY_OPTIONS = [
  { value: "__all_cat__", label: "All categories" },
  { value: "macro", label: "Macro" },
  { value: "rbi_policy", label: "RBI policy" },
  { value: "regulatory", label: "Regulatory" },
  { value: "india_specific", label: "India-specific" },
  { value: "geopolitical", label: "Geopolitical" },
  { value: "budget", label: "Budget" },
] as const;

const SOURCE_FILTERS = [
  { value: SOURCES_ALL, label: "All sources" },
  { value: "newsapi", label: "NewsAPI" },
  { value: "rbi_rss", label: "RBI RSS" },
  { value: "nse_bse", label: "NSE / BSE feed" },
] as const;

function buildFetchUrl(filters: {
  category: string;
  source: string;
}) {
  const base = `${getApiBaseUrl().replace(/\/$/, "")}/admin/events`;
  const params = new URLSearchParams();
  params.set("lifecycle_state", "draft");
  if (filters.category && filters.category !== "__all_cat__") {
    params.set("category", filters.category);
  }
  if (filters.source !== SOURCES_ALL) {
    params.set("event_source", filters.source);
  }
  return `${base}?${params.toString()}`;
}

export default function EditorialQueuePage() {
  return (
    <Suspense fallback={<QueueLoading />}>
      <EditorialQueueInner />
    </Suspense>
  );
}

function QueueLoading() {
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-4 py-10">
      <h1 className="font-display text-3xl text-slate-900">Loading queue…</h1>
    </main>
  );
}

function EditorialQueueInner() {
  const router = useRouter();
  const [rows, setRows] = useState<QueueEventRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generatingEventId, setGeneratingEventId] = useState<string | null>(null);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const {
    status: factsStatus,
    data: factsData,
    errorMessage: factsError,
  } = useMarketFacts();

  const [category, setCategory] = useState<string>("__all_cat__");
  const [source, setSource] = useState<string>(SOURCES_ALL);

  const url = useMemo(() => buildFetchUrl({ category, source }), [category, source]);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `${res.status} ${res.statusText}`);
      }
      const data = (await res.json()) as QueueEventRow[];
      const sorted = [...data].sort((a, b) => b.confidence_score - a.confidence_score);
      setRows(sorted);
    } catch (e: unknown) {
      setRows([]);
      setError(e instanceof Error ? e.message : "Failed to fetch queue.");
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    reload();
  }, [reload]);

  const handleGenerateDraft = useCallback(
    async (eventId: string) => {
      setGeneratingEventId(eventId);
      setGenerateError(null);
      const result = await requestDraftFromEvent(eventId);
      if (!result.ok) {
        setGenerateError(result.message);
        setGeneratingEventId(null);
        return;
      }

      setRows((current) =>
        current.map((row) =>
          row.id === eventId ? { ...row, draft_card_id: result.cardId } : row,
        ),
      );
      setGeneratingEventId(null);
      router.push(`/admin/review/${result.cardId}`);
    },
    [router],
  );

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-4 py-10">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Editorial</p>
        <h1 className="font-display text-3xl text-slate-900">Draft event queue</h1>
        <p className="max-w-2xl text-sm text-slate-600">
          Triage ingested events, then generate an ICE draft card to open the review workspace.
          Generation takes about 30–90 seconds. Rows with an existing draft show{" "}
          <span className="font-medium text-slate-800">Open review</span> instead.
        </p>
      </header>

      <MarketFactsBanner
        data={factsData}
        loading={factsStatus === "loading" || factsStatus === "idle"}
        errorMessage={factsError}
      />

      <section aria-label="Categories">
        <ToggleGroup
          type="single"
          value={category}
          onValueChange={(value) => {
            if (value) setCategory(value);
          }}
          variant="outline"
          className="flex flex-wrap"
        >
          {CATEGORY_OPTIONS.map((opt) => (
            <ToggleGroupItem key={opt.value} value={opt.value} className="rounded-full px-4">
              {opt.label}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </section>

      <section aria-label="Sources">
        <ToggleGroup
          type="single"
          value={source}
          onValueChange={(value) => {
            if (value) setSource(value);
          }}
          variant="outline"
          className="flex flex-wrap"
        >
          {SOURCE_FILTERS.map((opt) => (
            <ToggleGroupItem key={opt.value} value={opt.value} className="rounded-full px-4">
              {opt.label}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </section>

      {error ? (
        <Alert variant="destructive" className="border-amber-200 bg-amber-50 text-amber-900">
          <AlertDescription>
            <p>{error}</p>
            <p className="mt-2 text-xs text-amber-800">
              Hint: confirm <code>NEXT_PUBLIC_API_BASE_URL</code> in <code>.env.local</code> reaches
              the FastAPI backend and CORS permits this origin.
            </p>
          </AlertDescription>
        </Alert>
      ) : null}

      {generateError ? (
        <Alert variant="destructive" className="border-amber-200 bg-amber-50 text-amber-900">
          <AlertDescription className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p>{generateError}</p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setGenerateError(null)}
            >
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      <QueueEventsTable
        loading={loading}
        rows={rows}
        generatingEventId={generatingEventId}
        onGenerateDraft={(eventId) => void handleGenerateDraft(eventId)}
      />

      <footer className="border-t border-slate-200 pt-6 text-center text-[11px] leading-relaxed text-slate-700">
        <p>
          Editorial tooling only — not investment advice or a recommendation under SEBI
          regulations.
        </p>
      </footer>
    </main>
  );
}
