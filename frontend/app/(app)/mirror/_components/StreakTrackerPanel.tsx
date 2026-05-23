import type { MirrorStreakResponse } from "@/lib/mirror/types";

import { StreakSummary } from "./StreakSummary";
import { StreakTracker } from "./StreakTracker";

type StreakTrackerPanelProps = {
  streak: MirrorStreakResponse | null;
  loading?: boolean;
};

export function StreakTrackerPanel({ streak, loading = false }: StreakTrackerPanelProps) {
  return (
    <section
      className="rounded-lg border border-border bg-background p-4 shadow-sm"
      data-testid="streak-tracker-panel"
      aria-labelledby="streak-tracker-heading"
    >
      <h2
        id="streak-tracker-heading"
        className="font-mono text-[10px] font-semibold uppercase tracking-wide text-slate-500"
      >
        Streak tracker
      </h2>
      <p className="mt-1 text-[11px] leading-snug text-slate-500">
        Last 14 predictions — mechanism grade per cell
      </p>
      <div className="mt-4">
        <StreakTracker cells={streak?.cells ?? null} loading={loading} />
      </div>
      <StreakSummary streak={streak} loading={loading} />
    </section>
  );
}
