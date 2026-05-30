"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { MarketFactsBanner } from "@/components/market-facts/MarketFactsBanner";
import { getApiBaseUrl } from "@/lib/api";
import { useMarketFacts } from "@/lib/marketFacts/useMarketFacts";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";

type QueueEventRow = {
  id: string;
  title: string;
  category: string;
  event_source: string;
  confidence_score: number;
  lifecycle_state: string;
  canonical_url: string;
  source_url?: string | null;
  created_at: string;
};

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
  const [rows, setRows] = useState<QueueEventRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-4 py-10">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Editorial</p>
        <h1 className="font-display text-3xl text-slate-900">Draft event queue</h1>
        <p className="max-w-2xl text-sm text-slate-600">
          Draft events surfaced by FinnWise ingestion. Sorted highest confidence first. Filters
          combine with the FastAPI catalogue view (Phase&nbsp;1: no reviewer auth gate).
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

      <EventsTable loading={loading} rows={rows} />

      <footer className="border-t border-slate-200 pt-6 text-center text-[11px] leading-relaxed text-slate-700">
        <p>
          Editorial tooling only — not investment advice or a recommendation under SEBI
          regulations.
        </p>
      </footer>
    </main>
  );
}

function EventsTable({
  loading,
  rows,
}: {
  loading: boolean;
  rows: QueueEventRow[];
}) {
  if (loading) {
    return <p className="text-sm text-slate-500">Refreshing ingest snapshot…</p>;
  }

  if (!rows.length) {
    return (
      <p className="rounded-lg border border-dashed border-slate-300 bg-white px-4 py-6 text-sm text-slate-600">
        No draft events matched these filters yet. Run&nbsp;
        <code className="font-mono text-xs">python -m app.jobs.event_detection</code> against a
        configured Supabase backend to populate drafts.
      </p>
    );
  }

  return (
    <div className="overflow-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <Table className="min-w-full border-collapse text-left text-sm">
        <TableHeader className="bg-slate-50 text-xs uppercase tracking-wide text-slate-600">
          <TableRow className="hover:bg-transparent">
            <TableHead className="px-4 py-3 font-medium">Confidence</TableHead>
            <TableHead className="px-4 py-3 font-medium">Title</TableHead>
            <TableHead className="px-4 py-3 font-medium">Category</TableHead>
            <TableHead className="px-4 py-3 font-medium">Source</TableHead>
            <TableHead className="px-4 py-3 font-medium">Link</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((ev) => (
            <TableRow key={ev.id} className="border-t border-slate-100 hover:bg-slate-50/80">
              <TableCell className="px-4 py-3 font-mono text-finnwise-green">
                {ev.confidence_score}
              </TableCell>
              <TableCell className="max-w-xl px-4 py-3 whitespace-normal text-slate-900">
                {ev.title}
              </TableCell>
              <TableCell className="px-4 py-3 text-xs uppercase tracking-wide text-slate-600">
                {ev.category.replaceAll("_", " ")}
              </TableCell>
              <TableCell className="px-4 py-3 text-xs text-slate-500">{ev.event_source}</TableCell>
              <TableCell className="px-4 py-3">
                <QueueLink canonical={ev.canonical_url} fallback={ev.source_url} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function QueueLink({
  canonical,
  fallback,
}: {
  canonical: string;
  fallback?: string | null;
}) {
  const hrefCandidate = canonical.startsWith("http") ? canonical : fallback;
  const href =
    typeof hrefCandidate === "string" && hrefCandidate.startsWith("http")
      ? hrefCandidate
      : null;
  const label = canonical.length > 64 ? `${canonical.slice(0, 64)}…` : canonical;
  return href ? (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-xs text-finnwise-blue underline decoration-dotted"
    >
      {label || "Open"}
    </a>
  ) : (
    <span className="font-mono text-[11px] text-slate-500">{canonical}</span>
  );
}
