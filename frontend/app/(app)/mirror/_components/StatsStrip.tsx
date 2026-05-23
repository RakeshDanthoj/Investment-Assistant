import { cn } from "@/lib/utils";
import type { MirrorStatsResponse } from "@/lib/mirror/types";

type StatsStripProps = {
  stats: MirrorStatsResponse | null;
  loading?: boolean;
};

type StatCellProps = {
  value: string;
  label: string;
  subtext: string;
  valueClassName?: string;
};

function StatCell({ value, label, subtext, valueClassName }: StatCellProps) {
  return (
    <div className="flex flex-1 flex-col gap-1 px-4 py-4">
      <span className={cn("font-display text-[28px] font-semibold leading-none", valueClassName)}>
        {value}
      </span>
      <span className="font-mono text-[10px] uppercase tracking-wide text-slate-600">{label}</span>
      <span className="text-[11px] leading-snug text-slate-500">{subtext}</span>
    </div>
  );
}

function formatPct(pct: number | null): string {
  if (pct === null) return "—";
  return `${pct.toFixed(pct % 1 === 0 ? 0 : 1)}%`;
}

function toneClass(tone: "strong" | "developing" | "neutral"): string | undefined {
  if (tone === "strong") return "text-finnwise-green";
  if (tone === "developing") return "text-finnwise-amber";
  return undefined;
}

export function StatsStrip({ stats, loading = false }: StatsStripProps) {
  if (loading || !stats) {
    return (
      <div
        className="grid grid-cols-2 border-b border-border bg-background min-[720px]:grid-cols-4"
        aria-busy="true"
      >
        {[1, 2, 3, 4].map((key) => (
          <div key={key} className="h-[88px] animate-pulse border-r border-border bg-muted/30" />
        ))}
      </div>
    );
  }

  return (
    <div
      className="grid grid-cols-2 divide-x divide-border border-b border-border bg-background min-[720px]:grid-cols-4"
      data-testid="mirror-stats-strip"
    >
      <StatCell
        value={String(stats.total_predictions)}
        label="Total predictions"
        subtext="Logged before Context on Thread"
      />
      <StatCell
        value={formatPct(stats.mechanism_accuracy_pct)}
        label="Mechanism accuracy"
        subtext="Causal chain vs outcome"
        valueClassName={toneClass(stats.mechanism_tone)}
      />
      <StatCell
        value={formatPct(stats.market_accuracy_pct)}
        label="Market reaction match"
        subtext="Price path vs your call"
        valueClassName={toneClass(stats.market_tone)}
      />
      <StatCell
        value={String(stats.reasoning_gaps_found)}
        label="Reasoning gaps found"
        subtext="Graded predictions with a gap"
      />
    </div>
  );
}
