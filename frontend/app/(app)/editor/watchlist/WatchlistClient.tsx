"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getApiBaseUrl } from "@/lib/api";

export type WatchlistRow = {
  id: string;
  event_description: string;
  category: string;
  added_at: string;
  review_frequency: string;
  last_reviewed_at?: string | null;
  escalation_trigger?: string | null;
  status: "watching" | "escalated" | "closed";
  escalated_event_id?: string | null;
};

const STATUS_OPTIONS = [
  { value: "watching", label: "Watching" },
  { value: "escalated", label: "Escalated" },
  { value: "closed", label: "Closed" },
] as const;

function apiBase() {
  return `${getApiBaseUrl().replace(/\/$/, "")}/api/editor/watchlist`;
}

function statusBadgeVariant(status: WatchlistRow["status"]) {
  if (status === "watching") return "secondary" as const;
  if (status === "escalated") return "default" as const;
  return "outline" as const;
}

type Props = {
  accessToken: string;
};

export default function WatchlistClient({ accessToken }: Props) {
  const [rows, setRows] = useState<WatchlistRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    const headers = { Authorization: `Bearer ${accessToken}` };
    try {
      const res = await fetch(apiBase(), { headers, cache: "no-store" });
      if (res.status === 403) {
        throw new Error("403 — editor access denied. Check ADMIN_EMAILS on the API.");
      }
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `${res.status} ${res.statusText}`);
      }
      const data = (await res.json()) as WatchlistRow[];
      setRows(data);
    } catch (e: unknown) {
      setRows([]);
      setError(e instanceof Error ? e.message : "Failed to load watchlist.");
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const patchStatus = async (id: string, status: WatchlistRow["status"]) => {
    setBusyId(id);
    setError(null);
    try {
      const res = await fetch(`${apiBase()}/${id}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `${res.status} ${res.statusText}`);
      }
      const updated = (await res.json()) as WatchlistRow;
      setRows((prev) => prev.map((r) => (r.id === id ? updated : r)));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to update status.");
    } finally {
      setBusyId(null);
    }
  };

  const escalate = async (id: string) => {
    setBusyId(id);
    setError(null);
    try {
      const res = await fetch(`${apiBase()}/${id}/escalate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `${res.status} ${res.statusText}`);
      }
      const payload = (await res.json()) as { item: WatchlistRow; event_id: string };
      setRows((prev) => prev.map((r) => (r.id === id ? payload.item : r)));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Escalate failed.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-4 py-10">
      <header className="space-y-2">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Editorial</p>
        <h1 className="font-display text-3xl text-slate-900">Slow-burn watchlist</h1>
        <p className="max-w-2xl text-sm text-slate-600">
          Long-lead risks (monsoon, budget, regulatory reviews). Review weekly; escalate manually to
          create a draft event — no auto-escalation in Phase 3.
        </p>
      </header>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {loading ? (
        <p className="text-sm text-slate-600">Loading watchlist…</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Description</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Review</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.id}>
                <TableCell className="max-w-md space-y-1">
                  <p className="text-sm text-slate-900">{row.event_description}</p>
                  {row.escalation_trigger ? (
                    <p className="text-xs text-slate-500">Trigger: {row.escalation_trigger}</p>
                  ) : null}
                  {row.escalated_event_id ? (
                    <Link
                      href={`/admin/queue`}
                      className="text-xs text-blue-800 underline"
                    >
                      Draft event queued
                    </Link>
                  ) : null}
                </TableCell>
                <TableCell className="text-sm capitalize text-slate-700">
                  {row.category.replaceAll("_", " ")}
                </TableCell>
                <TableCell className="text-sm text-slate-600">{row.review_frequency}</TableCell>
                <TableCell>
                  <div className="flex flex-col gap-2">
                    <Badge variant={statusBadgeVariant(row.status)}>{row.status}</Badge>
                    <Select
                      value={row.status}
                      onValueChange={(v) =>
                        void patchStatus(row.id, v as WatchlistRow["status"])
                      }
                      disabled={busyId === row.id}
                    >
                      <SelectTrigger className="h-8 w-[130px] text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {STATUS_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    size="sm"
                    disabled={busyId === row.id || row.status === "escalated"}
                    onClick={() => void escalate(row.id)}
                  >
                    Escalate
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <p className="text-xs text-slate-500">
        Sunday digest email includes up to 10 watching items and 10 pending dedup-review rows.
      </p>
    </main>
  );
}
