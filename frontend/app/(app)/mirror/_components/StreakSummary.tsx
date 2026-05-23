import type { MirrorStreakResponse } from "@/lib/mirror/types";

type StreakSummaryProps = {
  streak: MirrorStreakResponse | null;
  loading?: boolean;
};

export function StreakSummary({ streak, loading = false }: StreakSummaryProps) {
  if (loading || !streak) {
    return (
      <p
        className="mt-4 animate-pulse text-[13px] leading-relaxed text-slate-500"
        data-testid="streak-summary"
        aria-busy="true"
      >
        &nbsp;
      </p>
    );
  }

  return (
    <p
      className="mt-4 text-[13px] leading-relaxed text-slate-700"
      data-testid="streak-summary"
    >
      {streak.summary}
    </p>
  );
}
