"use client";

import type { EvidenceRow } from "@/lib/cards/threadTypes";

function FreshDot({ tone }: { tone: EvidenceRow["freshness"] }) {
  const cls =
    tone === "green"
      ? "bg-emerald-500"
      : tone === "amber"
        ? "bg-amber-500"
        : "bg-red-500";
  return (
    <span className="inline-flex items-center gap-1 font-mono text-[10px] text-slate-600">
      <span className={`inline-block h-2 w-2 rounded-full ${cls}`} aria-hidden />
      {tone}
    </span>
  );
}

function mmjPill(mmj: string): string {
  const k = mmj.toUpperCase();
  if (k === "MODELLED") return "bg-finnwise-modelled-bg text-finnwise-green";
  if (k === "JUDGED") return "bg-finnwise-judged-bg text-finnwise-amber";
  return "bg-finnwise-blue-tint text-finnwise-blue";
}

type EvidenceLayerProps = {
  rows: EvidenceRow[];
  markdown: string;
  macroStub: string;
};

export function EvidenceLayer({ rows, markdown, macroStub }: EvidenceLayerProps) {
  const tableRows =
    rows.length > 0
      ? rows
      : [
          {
            claim: "Structured sources will populate here once citation rows are emitted.",
            source_name: "—",
            date_label: "—",
            retrieved_at: null,
            freshness: "amber" as const,
            mmj: "MEASURED",
          },
        ];

  return (
    <div className="space-y-4 rounded-[10px] border border-slate-200 bg-white p-6">
      <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">Evidence</p>
      <p className="text-[12px] leading-relaxed text-slate-600">
        Human-sourced references only — model outputs never appear as rows in this table (PRD §5).
      </p>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] border-collapse text-left text-[12px]">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 font-mono text-[10px] uppercase tracking-wide text-slate-500">
              <th className="px-2 py-2">Claim</th>
              <th className="px-2 py-2">Source</th>
              <th className="px-2 py-2">Date</th>
              <th className="px-2 py-2">Fresh</th>
              <th className="px-2 py-2">MMJ</th>
            </tr>
          </thead>
          <tbody>
            {tableRows.map((r, idx) => (
              <tr key={`${idx}-${r.claim.slice(0, 24)}`} className="border-b border-slate-100">
                <td className="px-2 py-2 align-top font-medium text-slate-800">{r.claim}</td>
                <td className="px-2 py-2 align-top text-slate-600">{r.source_name}</td>
                <td className="px-2 py-2 align-top text-slate-600">{r.date_label}</td>
                <td className="px-2 py-2 align-top">
                  <FreshDot tone={r.freshness} />
                </td>
                <td className="px-2 py-2 align-top">
                  <span
                    className={`inline-flex rounded px-2 py-0.5 font-mono text-[10px] font-semibold ${mmjPill(r.mmj)}`}
                  >
                    {r.mmj.toLowerCase()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {markdown.trim() ? (
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-4 font-mono text-[11px] leading-relaxed text-slate-700 whitespace-pre-wrap">
          {markdown}
        </div>
      ) : null}
      {macroStub.trim() ? (
        <p className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-[12px] leading-relaxed text-slate-600">
          {macroStub}
        </p>
      ) : null}
    </div>
  );
}
