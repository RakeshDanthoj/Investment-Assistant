"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";

import type { CardDetailResponse } from "@/lib/cards/threadTypes";
import { intersectHoldingsWithInstruments } from "@/lib/personalisation/sessionHoldings";
import { useSessionHoldings } from "@/lib/personalisation/useSessionHoldings";

import { Card, CardContent } from "@/components/ui/card";

import { DissentingView } from "./DissentingView";
import { HoldingCallout } from "./HoldingCallout";
import { EmptyLayerState } from "./EmptyLayerState";
import { FrameworkBehindThis } from "./FrameworkBehindThis";
import { InstrumentCard } from "./InstrumentCard";

const PredictionLogger = dynamic(
  () => import("./PredictionLogger").then((m) => ({ default: m.PredictionLogger })),
  { ssr: false },
);

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
  const hasInsight = insight_layer.trim().length > 0;
  const { holdings } = useSessionHoldings();
  const holdingIntersections = useMemo(
    () => intersectHoldingsWithInstruments(holdings, instruments),
    [holdings, instruments],
  );

  return (
    <div className="w-full min-w-0 space-y-8">
      <HoldingCallout intersections={holdingIntersections} />
      <Card className="w-full min-w-0 rounded-[10px] py-0 shadow-none ring-slate-200">
        <CardContent className="p-6">
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">Insight</p>
          {hasInsight ? (
            <div className="mt-4 text-[15px] leading-[1.75] font-light whitespace-pre-wrap text-slate-700">
              {insight_layer}
            </div>
          ) : (
            <EmptyLayerState
              className="mt-4"
              title="No insight published yet"
              description="This card does not have insight content yet. Check back after editorial review, or open another card from The Pulse."
            />
          )}
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
