"use client";

import { ChevronRight } from "lucide-react";

import { formatFinnwiseDate } from "@/lib/format/dateTime";
import type { MirrorUnreadNotification } from "@/lib/mirror/types";
import { cn } from "@/lib/utils";

type ReadyToGradePanelProps = {
  items: MirrorUnreadNotification[];
  onSelect: (item: MirrorUnreadNotification) => void;
  className?: string;
};

export function ReadyToGradePanel({ items, onSelect, className }: ReadyToGradePanelProps) {
  return (
    <section
      className={cn("rounded-lg border border-[#BBF7D0] bg-[#F0FDF4] p-4", className)}
      aria-labelledby="ready-to-grade-heading"
      data-testid="ready-to-grade-panel"
    >
      <h2
        id="ready-to-grade-heading"
        className="font-mono text-[10px] font-semibold uppercase tracking-wide text-finnwise-green"
      >
        Ready to grade
      </h2>

      {items.length === 0 ? (
        <p className="mt-3 text-[12px] text-slate-600">No newly graded cards right now.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {items.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className="flex w-full items-center gap-2 rounded-md border border-[#BBF7D0] bg-white px-3 py-2 text-left transition-colors hover:bg-[#ECFDF5]"
                onClick={() => onSelect(item)}
                data-testid={`ready-to-grade-item-${item.prediction_id}`}
              >
                <span
                  className="inline-block h-2 w-2 shrink-0 rounded-full bg-finnwise-green"
                  aria-hidden
                />
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium text-[13px] text-slate-900">
                    {item.event_title || item.card_title}
                  </span>
                  {item.resolved_at ? (
                    <span className="font-mono text-[10px] text-slate-500">
                      Resolved {item.resolved_at ? formatFinnwiseDate(item.resolved_at) : ""}
                    </span>
                  ) : null}
                </span>
                <ChevronRight className="h-4 w-4 shrink-0 text-slate-400" aria-hidden />
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
