"use client";

import type { CardDetailResponse } from "@/lib/cards/threadTypes";

type BiasFlagsProps = {
  audit: CardDetailResponse["bias_audit"];
};

export function BiasFlags({ audit }: BiasFlagsProps) {
  return (
    <section className="rounded-[10px] border border-slate-200 bg-white p-4">
      <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
        Bias flags
      </p>
      <div className="mt-3 space-y-3">
        {audit.flags.map((f) => (
          <div key={f.id} className="rounded-lg border border-amber-200 bg-[#FFFBEB] p-3">
            <p className="font-mono text-[11px] font-semibold text-amber-900">{f.label}</p>
            <p className="mt-1 text-[12px] leading-relaxed text-amber-950">{f.detail}</p>
          </div>
        ))}
        {audit.monitored.map((f) => (
          <div key={f.id} className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="font-mono text-[11px] font-semibold text-slate-700">{f.label}</p>
            <p className="mt-1 text-[12px] leading-relaxed text-slate-600">{f.detail}</p>
          </div>
        ))}
      </div>
      {audit.note ? (
        <p className="mt-3 font-mono text-[10px] leading-relaxed text-slate-500">{audit.note}</p>
      ) : null}
    </section>
  );
}
