"use client";

import { Button } from "@/components/ui/button";

type ResultPlaceholderProps = {
  queryText: string;
  onNewQuery: () => void;
};

/** Result shell until P2-S8 renders the full ICE card. */
export function ResultPlaceholder({ queryText, onNewQuery }: ResultPlaceholderProps) {
  return (
    <div className="mx-auto w-full max-w-[680px] space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <Button type="button" variant="outline" size="sm" onClick={onNewQuery}>
          ← New query
        </Button>
        <span className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
          The Lens — Generated card
        </span>
      </div>
      <div className="rounded-xl border border-border bg-card p-6">
        <blockquote className="border-l-4 border-[#1A4FCC] pl-4 font-display text-lg italic text-foreground">
          {queryText}
        </blockquote>
        <p className="mt-4 text-sm text-muted-foreground">
          Full ICE card rendering arrives in P2-S8. Your query is saved and ready for the
          generation pipeline.
        </p>
      </div>
    </div>
  );
}
