import { cn } from "@/lib/utils";
import type { StreakCell, StreakGrade } from "@/lib/mirror/types";

const STREAK_SLOT_COUNT = 14;

type StreakTrackerProps = {
  cells: StreakCell[] | null;
  loading?: boolean;
};

function cellStyles(grade: StreakGrade): { box: string; text: string } {
  switch (grade) {
    case "correct":
      return {
        box: "bg-finnwise-modelled-bg border-emerald-200",
        text: "text-finnwise-green",
      };
    case "partial":
      return {
        box: "bg-finnwise-judged-bg border-amber-200",
        text: "text-finnwise-amber",
      };
    case "incorrect":
      return {
        box: "bg-[#FEE2E2] border-red-200",
        text: "text-finnwise-red",
      };
    case "monitoring":
      return {
        box: "bg-slate-100 border-slate-200",
        text: "text-slate-500",
      };
    default:
      return {
        box: "border-transparent bg-transparent",
        text: "text-slate-300",
      };
  }
}

const LEGEND_ITEMS: { label: string; grade: StreakGrade; letter: StreakCell["letter"] }[] = [
  { label: "Correct", grade: "correct", letter: "M" },
  { label: "Partial", grade: "partial", letter: "P" },
  { label: "Incorrect", grade: "incorrect", letter: "✗" },
  { label: "Monitoring", grade: "monitoring", letter: "·" },
  { label: "No prediction", grade: "empty", letter: "–" },
];

function LegendSwatch({ grade, letter }: { grade: StreakGrade; letter: StreakCell["letter"] }) {
  const styles = cellStyles(grade);
  return (
    <span
      className={cn(
        "inline-flex h-5 w-5 items-center justify-center rounded border font-mono text-[10px] font-medium",
        styles.box,
        styles.text,
      )}
      aria-hidden
    >
      {letter}
    </span>
  );
}

export function StreakTracker({ cells, loading = false }: StreakTrackerProps) {
  const slots =
    cells && cells.length === STREAK_SLOT_COUNT
      ? cells
      : Array.from({ length: STREAK_SLOT_COUNT }, () => ({
          letter: "–" as const,
          grade: "empty" as const,
        }));

  return (
    <div data-testid="streak-tracker">
      <div
        className="grid grid-cols-7 gap-1.5 min-[400px]:grid-cols-14"
        aria-label="Last 14 predictions, most recent on the left"
      >
        {slots.map((cell, index) => {
          const styles = cellStyles(cell.grade);
          return (
            <div
              key={`streak-cell-${index}`}
              data-testid={`streak-cell-${index}`}
              data-grade={cell.grade}
              className={cn(
                "flex aspect-square items-center justify-center rounded border font-mono text-[11px] font-semibold",
                styles.box,
                styles.text,
                loading && "animate-pulse",
              )}
              title={
                index === 0
                  ? "Most recent prediction"
                  : cell.grade === "empty"
                    ? "No prediction in this slot"
                    : undefined
              }
            >
              {cell.letter}
            </div>
          );
        })}
      </div>

      <div
        className="mt-3 flex flex-wrap gap-x-4 gap-y-2"
        data-testid="streak-legend"
        aria-label="Streak legend"
      >
        {LEGEND_ITEMS.map((item) => (
          <span key={item.label} className="inline-flex items-center gap-1.5">
            <LegendSwatch grade={item.grade} letter={item.letter} />
            <span className="font-mono text-[10px] text-slate-500">{item.label}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
