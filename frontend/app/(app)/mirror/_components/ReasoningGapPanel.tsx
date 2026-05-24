"use client";

import Link from "next/link";
import { Compass, Layers, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { MirrorReasoningGap, MirrorReasoningGapsResponse } from "@/lib/mirror/types";
import { cn } from "@/lib/utils";

const GAP_ICONS: Record<string, { Icon: typeof Compass; boxClass: string }> = {
  direction_magnitude_mismatch: {
    Icon: Compass,
    boxClass: "bg-sky-100 text-sky-700",
  },
  narrative_anchoring: {
    Icon: Layers,
    boxClass: "bg-amber-100 text-amber-800",
  },
  sector_concentration: {
    Icon: Layers,
    boxClass: "bg-violet-100 text-violet-800",
  },
};

type ReasoningGapPanelProps = {
  gaps: MirrorReasoningGapsResponse | null;
  loading?: boolean;
  refreshing?: boolean;
  onRefresh?: () => void;
  className?: string;
};

function GapItem({ gap }: { gap: MirrorReasoningGap }) {
  const meta = GAP_ICONS[gap.gap_type] ?? GAP_ICONS.direction_magnitude_mismatch;
  const { Icon, boxClass } = meta;
  const href = `/map?module=${encodeURIComponent(gap.linked_map_module_id)}`;

  return (
    <li className="flex gap-3" data-testid={`reasoning-gap-${gap.gap_type}`}>
      <span
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-md",
          boxClass,
        )}
        aria-hidden
      >
        <Icon className="h-4 w-4" strokeWidth={2} />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-bold leading-snug text-slate-900">{gap.gap_name}</p>
        <p className="mt-1 text-[12px] leading-relaxed text-slate-600">{gap.pattern_explanation}</p>
        <Link
          href={href}
          className="mt-2 inline-flex text-[13px] font-medium text-finnwise-blue hover:underline"
        >
          🗺 The Map: {gap.linked_map_module_name} →
        </Link>
      </div>
    </li>
  );
}

export function ReasoningGapPanel({
  gaps,
  loading = false,
  refreshing = false,
  onRefresh,
  className,
}: ReasoningGapPanelProps) {
  const items = gaps?.items ?? [];
  const insufficient = gaps?.insufficient_history ?? false;

  return (
    <section
      className={cn(
        "rounded-lg border border-border bg-background p-4 shadow-sm",
        className,
      )}
      data-testid="reasoning-gap-panel"
      aria-labelledby="reasoning-gap-heading"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2
            id="reasoning-gap-heading"
            className="font-mono text-[10px] font-semibold uppercase tracking-wide text-slate-500"
          >
            Reasoning gap analysis
          </h2>
          <p className="mt-1 text-[11px] leading-snug text-slate-500">
            Patterns from your resolved predictions
          </p>
        </div>
        {onRefresh ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 shrink-0 px-2 text-[11px]"
            onClick={onRefresh}
            disabled={loading || refreshing}
            data-testid="reasoning-gap-refresh"
          >
            <RefreshCw className={cn("mr-1 h-3.5 w-3.5", refreshing && "animate-spin")} />
            Refresh
          </Button>
        ) : null}
      </div>

      {loading ? (
        <div className="mt-4 space-y-3" aria-hidden>
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : null}

      {!loading && insufficient ? (
        <p className="mt-4 text-[12px] leading-relaxed text-slate-600" data-testid="reasoning-gap-empty">
          Resolve at least three predictions with grades to surface reasoning gaps. Your gap
          insights on each card will still appear as cards resolve.
        </p>
      ) : null}

      {!loading && !insufficient && items.length === 0 ? (
        <p className="mt-4 text-[12px] leading-relaxed text-slate-600">
          No strong cross-prediction patterns yet — keep logging calls and check back after more
          cards resolve.
        </p>
      ) : null}

      {!loading && items.length > 0 ? (
        <ul className="mt-4 space-y-4">
          {items.slice(0, 3).map((gap) => (
            <GapItem key={gap.gap_type} gap={gap} />
          ))}
        </ul>
      ) : null}
    </section>
  );
}
