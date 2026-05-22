"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getApiBaseUrl } from "@/lib/api";

export type EditorialSignalRow = {
  id: string;
  card_id: string;
  signal_id: string;
  status: string;
  gate: string;
  reason: string;
  payload: Record<string, unknown>;
  created_at: string;
};

function buildSignalQueueUrl() {
  const base = `${getApiBaseUrl().replace(/\/$/, "")}/api/admin/signal-queue`;
  const params = new URLSearchParams();
  params.set("status", "pending");
  return `${base}?${params.toString()}`;
}

function formatReason(reason: string) {
  return reason.replaceAll("_", " ").replaceAll(":", " · ");
}

function formatQueuedAt(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function cardLabel(row: EditorialSignalRow) {
  const payloadTitle = row.payload?.card_title;
  if (typeof payloadTitle === "string" && payloadTitle.trim()) {
    return payloadTitle.trim();
  }
  return row.card_id;
}

export default function SignalQueueClient() {
  const [rows, setRows] = useState<EditorialSignalRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(buildSignalQueueUrl(), { cache: "no-store" });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `${res.status} ${res.statusText}`);
      }
      const data = (await res.json()) as EditorialSignalRow[];
      setRows(data);
    } catch (e: unknown) {
      setRows([]);
      setError(e instanceof Error ? e.message : "Failed to fetch signal queue.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-4 py-10">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Editorial</p>
        <h1 className="font-display text-3xl text-slate-900">Signal review queue</h1>
        <p className="max-w-2xl text-sm text-slate-600">
          Medium-confidence signal hits queued for editorial review before any card changes.
          Open a row to inspect the draft in the review workspace.
        </p>
      </header>

      {error ? (
        <Alert variant="destructive" className="border-amber-200 bg-amber-50 text-amber-900">
          <AlertDescription className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p>{error}</p>
              <p className="mt-2 text-xs text-amber-800">
                Hint: confirm <code>NEXT_PUBLIC_API_BASE_URL</code> in <code>.env.local</code>{" "}
                reaches the FastAPI backend and CORS permits this origin.
              </p>
            </div>
            <Button type="button" variant="outline" size="sm" onClick={() => void reload()}>
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      <SignalQueueTable loading={loading} rows={rows} />

      <footer className="border-t border-slate-200 pt-6 text-center text-[11px] leading-relaxed text-slate-700">
        <p>
          Editorial tooling only — not investment advice or a recommendation under SEBI
          regulations.
        </p>
      </footer>
    </main>
  );
}

export function SignalQueueTable({
  loading,
  rows,
}: {
  loading: boolean;
  rows: EditorialSignalRow[];
}) {
  if (loading) {
    return <p className="text-sm text-slate-500">Loading pending signal hits…</p>;
  }

  if (!rows.length) {
    return (
      <p className="rounded-lg border border-dashed border-slate-300 bg-white px-4 py-6 text-sm text-slate-600">
        No medium-confidence signal hits are pending review. The signal monitor queues items here
        when the confidence gate routes a hit to the editorial path.
      </p>
    );
  }

  return (
    <div className="overflow-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <Table className="min-w-full border-collapse text-left text-sm">
        <TableHeader className="bg-slate-50 text-xs uppercase tracking-wide text-slate-600">
          <TableRow className="hover:bg-transparent">
            <TableHead className="px-4 py-3 font-medium">Card</TableHead>
            <TableHead className="px-4 py-3 font-medium">Signal reason</TableHead>
            <TableHead className="px-4 py-3 font-medium">Gate</TableHead>
            <TableHead className="px-4 py-3 font-medium">Queued</TableHead>
            <TableHead className="px-4 py-3 font-medium">Review</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.id} className="border-t border-slate-100 hover:bg-slate-50/80">
              <TableCell className="max-w-xs px-4 py-3 whitespace-normal text-slate-900">
                <span title={row.card_id}>{cardLabel(row)}</span>
              </TableCell>
              <TableCell className="max-w-md px-4 py-3 whitespace-normal text-slate-700">
                {formatReason(row.reason)}
              </TableCell>
              <TableCell className="px-4 py-3">
                <Badge
                  variant="secondary"
                  className="rounded-full px-2.5 py-0.5 font-mono text-[11px] uppercase tracking-wide"
                >
                  {row.gate}
                </Badge>
              </TableCell>
              <TableCell className="px-4 py-3 text-xs text-slate-500">
                {formatQueuedAt(row.created_at)}
              </TableCell>
              <TableCell className="px-4 py-3">
                <Link
                  href={`/admin/review/${row.card_id}`}
                  className="text-xs font-medium text-finnwise-blue underline decoration-dotted hover:opacity-80"
                >
                  Open review
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
