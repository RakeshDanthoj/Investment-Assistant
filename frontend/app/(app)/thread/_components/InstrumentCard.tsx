"use client";

import type { InstrumentDetail } from "@/lib/cards/threadTypes";

function pillClass(label: string): string {
  const s = label.toLowerCase();
  if (s.includes("opportunity")) return "bg-[#F0FDF4] text-finnwise-green border border-emerald-200";
  if (s.includes("headwind")) return "bg-[#FEF2F2] text-finnwise-red border border-red-200";
  return "bg-[#FFF7ED] text-finnwise-amber border border-amber-200";
}

type InstrumentCardProps = {
  row: InstrumentDetail;
};

export function InstrumentCard({ row }: InstrumentCardProps) {
  return (
    <article className="rounded-[10px] border border-slate-200 bg-white p-4">
      <p className="font-display text-[15px] font-semibold text-slate-900">{row.instrument_id}</p>
      <p className="mt-1 font-mono text-[10px] uppercase tracking-wide text-slate-400">
        Instrument assessment
      </p>
      <span
        className={`mt-3 inline-flex rounded-full px-2.5 py-0.5 font-mono text-[10px] font-semibold ${pillClass(row.signal_label)}`}
      >
        {row.signal_label}
      </span>
      {row.reasoning ? (
        <p className="mt-3 text-[13px] leading-relaxed text-slate-600">{row.reasoning}</p>
      ) : null}
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <section className="rounded-lg border border-emerald-100 bg-[#F0FDF4] p-3">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-wide text-emerald-800">
            Entry conditions
          </p>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-[12px] leading-snug text-emerald-950">
            {(row.entry_conditions.length ? row.entry_conditions : ["—"]).map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </section>
        <section className="rounded-lg border border-amber-100 bg-[#FFF7ED] p-3">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-wide text-amber-900">
            Exit conditions
          </p>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-[12px] leading-snug text-amber-950">
            {(row.exit_conditions.length ? row.exit_conditions : ["—"]).map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </section>
      </div>
    </article>
  );
}
