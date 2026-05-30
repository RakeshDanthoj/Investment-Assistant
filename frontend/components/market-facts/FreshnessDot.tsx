import { cn } from "@/lib/utils";

import type { FreshnessStatus } from "@/lib/marketFacts/types";

const FRESHNESS_DOT: Record<FreshnessStatus, string> = {
  fresh: "bg-emerald-500",
  stale: "bg-amber-500",
  unavailable: "bg-red-500",
};

const FRESHNESS_LABEL: Record<FreshnessStatus, string> = {
  fresh: "Fresh",
  stale: "Stale",
  unavailable: "Unavailable",
};

type FreshnessDotProps = {
  status: FreshnessStatus;
  className?: string;
};

export function FreshnessDot({ status, className }: FreshnessDotProps) {
  return (
    <span
      className={cn("inline-block h-2 w-2 shrink-0 rounded-full", FRESHNESS_DOT[status], className)}
      title={`Data freshness: ${FRESHNESS_LABEL[status]}`}
      aria-label={`Data freshness: ${FRESHNESS_LABEL[status]}`}
    />
  );
}
