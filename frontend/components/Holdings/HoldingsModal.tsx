"use client";

import { useCallback, useEffect, useId, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { searchInstruments, type InstrumentSearchResult } from "@/lib/api/instruments";
import {
  clearSessionHoldings,
  saveSessionHoldings,
  type SessionHolding,
} from "@/lib/personalisation/sessionHoldings";

type HoldingsModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialHoldings: SessionHolding[];
  onSaved?: () => void;
};

export default function HoldingsModal({
  open,
  onOpenChange,
  initialHoldings,
  onSaved,
}: HoldingsModalProps) {
  const titleId = useId();
  const [draft, setDraft] = useState<SessionHolding[]>(initialHoldings);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<InstrumentSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [saving, setSaving] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setDraft(initialHoldings);
      setQuery("");
      setSuggestions([]);
      setSearchError(null);
    }
  }, [open, initialHoldings]);

  useEffect(() => {
    if (!open) return;
    const q = query.trim();
    if (q.length < 2) {
      setSuggestions([]);
      setSearchError(null);
      return;
    }
    const handle = window.setTimeout(() => {
      setSearching(true);
      setSearchError(null);
      void searchInstruments(q)
        .then((rows) => {
          const selected = new Set(draft.map((h) => h.instrumentId.toUpperCase()));
          setSuggestions(rows.filter((r) => !selected.has(r.instrument_id.toUpperCase())));
        })
        .catch((e: unknown) => {
          setSuggestions([]);
          setSearchError(e instanceof Error ? e.message : "Could not search instruments.");
        })
        .finally(() => setSearching(false));
    }, 280);
    return () => window.clearTimeout(handle);
  }, [query, open, draft]);

  const addHolding = useCallback((row: InstrumentSearchResult) => {
    setDraft((prev) => {
      if (prev.some((h) => h.instrumentId.toUpperCase() === row.instrument_id.toUpperCase())) {
        return prev;
      }
      return [
        ...prev,
        {
          instrumentId: row.instrument_id,
          displayName: row.display_name,
          exchange: row.exchange,
        },
      ];
    });
    setQuery("");
    setSuggestions([]);
  }, []);

  const removeHolding = useCallback((instrumentId: string) => {
    setDraft((prev) => prev.filter((h) => h.instrumentId !== instrumentId));
  }, []);

  async function handleSave() {
    setSaving(true);
    try {
      await saveSessionHoldings(draft);
      onSaved?.();
      onOpenChange(false);
    } finally {
      setSaving(false);
    }
  }

  async function handleClear() {
    setSaving(true);
    try {
      await clearSessionHoldings();
      setDraft([]);
      onSaved?.();
      onOpenChange(false);
    } finally {
      setSaving(false);
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center"
      role="presentation"
      onClick={() => onOpenChange(false)}
      onKeyDown={(e) => {
        if (e.key === "Escape") onOpenChange(false);
      }}
    >
      <dialog
        open
        aria-labelledby={titleId}
        className="m-0 max-h-[min(90vh,640px)] w-full max-w-lg overflow-hidden rounded-xl border border-border bg-background p-0 shadow-lg"
        onClick={(e) => e.stopPropagation()}
        onCancel={(e) => {
          e.preventDefault();
          onOpenChange(false);
        }}
      >
        <div className="border-b border-border px-5 py-4">
          <h2 id={titleId} className="font-display text-lg font-semibold text-foreground">
            Session holdings
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Add tickers you hold so The Pulse and The Thread can highlight what matters to you.
          </p>
          <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
            This data is not stored on our servers — it stays in this browser tab only and is
            cleared when you close the tab.
          </p>
        </div>

        <div className="space-y-4 overflow-y-auto px-5 py-4">
          <div>
            <Label htmlFor="holdings-search" className="text-xs font-medium uppercase tracking-wide">
              Search instruments
            </Label>
            <Input
              id="holdings-search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. HDFCBANK or HDFC Bank"
              className="mt-1.5"
              autoComplete="off"
            />
            {searching ? (
              <p className="mt-1 font-mono text-[10px] text-muted-foreground">Searching…</p>
            ) : null}
            {searchError ? (
              <p className="mt-1 text-xs text-destructive">{searchError}</p>
            ) : null}
            {suggestions.length ? (
              <ul className="mt-2 max-h-40 overflow-y-auto rounded-md border border-border bg-muted/30">
                {suggestions.map((row) => (
                  <li key={row.instrument_id}>
                    <button
                      type="button"
                      className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm hover:bg-muted"
                      onClick={() => addHolding(row)}
                    >
                      <span>
                        <span className="font-medium text-foreground">{row.display_name}</span>
                        <span className="ml-2 font-mono text-[10px] text-muted-foreground">
                          {row.instrument_id}
                        </span>
                      </span>
                      <span className="shrink-0 text-xs text-finnwise-blue">Add</span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>

          {draft.length ? (
            <ul className="space-y-2" aria-label="Selected holdings">
              {draft.map((h) => (
                <li
                  key={h.instrumentId}
                  className="flex items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-2"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-foreground">{h.displayName}</p>
                    <p className="font-mono text-[10px] text-muted-foreground">{h.instrumentId}</p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="shrink-0 text-xs text-muted-foreground"
                    onClick={() => removeHolding(h.instrumentId)}
                  >
                    Remove
                  </Button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No holdings added yet.</p>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-end gap-2 border-t border-border px-5 py-4">
          {draft.length ? (
            <Button type="button" variant="ghost" disabled={saving} onClick={() => void handleClear()}>
              Clear all
            </Button>
          ) : null}
          <Button type="button" variant="outline" disabled={saving} onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button type="button" disabled={saving} onClick={() => void handleSave()}>
            {saving ? "Saving…" : "Save for this session"}
          </Button>
        </div>
      </dialog>
    </div>
  );
}
