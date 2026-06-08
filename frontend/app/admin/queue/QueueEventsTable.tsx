import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export type QueueEventRow = {
  id: string;
  title: string;
  category: string;
  event_source: string;
  confidence_score: number;
  lifecycle_state: string;
  canonical_url: string;
  source_url?: string | null;
  created_at: string;
  draft_card_id?: string | null;
};

export function QueueEventsTable({
  loading,
  rows,
  generatingEventId,
  onGenerateDraft,
}: {
  loading: boolean;
  rows: QueueEventRow[];
  generatingEventId: string | null;
  onGenerateDraft: (eventId: string) => void;
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
            <TableHead className="px-4 py-3 font-medium">Review</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((ev) => {
            const isGenerating = generatingEventId === ev.id;
            const hasDraft = Boolean(ev.draft_card_id);

            return (
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
                <TableCell className="px-4 py-3">
                  {hasDraft ? (
                    <Link
                      href={`/admin/review/${ev.draft_card_id}`}
                      className="text-xs font-medium text-finnwise-blue underline decoration-dotted hover:opacity-80"
                    >
                      Open review
                    </Link>
                  ) : (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="h-8 text-xs"
                      disabled={isGenerating || generatingEventId !== null}
                      onClick={() => onGenerateDraft(ev.id)}
                    >
                      {isGenerating ? "Generating…" : "Generate draft"}
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
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
