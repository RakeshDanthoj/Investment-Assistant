"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { categoryLabel, categoryPillClass } from "@/lib/cards/categories";
import type { CardDetailResponse } from "@/lib/cards/threadTypes";
import { useCard } from "@/lib/cards/useCard";

import { CurrentOriginalToggle } from "./CurrentOriginalToggle";
import type { IceTabId } from "./IceTabs";
import { IceTabs } from "./IceTabs";
import { InsightLayer } from "./InsightLayer";

const ContextLayer = dynamic(
  () => import("./ContextLayer").then((m) => ({ default: m.ContextLayer })),
  { loading: () => <IceLayerSkeleton /> },
);

const EvidenceLayer = dynamic(
  () => import("./EvidenceLayer").then((m) => ({ default: m.EvidenceLayer })),
  { loading: () => <IceLayerSkeleton /> },
);

const LifecycleTracker = dynamic(
  () => import("./aside/LifecycleTracker").then((m) => ({ default: m.LifecycleTracker })),
  { loading: () => <AsideBlockSkeleton />, ssr: false },
);

const SignalsToWatch = dynamic(
  () => import("./aside/SignalsToWatch").then((m) => ({ default: m.SignalsToWatch })),
  { loading: () => <AsideBlockSkeleton />, ssr: false },
);

const ConfidenceComposition = dynamic(
  () =>
    import("./aside/ConfidenceComposition").then((m) => ({ default: m.ConfidenceComposition })),
  { loading: () => <AsideBlockSkeleton />, ssr: false },
);

const BiasFlags = dynamic(
  () => import("./aside/BiasFlags").then((m) => ({ default: m.BiasFlags })),
  { loading: () => <AsideBlockSkeleton />, ssr: false },
);

