import { cn } from "@/lib/utils";
import type { AccuracyGrade, AccuracyLevel } from "@/lib/mirror/types";

const LEVEL_LABELS: Record<AccuracyLevel, string> = {
  mechanism: "Mechanism",
  business: "Business impact",
  market: "Market reaction",
};

type AccuracyMeterProps = {
  level: AccuracyLevel;
  grade: AccuracyGrade;
};

function gradeMeta(grade: AccuracyGrade) {
  switch (grade) {
    case "correct":
      return {
        fill: "w-full bg-finnwise-green",
        label: "✓ Correct",
        labelClass: "text-finnwise-green",
      };
    case "partial":
      return {
        fill: "w-2/3 bg-finnwise-amber",
        label: "~ Partial",
        labelClass: "text-finnwise-amber",
      };
    case "incorrect":
      return {
        fill: "w-1/3 bg-finnwise-red",
        label: "✗ Incorrect",
        labelClass: "text-finnwise-red",
      };
    default:
      return {
        fill: "w-1/2 bg-slate-300",
        label: "Monitoring",
        labelClass: "italic text-slate-500",
      };
  }
}

export function AccuracyMeter({ level, grade }: AccuracyMeterProps) {
  const meta = gradeMeta(grade);

  return (
    <div className="space-y-1" data-testid={`accuracy-meter-${level}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[10px] uppercase tracking-wide text-slate-500">
          {LEVEL_LABELS[level]}
        </span>
        <span className={cn("font-mono text-[10px]", meta.labelClass)}>{meta.label}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div className={cn("h-full rounded-full transition-all", meta.fill)} />
      </div>
    </div>
  );
}

export function AccuracyMeterGroup({
  mechanism,
  business,
  market,
}: {
  mechanism: AccuracyGrade;
  business: AccuracyGrade;
  market: AccuracyGrade;
}) {
  return (
    <div className="space-y-2.5" data-testid="accuracy-meter-group">
      <AccuracyMeter level="mechanism" grade={mechanism} />
      <AccuracyMeter level="business" grade={business} />
      <AccuracyMeter level="market" grade={market} />
    </div>
  );
}
