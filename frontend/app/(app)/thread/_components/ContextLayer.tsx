"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { ContextStep } from "@/lib/cards/threadTypes";

function mmjVariant(mmj: string | null): "measured" | "modelled" | "judged" {
  const k = (mmj || "MEASURED").toUpperCase();
  if (k === "MODELLED") return "modelled";
  if (k === "JUDGED") return "judged";
  return "measured";
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
    <Card className="w-full min-w-0 rounded-[10px] py-0 shadow-none ring-slate-200">
      <CardContent className="p-6">
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
                  <div className="my-1 min-h-[24px] w-px flex-1 bg-slate-200" aria-hidden />
                ) : null}
              </div>
              <div className={`flex-1 pb-8 ${idx === items.length - 1 ? "pb-2" : ""}`}>
                <p className="text-[14px] leading-snug font-semibold text-slate-900">{step.title}</p>
                {step.body ? (
                  <p className="mt-2 text-[13px] leading-relaxed text-slate-600">{step.body}</p>
                ) : null}
                <Badge variant={mmjVariant(step.mmj)} className="mt-3">
                  {mmjLabel(step.mmj)} · MMJ
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
