"use client";

import { ChevronRight, FileText } from "lucide-react";

import type { LensQueryItem } from "@/lib/lens/types";
import { formatRelativeDate } from "@/lib/lens/relativeDate";

type QueryHistoryProps = {
  items: LensQueryItem[];
  loading?: boolean;
  onSelect: (item: LensQueryItem) => void;
};

export function QueryHistory({ items, loading = false, onSelect }: QueryHistoryProps) {
  if (loading) {
    return (
      <div className="mt-8 space-y-2" aria-busy>
        <div className="h-4 w-32 animate-pulse rounded bg-muted" />
        <div className="h-12 animate-pulse rounded-lg bg-muted" />
        <div className="h-12 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="mt-8">
      <h2 className="font-mono text-[10px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
        Recent queries
      </h2>
      <ul className="mt-3 divide-y divide-border rounded-lg border border-border bg-card">
        {items.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              onClick={() => onSelect(item)}
              className="flex w-full items-center gap-3 px-3 py-3 text-left transition-colors hover:bg-muted/40"
            >
              <FileText className="size-4 shrink-0 text-muted-foreground" aria-hidden />
              <span className="min-w-0 flex-1 truncate text-[13px] text-foreground">
                {item.query}
              </span>
              <span className="shrink-0 font-mono text-[10px] text-muted-foreground">
                {formatRelativeDate(item.created_at)}
              </span>
              <ChevronRight className="size-4 shrink-0 text-muted-foreground" aria-hidden />
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
