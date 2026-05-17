"use client";

import { getApiBaseUrl } from "@/lib/api";
import { Suspense, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

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

      <section className="flex flex-wrap gap-2">
        <FilterGroup ariaLabel="Categories">
          {CATEGORY_OPTIONS.map((opt) => (
            <FilterPill
              key={opt.value}
              selected={category === opt.value}
              onClick={() => setCategory(opt.value)}
            >
              {opt.label}
            </FilterPill>
          ))}
        </FilterGroup>
      </section>

      <section className="flex flex-wrap gap-2">
        <FilterGroup ariaLabel="Sources">
          {SOURCE_FILTERS.map((opt) => (
            <FilterPill
              key={opt.value}
              selected={source === opt.value}
              onClick={() => setSource(opt.value)}
            >
              {opt.label}
            </FilterPill>
          ))}
        </FilterGroup>
      </section>

      {error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <p>{error}</p>
          <p className="mt-2 text-xs text-amber-800">
            Hint: confirm <code>NEXT_PUBLIC_API_BASE_URL</code> in <code>.env.local</code> reaches
            the FastAPI backend and CORS permits this origin.
          </p>
        </div>
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

function FilterGroup({
  children,
  ariaLabel,
}: {
  children: ReactNode;
  ariaLabel: string;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2" aria-label={ariaLabel} role="group">
      {children}
    </div>
  );
}

function FilterPill({
  children,
  selected,
  onClick,
}: {
  children: ReactNode;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "rounded-full border px-4 py-1.5 text-sm transition",
        selected
          ? "border-finnwise-blue bg-finnwise-blue text-white shadow-sm"
          : "border-slate-200 bg-white text-slate-700 hover:border-finnwise-blue hover:text-finnwise-blue",
      ].join(" ")}
    >
      {children}
    </button>
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
      <table className="min-w-full border-collapse text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-600">
          <tr>
            <th className="px-4 py-3 font-medium">Confidence</th>
            <th className="px-4 py-3 font-medium">Title</th>
            <th className="px-4 py-3 font-medium">Category</th>
            <th className="px-4 py-3 font-medium">Source</th>
            <th className="px-4 py-3 font-medium">Link</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((ev) => (
            <tr key={ev.id} className="border-t border-slate-100 hover:bg-slate-50/80">
              <td className="px-4 py-3 font-mono text-finnwise-green">
                {ev.confidence_score}
              </td>
              <td className="max-w-xl px-4 py-3 text-slate-900">{ev.title}</td>
              <td className="px-4 py-3 text-xs uppercase tracking-wide text-slate-600">
                {ev.category.replaceAll("_", " ")}
              </td>
              <td className="px-4 py-3 text-xs text-slate-500">{ev.event_source}</td>
              <td className="px-4 py-3">
                <QueueLink canonical={ev.canonical_url} fallback={ev.source_url} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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
