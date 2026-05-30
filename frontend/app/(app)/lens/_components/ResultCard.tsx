"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { categoryLabel, categoryPillClass } from "@/lib/cards/categories";
import { useCard } from "@/lib/cards/useCard";
import type { Horizon } from "@/lib/onboarding/state";
import { horizonLabel } from "@/lib/lens/horizons";
import { formatGeneratedMeta } from "@/lib/lens/formatGeneratedMeta";
import { LENS_CONFIDENCE_NOTE } from "./LensLimitations";

import type { IceTabId } from "@/app/(app)/thread/_components/IceTabs";
import { IceTabs } from "@/app/(app)/thread/_components/IceTabs";
import { InsightLayer } from "@/app/(app)/thread/_components/InsightLayer";
import { LensLimitations } from "./LensLimitations";
import { SaveToThreadButton } from "./SaveToThreadButton";

const ContextLayer = dynamic(
  () =>
    import("@/app/(app)/thread/_components/ContextLayer").then((m) => ({
      default: m.ContextLayer,
    })),
  { loading: () => <IceLayerSkeleton /> },
);

const EvidenceLayer = dynamic(
  () =>
    import("@/app/(app)/thread/_components/EvidenceLayer").then((m) => ({
      default: m.EvidenceLayer,
    })),
  { loading: () => <IceLayerSkeleton /> },
);

const ConfidenceComposition = dynamic(
  () =>
    import("@/app/(app)/thread/_components/aside/ConfidenceComposition").then((m) => ({
      default: m.ConfidenceComposition,
    })),
  { loading: () => <AsideBlockSkeleton />, ssr: false },
);

const BiasFlags = dynamic(
  () =>
    import("@/app/(app)/thread/_components/aside/BiasFlags").then((m) => ({
      default: m.BiasFlags,
    })),
  { loading: () => <AsideBlockSkeleton />, ssr: false },
);

function IceLayerSkeleton() {
  return (
    <div className="space-y-3" aria-hidden>
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-24 w-full rounded-lg" />
    </div>
  );
}

function AsideBlockSkeleton() {
  return <Skeleton className="h-28 w-full rounded-lg" aria-hidden />;
}

function dotClass(tier: string): string {
  if (tier === "high") return "bg-finnwise-blue";
  if (tier === "moderate") return "bg-finnwise-amber";
  return "bg-slate-300";
}

type ResultCardProps = {
  cardId: string;
  queryText: string;
  sector: string | null;
  horizon: Horizon | null;
  generationSeconds: number | null;
  generatedAt: string;
  onNewQuery: () => void;
  onSaved?: () => void;
};