function IceLayerSkeleton() {
  return (
    <div className="space-y-3" aria-hidden>
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-24 w-full rounded-lg" />
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

type ThreadExperienceProps = {
  cardId: string;
  initialData?: CardDetailResponse | null;
  initialError?: string | null;
};

export default function ThreadExperience({
  cardId,
  initialData,
  initialError,
}: ThreadExperienceProps) {
  const [view, setView] = useState<"current" | "original">("current");
  const initialState = useMemo(
    () => ({ data: initialData, error: initialError }),
    [initialData, initialError],
  );
  const { status, data, errorMessage, refetch, contextRevealed, revealContext } = useCard(
    cardId,
    view,
    initialState,
  );

  const [iceTab, setIceTab] = useState<IceTabId>("insight");
  const [maxTier, setMaxTier] = useState(0);

  useEffect(() => {
    setIceTab("insight");
    setMaxTier(0);
  }, [view]);

  const pulseLifecycle = useMemo(() => {
    const s = data?.lifecycle_state ?? "";
    return s === "active" || s === "signal_triggered";
  }, [data?.lifecycle_state]);

  const shouldLoadContext = maxTier >= 1 || iceTab === "context";
  const shouldLoadEvidence = maxTier >= 2 || iceTab === "evidence";

  if ((status === "loading" || status === "idle") && !initialData && !initialError) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="mt-6 h-96 rounded-lg" />
      </div>
    );
  }

  if (status === "error" || !data) {
    return (
      <main className="mx-auto max-w-3xl p-6 md:p-8">
        <Alert variant="destructive">
          <AlertDescription>{errorMessage ?? "Could not load card."}</AlertDescription>
        </Alert>
        <Button
          type="button"
          variant="link"
          className="mt-4 h-auto p-0 text-sm font-medium text-finnwise-blue"
          onClick={() => {
            void refetch();
          }}
        >
          Retry
        </Button>
        <Link href="/pulse" className="mt-6 block text-sm text-slate-600 hover:underline">
          ← Back to The Pulse
        </Link>
      </main>
    );
  }

  const lifeBadge =
    data.week_number != null
      ? `${data.lifecycle_state.replace(/_/g, " ")} · Week ${data.week_number} of 4`
      : data.lifecycle_state.replace(/_/g, " ");

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-x-hidden bg-[#F8FAFC]">
      <header className="sticky top-0 z-10 shrink-0 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur md:px-8">
        <div className="flex min-w-0 flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/pulse"
              className="font-mono text-[11px] font-medium text-finnwise-blue hover:underline"
            >
              ← The Pulse
            </Link>
            <span className="text-slate-300" aria-hidden>
              /
            </span>
            <span className="font-mono text-[11px] text-slate-500">The Thread</span>
            <Badge
              variant="outline"
              className="gap-2 rounded-full border-slate-200 bg-slate-50 px-3 py-1 font-mono text-[10px] font-semibold uppercase tracking-wide text-slate-700"
            >
              {pulseLifecycle ? (
                <span className="thread-lifecycle-pulse h-2 w-2 rounded-full bg-finnwise-blue" />
              ) : (
                <span className="h-2 w-2 rounded-full bg-slate-300" />
              )}
              {lifeBadge}
            </Badge>
            <Badge className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold ${categoryPillClass(data.category)}`}>
              {categoryLabel(data.category)}
            </Badge>
          </div>
          <CurrentOriginalToggle view={view} onChange={setView} />
        </div>
      </header>

      <div className="grid w-full min-w-0 flex-1 grid-cols-1 gap-0 lg:grid-cols-[minmax(0,1fr)_340px]">
        <article className="min-w-0 border-slate-200 px-4 py-8 md:px-10 lg:border-r">
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">
            Event Intelligence Card
          </p>
          <h1 className="font-display mt-2 text-[26px] leading-snug font-semibold text-slate-900 md:text-[28px]">
            {data.title}
          </h1>
          <p className="mt-3 text-[15px] leading-relaxed font-light italic text-slate-600">
            {data.event_title}
          </p>

          <Card className="mt-8 w-full min-w-0 overflow-hidden rounded-lg py-0 shadow-none ring-slate-200">
            <CardContent className="flex min-w-0 flex-col gap-0 p-0 sm:flex-row">
              <div className="min-w-0 flex-1 border-slate-200 bg-white px-4 py-3 sm:border-r">
                <p className="font-mono text-[10px] uppercase tracking-wide text-slate-400">
                  Direction confidence
                </p>
                <p className="mt-1 flex items-center gap-2 text-[13px] font-medium text-slate-800">
                  <span className={`h-2 w-2 rounded-full ${dotClass(data.direction_confidence.tier)}`} />
                  {data.direction_confidence.label}
                </p>
              </div>
              <div className="min-w-0 flex-1 bg-white px-4 py-3">
                <p className="font-mono text-[10px] uppercase tracking-wide text-slate-400">
                  Magnitude confidence
                </p>
                <p className="mt-1 flex items-center gap-2 text-[13px] font-medium text-slate-800">
                  <span className={`h-2 w-2 rounded-full ${dotClass(data.magnitude_confidence.tier)}`} />
                  {data.magnitude_confidence.label}
                  {data.event_confidence_score != null ? (
                    <span className="font-normal text-slate-400">
                      ({data.event_confidence_score}/100)
                    </span>
                  ) : null}
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
                if (tier >= 1) {
                  revealContext();
                }
              }}
              panels={{
                insight: (
                  <InsightLayer
                    cardId={data.card_id}
                    showPredictionLogger={!contextRevealed}
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

        <aside className="hidden min-w-0 bg-[#F8FAFC] px-6 py-6 lg:block">
          <div className="sticky top-6 min-w-0 space-y-4">
            <LifecycleTracker steps={data.lifecycle_tracker} pulseActive={pulseLifecycle} />
            <SignalsToWatch signals={data.signals} instruments={data.instruments} />
            <ConfidenceComposition
              measured={data.confidence_composition.measured}
              modelled={data.confidence_composition.modelled}
              judged={data.confidence_composition.judged}
            />
            <BiasFlags audit={data.bias_audit} />
          </div>
        </aside>
      </div>
    </div>
  );
}
