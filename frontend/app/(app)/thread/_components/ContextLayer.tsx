"use client";

import type { ContextStep } from "@/lib/cards/threadTypes";

function mmjClass(mmj: string | null): string {
  const k = (mmj || "MEASURED").toUpperCase();
  if (k === "MODELLED") return "bg-finnwise-modelled-bg text-finnwise-green border border-emerald-200";
  if (k === "JUDGED") return "bg-finnwise-judged-bg text-finnwise-amber border border-amber-200";
  return "bg-finnwise-blue-tint text-finnwise-blue border border-blue-200";
}

function mmjLabel(mmj: string | null): string {
  const k = (mmj || "MEASURED").toUpperCase();
  if (k === "MODELLED") return "modelled";
  if (k === "JUDGED") return "judged";
  return "measured";
}

type ContextLayerProps = {
  steps: ContextStep[];
  fallbackText: string;
};

export function ContextLayer({ steps, fallbackText }: ContextLayerProps) {
  const items =
    steps.length > 0
      ? steps
      : [{ title: fallbackText.trim() || "—", body: "", mmj: null as string | null }];

  return (
    <div className="rounded-[10px] border border-slate-200 bg-white p-6">
      <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">
        Causal chain
      </p>
      <div className="mt-6 flex flex-col">
        {items.map((step, idx) => (
          <div key={`${idx}-${step.title.slice(0, 24)}`} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-slate-900 bg-[#EEF2FF] font-mono text-xs font-bold text-slate-900">
                {idx + 1}
              </div>
              {idx < items.length - 1 ? (
                <div className="my-1 w-px flex-1 min-h-[24px] bg-slate-200" aria-hidden />
              ) : null}
            </div>
            <div className={`flex-1 pb-8 ${idx === items.length - 1 ? "pb-2" : ""}`}>
              <p className="text-[14px] font-semibold leading-snug text-slate-900">{step.title}</p>
              {step.body ? (
                <p className="mt-2 text-[13px] leading-relaxed text-slate-600">{step.body}</p>
              ) : null}
              <span
                className={`mt-3 inline-flex items-center rounded px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide ${mmjClass(step.mmj)}`}
              >
                {mmjLabel(step.mmj)} · MMJ
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
