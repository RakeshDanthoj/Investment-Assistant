"use client";

import { MarketFactChips } from "@/components/market-facts/MarketFactChips";
import { useMarketFacts } from "@/lib/marketFacts/useMarketFacts";
import { cn } from "@/lib/utils";

type MarketFactsStripProps = {
  className?: string;
  compact?: boolean;
};

export function MarketFactsStrip({ className, compact = false }: MarketFactsStripProps) {
  const { status, data, errorMessage } = useMarketFacts();
  const loading = status === "loading" || status === "idle";

  return (
    <div
      className={cn(
        "border-b border-border bg-finnwise-surface/60 px-4 py-2",
        className,
      )}
    >
      <MarketFactChips
        data={data}
        loading={loading}
        errorMessage={errorMessage}
        compact={compact}
      />
    </div>
  );
}
