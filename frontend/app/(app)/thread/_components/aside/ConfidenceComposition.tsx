"use client";

import { useCallback, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Skeleton } from "@/components/ui/skeleton";
import {
  fetchConfidenceBreakdown,
  type ConfidenceBreakdownInputs,
  type ConfidenceBreakdownResponse,
} from "@/lib/api/confidenceBreakdown";

type ConfidenceCompositionProps = {
  measured: number;
  modelled: number;
  judged: number;
  /** Lens result: PRD §5 explanatory note below the legend. */
  footnote?: string;
  /** When set, enables lazy-loaded event confidence breakdown on expand. */
  eventId?: string;
};

const INPUT_ORDER = [
  "source_count",
  "source_quality",
  "factor_db_match",
  "recency",
  "unique_publisher",
] as const satisfies ReadonlyArray<keyof ConfidenceBreakdownInputs>;

const INPUT_LABELS: Record<(typeof INPUT_ORDER)[number], string> = {
  source_count: "Source count",
  source_quality: "Source quality",
  factor_db_match: "Factor DB match",
  recency: "Recency",
  unique_publisher: "Unique publishers",
};

function tierLabel(tier: ConfidenceBreakdownResponse["tier"]): string {
  if (tier === "high") return "High";
  if (tier === "medium") return "Medium";
  return "Low";
}

function tierDotClass(tier: ConfidenceBreakdownResponse["tier"]): string {
  if (tier === "high") return "bg-finnwise-blue";
  if (tier === "medium") return "bg-finnwise-amber";
  return "bg-slate-400";
}

function tierExplanation(tier: ConfidenceBreakdownResponse["tier"]): string {
  if (tier === "high") {
    return "Score ≥ 0.75 — eligible for high-confidence routing when other gates pass.";
  }
  if (tier === "medium") {
    return "Score 0.55–0.74 — partial editorial path; thresholds are provisional.";
  }
  return "Score < 0.55 — low-confidence routing; held for review when gates require it.";
}

function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

