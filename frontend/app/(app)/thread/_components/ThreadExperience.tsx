"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { categoryLabel, categoryPillClass } from "@/lib/cards/categories";
import { useCard } from "@/lib/cards/useCard";

import { BiasFlags } from "./aside/BiasFlags";
import { ConfidenceComposition } from "./aside/ConfidenceComposition";
import { LifecycleTracker } from "./aside/LifecycleTracker";
import { SignalsToWatch } from "./aside/SignalsToWatch";
import { ContextLayer } from "./ContextLayer";
import { CurrentOriginalToggle } from "./CurrentOriginalToggle";
import { EvidenceLayer } from "./EvidenceLayer";
import type { IceTabId } from "./IceTabs";
import { IceTabs } from "./IceTabs";
import { InsightLayer } from "./InsightLayer";

function dotClass(tier: string): string {
  if (tier === "high") return "bg-finnwise-blue";
  if (tier === "moderate") return "bg-finnwise-amber";
  return "bg-slate-300";
}

type ThreadExperienceProps = {
  cardId: string;
};

export default function ThreadExperience({ cardId }: ThreadExperienceProps) {
  const [view, setView] = useState<"current" | "original">("current");
  const { status, data, errorMessage, refetch } = useCard(cardId, view);

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

  if (status === "loading" || status === "idle") {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="h-10 w-64 animate-pulse rounded bg-slate-200" />
        <div className="mt-6 h-96 animate-pulse rounded-lg bg-slate-100" />
      </div>
    );
  }

  if (status === "error" || !data) {
    return (
      <main className="mx-auto max-w-3xl p-6 md:p-8">
        <p className="text-sm text-finnwise-red">{errorMessage ?? "Could not load card."}</p>
        <button
          type="button"
          className="mt-4 text-sm font-medium text-finnwise-blue hover:underline"
          onClick={() => {
            void refetch();
          }}
        >
          Retry
        </button>
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
    <div className="flex min-h-0 flex-1 flex-col bg-[#F8FAFC]">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur md:px-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 md:flex-row md:items-center md:justify-between">
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
            <span
              className={`inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 font-mono text-[10px] font-semibold uppercase tracking-wide text-slate-700`}
            >
              {pulseLifecycle ? (
                <span className="thread-lifecycle-pulse h-2 w-2 rounded-full bg-finnwise-blue" />
              ) : (
                <span className="h-2 w-2 rounded-full bg-slate-300" />
              )}
              {lifeBadge}
            </span>
            <span className={`rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold ${categoryPillClass(data.category)}`}>
              {categoryLabel(data.category)}
            </span>
          </div>
          <CurrentOriginalToggle view={view} onChange={setView} />
        </div>
      </header>

      <div className="mx-auto grid w-full max-w-6xl flex-1 grid-cols-1 gap-0 lg:grid-cols-[1fr_340px]">
        <article className="border-slate-200 px-4 py-8 md:px-10 lg:border-r">
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">
            Event Intelligence Card
          </p>
          <h1 className="font-display mt-2 text-[26px] font-semibold leading-snug text-slate-900 md:text-[28px]">
            {data.title}
          </h1>
          <p className="mt-3 text-[15px] font-light italic leading-relaxed text-slate-600">
            {data.event_title}
          </p>

          <div className="mt-8 flex gap-0 overflow-hidden rounded-lg border border-slate-200">
            <div className="flex-1 border-r border-slate-200 bg-white px-4 py-3">
              <p className="font-mono text-[10px] uppercase tracking-wide text-slate-400">
                Direction confidence
              </p>
              <p className="mt-1 flex items-center gap-2 text-[13px] font-medium text-slate-800">
                <span className={`h-2 w-2 rounded-full ${dotClass(data.direction_confidence.tier)}`} />
                {data.direction_confidence.label}
              </p>
            </div>
            <div className="flex-1 bg-white px-4 py-3">
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
          </div>

          <div className="mt-10">
            <IceTabs
              active={iceTab}
              onTabChange={setIceTab}
              maxUnlockedTier={maxTier}
              onUnlockTier={(tier) => {
                setMaxTier((m) => Math.max(m, tier));
              }}
              panels={{
                insight: (
                  <InsightLayer
                    cardId={data.card_id}
                    insight_layer={data.insight_layer}
                    instruments={data.instruments}
                    dissenting_view={data.dissenting_view}
                    framework_behind_this={data.framework_behind_this}
                  />
                ),
                context: (
                  <ContextLayer steps={data.context_steps} fallbackText={data.context_layer} />
                ),
                evidence: (
                  <EvidenceLayer
                    rows={data.evidence_rows}
                    markdown={data.evidence_markdown}
                    macroStub={data.evidence_macro_stub}
                  />
                ),
              }}
            />
          </div>
        </article>

        <aside className="hidden bg-[#F8FAFC] px-4 py-8 lg:block">
          <div className="sticky top-24 space-y-4">
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
