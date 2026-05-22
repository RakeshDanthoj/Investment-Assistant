"use client";

import type { CardDetailResponse } from "@/lib/cards/threadTypes";

import { Card, CardContent } from "@/components/ui/card";

import { DissentingView } from "./DissentingView";
import { FrameworkBehindThis } from "./FrameworkBehindThis";
import { InstrumentCard } from "./InstrumentCard";
import { PredictionLogger } from "./PredictionLogger";

type InsightLayerProps = Pick<
  CardDetailResponse,
  "insight_layer" | "instruments" | "dissenting_view" | "framework_behind_this"
> & {
  cardId: string;
  showPredictionLogger?: boolean;
};

export function InsightLayer({
  cardId,
  showPredictionLogger = true,
  insight_layer,
  instruments,
  dissenting_view,
  framework_behind_this,
}: InsightLayerProps) {
  return (
    <div className="w-full min-w-0 space-y-8">
      <Card className="w-full min-w-0 rounded-[10px] py-0 shadow-none ring-slate-200">
        <CardContent className="p-6">
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">Insight</p>
          <div className="mt-4 text-[15px] leading-[1.75] font-light whitespace-pre-wrap text-slate-700">
            {insight_layer.trim() || "—"}
          </div>
        </CardContent>
      </Card>

      {instruments.length ? (
        <section>
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">
            Instrument assessments
          </p>
          <div className="mt-4 grid min-w-0 gap-3 sm:grid-cols-2">
            {instruments.map((row) => (
              <InstrumentCard key={`${row.instrument_id}-${row.signal_label}`} row={row} />
            ))}
          </div>
        </section>
      ) : null}

      <DissentingView text={dissenting_view} />

      {showPredictionLogger ? <PredictionLogger cardId={cardId} /> : null}

      <FrameworkBehindThis text={framework_behind_this} />
    </div>
  );
}