function formatRetrievedAt(value: string | null): string {
  if (!value) return "Time unknown";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function BreakdownSkeleton() {
  return (
    <div className="mt-3 space-y-3" data-testid="confidence-breakdown-skeleton" aria-hidden>
      <Skeleton className="h-4 w-40" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-16 w-full rounded-lg" />
    </div>
  );
}

type BreakdownPanelProps = {
  breakdown: ConfidenceBreakdownResponse;
};

function BreakdownPanel({ breakdown }: BreakdownPanelProps) {
  const fogReduced =
    breakdown.fog_active &&
    breakdown.confidence_effective < breakdown.confidence_raw - 0.001;

  return (
    <div className="mt-3 space-y-4" data-testid="confidence-breakdown-panel">
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`inline-block h-2 w-2 rounded-full ${tierDotClass(breakdown.tier)}`}
          aria-hidden
        />
        <span className="font-mono text-[12px] font-semibold text-slate-800">
          {tierLabel(breakdown.tier)} tier
        </span>
        <span className="font-mono text-[10px] text-slate-500">
          raw {formatScore(breakdown.confidence_raw)} · effective{" "}
          {formatScore(breakdown.confidence_effective)}
        </span>
        {breakdown.force_editorial_review ? (
          <Badge
            variant="outline"
            className="border-amber-300 bg-[#FFFBEB] font-mono text-[10px] text-amber-900"
            data-testid="confidence-escalation-badge"
          >
            Editorial review
          </Badge>
        ) : null}
      </div>

      <p className="text-[12px] leading-relaxed text-slate-600">{tierExplanation(breakdown.tier)}</p>

      {fogReduced ? (
        <p
          className="rounded-lg border border-violet-200 bg-violet-50 p-3 text-[12px] leading-relaxed text-violet-950"
          data-testid="confidence-fow-callout"
        >
          Fog of War is active — effective confidence is dampened by{" "}
          {breakdown.fog_dampener ?? 0.6}× while overlapping major events are live.
        </p>
      ) : null}

      <ul className="space-y-3">
        {INPUT_ORDER.map((key) => {
          const input = breakdown.inputs[key];
          const pct = Math.round(input.value * 100);
          const weightPct = Math.round(input.weight * 100);
          return (
            <li key={key}>
              <div className="flex items-baseline justify-between gap-2 font-mono text-[10px] text-slate-600">
                <span className="font-semibold text-slate-700">{INPUT_LABELS[key]}</span>
                <span>
                  {pct}% · weight {weightPct}%
                </span>
              </div>
              <div className="relative mt-1 flex h-2 w-full overflow-hidden rounded-full border border-slate-200 bg-muted">
                <span className="bg-finnwise-blue" style={{ width: `${pct}%` }} />
              </div>
              <p className="mt-1 text-[11px] leading-snug text-slate-500">{input.detail}</p>
            </li>
          );
        })}
      </ul>

      {breakdown.sources.length ? (
        <div>
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
            Sources
          </p>
          <ul className="mt-2 space-y-2">
            {breakdown.sources.map((source, idx) => (
              <li
                key={`${source.url}-${idx}`}
                className="rounded-lg border border-slate-100 bg-slate-50 p-2"
              >
                <p className="font-mono text-[11px] font-semibold text-slate-700">{source.name}</p>
                <p className="mt-0.5 text-[10px] text-slate-500">
                  Retrieved {formatRetrievedAt(source.retrieved_at)}
                </p>
                {source.url ? (
                  <a
                    href={source.url}
                    className="mt-1 block truncate text-[10px] text-finnwise-blue underline-offset-2 hover:underline"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {source.url}
                  </a>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export function ConfidenceComposition({
  measured,
  modelled,
  judged,
  footnote,
  eventId,
}: ConfidenceCompositionProps) {
  const mPct = Math.round(measured * 100);
  const moPct = Math.round(modelled * 100);
  const jPct = Math.max(0, 100 - mPct - moPct);

  const [expanded, setExpanded] = useState(false);
  const [breakdown, setBreakdown] = useState<ConfidenceBreakdownResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadBreakdown = useCallback(async () => {
    if (!eventId || breakdown || loading) return;
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await fetchConfidenceBreakdown(eventId);
      setBreakdown(data);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not load confidence breakdown.";
      setErrorMessage(message);
    } finally {
      setLoading(false);
    }
  }, [breakdown, eventId, loading]);

  const handleExpandChange = (open: boolean) => {
    setExpanded(open);
    if (open) {
      void loadBreakdown();
    }
  };

  return (
    <Card className="w-full min-w-0 rounded-[10px] py-0 shadow-none ring-slate-200" size="sm">
      <CardContent className="p-4">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
          Confidence composition
        </p>
        <div
          data-slot="progress"
          className="relative mt-3 flex h-3 w-full overflow-hidden rounded-full border border-slate-200 bg-muted"
        >
          <span className="bg-finnwise-blue" style={{ width: `${mPct}%` }} title="Measured" />
          <span className="bg-finnwise-green" style={{ width: `${moPct}%` }} title="Modelled" />
          <span className="bg-finnwise-amber" style={{ width: `${jPct}%` }} title="Judged" />
        </div>
        <ul className="mt-3 space-y-1 font-mono text-[10px] text-slate-600">
          <li>
            <span className="inline-block h-2 w-2 rounded-full bg-finnwise-blue align-middle" /> Measured{" "}
            {mPct}%
          </li>
          <li>
            <span className="inline-block h-2 w-2 rounded-full bg-finnwise-green align-middle" /> Modelled{" "}
            {moPct}%
          </li>
          <li>
            <span className="inline-block h-2 w-2 rounded-full bg-finnwise-amber align-middle" /> Judged{" "}
            {jPct}%
          </li>
        </ul>
        {footnote ? (
          <p className="mt-3 text-[12px] leading-relaxed text-slate-600">{footnote}</p>
        ) : null}

        {eventId ? (
          <Collapsible open={expanded} onOpenChange={handleExpandChange} className="mt-4 border-t border-slate-100 pt-3">
            <CollapsibleTrigger className="flex w-full items-center justify-between text-left font-mono text-[11px] font-semibold text-slate-700">
              Why this confidence tier?
              <span className="text-[10px] font-normal text-slate-400">{expanded ? "Hide" : "Show"}</span>
            </CollapsibleTrigger>
            <CollapsibleContent>
              {loading ? <BreakdownSkeleton /> : null}
              {errorMessage ? (
                <p
                  className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-[12px] text-red-900"
                  data-testid="confidence-breakdown-error"
                  role="alert"
                >
                  {errorMessage}
                </p>
              ) : null}
              {breakdown && !loading ? <BreakdownPanel breakdown={breakdown} /> : null}
            </CollapsibleContent>
          </Collapsible>
        ) : null}
      </CardContent>
    </Card>
  );
}