export function ResultCard({
  cardId,
  queryText,
  sector,
  horizon,
  generationSeconds,
  generatedAt,
  onNewQuery,
  onSaved,
}: ResultCardProps) {
  const { status, data, errorMessage, refetch, contextRevealed, revealContext } = useCard(
    cardId,
    "current",
  );
  const [iceTab, setIceTab] = useState<IceTabId>("insight");
  const [maxTier, setMaxTier] = useState(0);

  const category = sector ?? data?.category ?? "macro";
  const metaLabel = formatGeneratedMeta(generationSeconds, generatedAt);

  const shouldLoadContext = maxTier >= 1 || iceTab === "context";
  const shouldLoadEvidence = maxTier >= 2 || iceTab === "evidence";

  useEffect(() => {
    setIceTab("insight");
    setMaxTier(0);
  }, [cardId]);

  if (status === "loading" || status === "idle") {
    return (
      <div className="mx-auto w-full max-w-6xl px-4 py-10">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="mt-6 h-96 rounded-lg" />
      </div>
    );
  }

  if (status === "error" || !data) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-8">
        <Button type="button" variant="outline" size="sm" onClick={onNewQuery}>
          ← New query
        </Button>
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{errorMessage ?? "Could not load card."}</AlertDescription>
        </Alert>
        <Button
          type="button"
          variant="link"
          className="mt-4 h-auto p-0 text-sm font-medium text-finnwise-blue"
          onClick={() => void refetch()}
        >
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-6xl">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 md:px-6">
        <div className="flex flex-wrap items-center gap-3">
          <Button type="button" variant="outline" size="sm" onClick={onNewQuery}>
            ← New query
          </Button>
          <span className="font-mono text-[10px] uppercase tracking-wide text-slate-500">
            The Lens — Generated card
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <SaveToThreadButton cardId={cardId} onSaved={onSaved} />
          <Button type="button" size="sm" asChild className="bg-[#0F172A] hover:bg-[#0F172A]/90">
            <Link href={`/thread/${cardId}`}>Read full ICE card →</Link>
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 px-4 py-3 md:px-6">
        <Badge
          className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold ${categoryPillClass(category)}`}
        >
          {categoryLabel(category)}
        </Badge>
        {horizon ? (
          <Badge
            variant="outline"
            className="rounded-full border-slate-200 font-mono text-[10px] font-semibold text-slate-600"
          >
            {horizonLabel(horizon)}
          </Badge>
        ) : null}
        <span className="font-mono text-[10px] text-slate-500">{metaLabel}</span>
      </div>

      <div className="grid w-full min-w-0 grid-cols-1 gap-0 lg:grid-cols-[minmax(0,1fr)_280px]">
        <article className="min-w-0 border-slate-200 px-4 py-6 md:px-8 lg:border-r">
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">
            Event Intelligence Card
          </p>
          <h1 className="font-display mt-2 text-[24px] leading-snug font-semibold text-slate-900">
            {data.title}
          </h1>
          <p className="mt-3 text-[15px] font-light leading-relaxed italic text-slate-600">
            {data.event_title}
          </p>
          <blockquote className="mt-4 border-l-4 border-[#1A4FCC] pl-4 font-display text-base italic text-slate-700">
            {queryText}
          </blockquote>

          <Card className="mt-8 w-full min-w-0 overflow-hidden rounded-lg py-0 shadow-none ring-slate-200">
            <CardContent className="flex min-w-0 flex-col gap-0 p-0 sm:flex-row">
              <div className="min-w-0 flex-1 border-slate-200 bg-white px-4 py-3 sm:border-r">
                <p className="font-mono text-[10px] uppercase tracking-wide text-slate-400">
                  Direction confidence
                </p>
                <p className="mt-1 flex items-center gap-2 text-[13px] font-medium text-slate-800">
                  <span
                    className={`h-2 w-2 rounded-full ${dotClass(data.direction_confidence.tier)}`}
                  />
                  {data.direction_confidence.label}
                </p>
              </div>
              <div className="min-w-0 flex-1 bg-white px-4 py-3">
                <p className="font-mono text-[10px] uppercase tracking-wide text-slate-400">
                  Magnitude confidence
                </p>
                <p className="mt-1 flex items-center gap-2 text-[13px] font-medium text-slate-800">
                  <span
                    className={`h-2 w-2 rounded-full ${dotClass(data.magnitude_confidence.tier)}`}
                  />
                  {data.magnitude_confidence.label}
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="mt-10">
            <IceTabs
              active={iceTab}
              onTabChange={setIceTab}
              maxUnlockedTier={maxTier}
              onUnlockTier={(tier) => {
                setMaxTier((m) => Math.max(m, tier));
                if (tier >= 1) revealContext();
              }}
              panels={{
                insight: (
                  <InsightLayer
                    cardId={data.card_id}
                    showPredictionLogger={false}
                    insight_layer={data.insight_layer}
                    instruments={data.instruments}
                    dissenting_view={data.dissenting_view}
                    framework_behind_this={data.framework_behind_this}
                  />
                ),
                context: shouldLoadContext ? (
                  <ContextLayer steps={data.context_steps} fallbackText={data.context_layer} />
                ) : null,
                evidence: shouldLoadEvidence ? (
                  <EvidenceLayer
                    rows={data.evidence_rows}
                    markdown={data.evidence_markdown}
                    macroStub={data.evidence_macro_stub}
                  />
                ) : null,
              }}
            />
          </div>
        </article>

        <aside className="min-w-0 bg-[#F8FAFC] px-4 py-6 md:px-5 lg:px-6">
          <div className="sticky top-4 min-w-0 space-y-4">
            <ConfidenceComposition
              measured={data.confidence_composition.measured}
              modelled={data.confidence_composition.modelled}
              judged={data.confidence_composition.judged}
              footnote={LENS_CONFIDENCE_NOTE}
              eventId={data.event_id}
            />
            <BiasFlags audit={data.bias_audit} />
            <LensLimitations />
          </div>
        </aside>
      </div>
    </div>
  );
}
