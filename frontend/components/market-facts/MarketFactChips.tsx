"use client";

import { Skeleton } from "@/components/ui/skeleton";
import type { MarketFactChip, MarketFactsResponse } from "@/lib/marketFacts/types";
import { cn } from "@/lib/utils";

import { FreshnessDot } from "./FreshnessDot";

type MarketFactChipsProps = {
  data: MarketFactsResponse | null;
  loading?: boolean;
  errorMessage?: string | null;
  className?: string;
  compact?: boolean;
};

function Chip({ fact, compact }: { fact: MarketFactChip; compact?: boolean }) {
  const muted = fact.freshness_status === "unavailable";
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-1",
        compact && "px-2 py-0.5",
        muted && "border-dashed bg-slate-50",
      )}
      title={`${fact.label} · ${fact.source}`}
    >
      <FreshnessDot status={fact.freshness_status} />
      <span className="font-mono text-[9px] uppercase tracking-wide text-slate-500">
        {fact.label}
      </span>
      <span
        className={cn(
          "font-mono text-[10px] text-slate-800",
          compact && "text-[9px]",
          muted && "text-slate-400",
        )}
      >
        {fact.display_value}
      </span>
    </div>
  );
}

export function MarketFactChips({
  data,
  loading = false,
  errorMessage,
  className,
  compact = false,
}: MarketFactChipsProps) {
  if (loading && !data) {
    return (
      <div className={cn("flex flex-wrap gap-2", className)} aria-busy="true">
        {[1, 2, 3].map((key) => (
          <Skeleton key={key} className="h-7 w-24 rounded-full" />
        ))}
      </div>
    );
  }

  if (errorMessage) {
    return (
      <p className={cn("font-mono text-[10px] text-amber-800", className)}>
        Market facts unavailable — {errorMessage}
      </p>
    );
  }

  if (!data?.facts.length) {
    return null;
  }

  return (
    <div className={cn("flex flex-wrap gap-2", className)} aria-label="Market fact chips">
      {data.facts.map((fact) => (
        <Chip key={fact.fact_id} fact={fact} compact={compact} />
      ))}
    </div>
  );
}
