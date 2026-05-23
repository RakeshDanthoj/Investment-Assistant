"use client";

import { forwardRef, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { categoryLabel, categoryPillClass } from "@/lib/cards/categories";
import type { MirrorPrediction } from "@/lib/mirror/types";
import { cn } from "@/lib/utils";

import { AccuracyMeterGroup } from "./AccuracyMeter";
import { GapInsightExpanded } from "./GapInsightExpanded";

type PredictionCardProps = {
  prediction: MirrorPrediction;
  defaultExpanded?: boolean;
  expanded?: boolean;
  onExpandedChange?: (open: boolean) => void;
};

function formatLoggedAt(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

function statusBadgeVariant(status: MirrorPrediction["mirror_status"]) {
  switch (status) {
    case "resolved":
      return "border-finnwise-green/30 bg-[#F0FDF4] text-finnwise-green";
    case "active":
      return "border-finnwise-amber/30 bg-[#FFFBEB] text-finnwise-amber";
    default:
      return "border-slate-200 bg-slate-50 text-slate-600";
  }
}

function statusLabel(status: MirrorPrediction["mirror_status"]) {
  switch (status) {
    case "resolved":
      return "Resolved";
    case "active":
      return "Active";
    default:
      return "Pending";
  }
}

export const PredictionCard = forwardRef<HTMLElement, PredictionCardProps>(function PredictionCard(
  { prediction, defaultExpanded = false, expanded: expandedProp, onExpandedChange },
  ref,
) {
  const [expandedInternal, setExpandedInternal] = useState(defaultExpanded);
  const isControlled = expandedProp !== undefined;
  const expanded = isControlled ? expandedProp : expandedInternal;

  useEffect(() => {
    if (isControlled) return;
    setExpandedInternal(defaultExpanded);
  }, [defaultExpanded, isControlled]);

  function setExpanded(next: boolean) {
    if (!isControlled) setExpandedInternal(next);
    onExpandedChange?.(next);
  }

  return (
    <article
      ref={ref}
      id={`prediction-${prediction.id}`}
      className="rounded-lg border border-slate-200 bg-white shadow-sm scroll-mt-28"
      data-testid={`prediction-card-${prediction.id}`}
      data-prediction-id={prediction.id}
    >
      <button
        type="button"
        className="w-full px-4 py-4 text-left"
        aria-expanded={expanded}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={cn(
              "rounded px-1.5 py-0.5 font-mono text-[10px] font-medium uppercase",
              categoryPillClass(prediction.event_category),
            )}
          >
            {categoryLabel(prediction.event_category)}
          </span>
          <span className="text-[12px] text-slate-600">{prediction.event_title}</span>
          <span className="font-mono text-[10px] text-slate-400">
            {formatLoggedAt(prediction.logged_at)}
          </span>
          <Badge
            variant="outline"
            className={cn("ml-auto font-mono text-[10px]", statusBadgeVariant(prediction.mirror_status))}
          >
            {statusLabel(prediction.mirror_status)}
          </Badge>
        </div>

        <h3 className="mt-2 font-display text-[14px] font-semibold leading-snug text-slate-900">
          {prediction.card_title}
        </h3>

        <p className="mt-2 text-[13px] text-slate-700">
          Your call: <span className="font-semibold text-slate-900">{prediction.prediction_text}</span>
        </p>

        <div className="mt-4">
          <AccuracyMeterGroup
            mechanism={prediction.mechanism_accuracy}
            business={prediction.business_accuracy}
            market={prediction.market_accuracy}
          />
        </div>
      </button>

      {expanded ? (
        <div className="px-4 pb-4">
          <GapInsightExpanded prediction={prediction} />
        </div>
      ) : null}
    </article>
  );
});
