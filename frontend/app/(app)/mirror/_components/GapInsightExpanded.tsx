import Link from "next/link";

import type { MirrorPrediction } from "@/lib/mirror/types";

type GapInsightExpandedProps = {
  prediction: MirrorPrediction;
};

export function GapInsightExpanded({ prediction }: GapInsightExpandedProps) {
  const insight = prediction.gap_insight?.trim();
  const moduleName = prediction.linked_map_module_name;
  const moduleId = prediction.linked_map_module_id;

  return (
    <div
      className="mt-4 border-t border-slate-200 pt-4"
      data-testid="gap-insight-expanded"
    >
      <p className="font-mono text-[10px] font-semibold uppercase tracking-wide text-slate-500">
        Gap insight
      </p>
      {insight ? (
        <p className="mt-2 text-[13px] leading-relaxed text-slate-700">{insight}</p>
      ) : (
        <p className="mt-2 text-[13px] leading-relaxed text-slate-500">
          Grading runs when this card resolves. Your gap insight will appear here after the
          three-level score is computed.
        </p>
      )}
      {moduleId && moduleName ? (
        <Link
          href={`/map?module=${encodeURIComponent(moduleId)}`}
          className="mt-3 inline-flex text-[13px] font-medium text-finnwise-blue hover:underline"
        >
          🗺 The Map: {moduleName} →
        </Link>
      ) : null}
    </div>
  );
}
