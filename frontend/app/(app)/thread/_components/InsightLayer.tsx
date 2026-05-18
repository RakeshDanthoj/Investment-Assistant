"use client";

import type { CardDetailResponse } from "@/lib/cards/threadTypes";

import { DissentingView } from "./DissentingView";
import { FrameworkBehindThis } from "./FrameworkBehindThis";
import { InstrumentCard } from "./InstrumentCard";
import { PredictionLogger } from "./PredictionLogger";

type InsightLayerProps = Pick<
  CardDetailResponse,
  "insight_layer" | "instruments" | "dissenting_view" | "framework_behind_this"
> & {
  cardId: string;
};

export function InsightLayer({
  cardId,
  insight_layer,
  instruments,
  dissenting_view,
  framework_behind_this,
}: InsightLayerProps) {
  return (
    <div className="space-y-8">
      <section className="rounded-[10px] border border-slate-200 bg-white p-6">
        <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">Insight</p>
        <div className="mt-4 whitespace-pre-wrap text-[15px] font-light leading-[1.75] text-slate-700">
          {insight_layer.trim() || "—"}
        </div>
      </section>

      {instruments.length ? (
        <section>
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">
            Instrument assessments
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {instruments.map((row) => (
              <InstrumentCard key={`${row.instrument_id}-${row.signal_label}`} row={row} />
            ))}
          </div>
        </section>
      ) : null}

      <DissentingView text={dissenting_view} />

      <PredictionLogger cardId={cardId} />

      <FrameworkBehindThis text={framework_behind_this} />
    </div>
  );
}
