"use client";

import { useMemo, useState } from "react";

export type FactorColumn = {
  slug: string;
  display_name: string;
  sort_order: number;
};

export type InstrumentRow = {
  id: string;
  ticker: string;
  display_name: string;
  isin?: string | null;
  exchange?: string | null;
};

export type SensitivityCell = {
  sensitivity: number;
  mmj_tag: string;
  source_url: string;
  retrieved_at: string;
  freshness: "green" | "amber" | "red";
};

export type Props = {
  sectorName: string;
  factors: FactorColumn[];
  instruments: InstrumentRow[];
  sensitivities: Record<string, Record<string, SensitivityCell>>;
};

const MMJ_DOT: Record<string, string> = {
  MEASURED: "#1A4FCC",
  MODELLED: "#0A6644",
  JUDGED: "#D97706",
};

export default function FactorMatrix({ sectorName, factors, instruments, sensitivities }: Props) {
  const factorSlugs = useMemo(() => factors.map((f) => f.slug), [factors]);
  const [activeFactorSlug, setActiveFactorSlug] = useState<string>("all");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col text-xs text-slate-600">
          Sector
          <span className="mt-1 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900">
            {sectorName}
          </span>
        </label>
        <label className="flex flex-col text-xs text-slate-600">
          Highlight factor column
          <select
            className="mt-1 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900"
            value={activeFactorSlug}
            onChange={(e) => setActiveFactorSlug(e.target.value)}
            aria-label="Factor column filter"
          >
            <option value="all">All factors</option>
            {factors.map((f) => (
              <option key={f.slug} value={f.slug}>
                {f.display_name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="relative max-w-full overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-[720px] border-collapse text-left text-sm">
          <thead className="bg-slate-50 text-[11px] font-medium uppercase tracking-wide text-slate-600">
            <tr>
              <th className="sticky left-0 z-30 border-b border-slate-200 bg-slate-50 px-4 py-3 whitespace-nowrap">
                Instrument
              </th>
              {factors.map((f) => (
                <th
                  key={f.slug}
                  className={`border-b border-slate-200 px-3 py-3 text-center whitespace-nowrap ${
                    activeFactorSlug !== "all" && activeFactorSlug !== f.slug ? "opacity-40" : ""
                  }`}
                >
                  <span className="font-normal normal-case">{f.display_name}</span>
                  <span className="mt-1 block text-[10px] text-slate-400">{f.slug.replace(/_/g, " ")}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="text-slate-800">
            {instruments.map((ins, idx) => (
              <tr key={ins.id ?? ins.ticker} className={idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"}>
                <td className="sticky left-0 z-10 border-t border-slate-100 bg-inherit px-4 py-2 align-middle">
                  <div className="flex flex-col">
                    <span className="font-medium">{ins.display_name}</span>
                    <span className="font-mono text-xs text-slate-500">
                      {ins.ticker}
                      {ins.isin ? ` · ${ins.isin}` : ""}
                    </span>
                  </div>
                </td>
                {factorSlugs.map((slug) => {
                  const cell = sensitivities[ins.ticker]?.[slug];
                  if (!cell)
                    return (
                      <td
                        key={slug}
                        className={`border-t border-slate-100 px-3 py-2 text-center align-middle font-mono text-xs text-slate-400 ${
                          activeFactorSlug !== "all" && activeFactorSlug !== slug ? "opacity-40" : ""
                        }`}
                      >
                        –
                      </td>
                    );
                  const dot = MMJ_DOT[cell.mmj_tag.toUpperCase()] ?? "#475569";

                  return (
                    <td
                      key={slug}
                      title={`${cell.mmj_tag} · freshness ${cell.freshness}`}
                      className={`border-t border-slate-100 px-3 py-2 text-center align-middle ${
                        activeFactorSlug !== "all" && activeFactorSlug !== slug ? "opacity-40" : ""
                      }`}
                    >
                      <div className="flex flex-col items-center gap-1">
                        <span className="font-mono text-xs font-semibold">{cell.sensitivity}</span>
                        <span className="inline-flex items-center gap-1 font-mono text-[10px] text-slate-500">
                          <span
                            className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                            style={{ backgroundColor: dot }}
                          />
                          {cell.mmj_tag}
                          <span
                            className="inline-block h-2 w-2 shrink-0 rounded-full"
                            style={{
                              backgroundColor:
                                cell.freshness === "green"
                                  ? "#15803d"
                                  : cell.freshness === "amber"
                                    ? "#D97706"
                                    : "#B91C1C",
                            }}
                            title={`Freshness: ${cell.freshness}`}
                          />
                        </span>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <dl className="grid gap-2 text-xs text-slate-600 md:grid-cols-2">
        <div className="flex gap-2">
          <dt className="font-mono shrink-0">MMJ</dt>
          <dd>Dots follow PRD 8.6: MEASURED blue, MODELLED green, JUDGED amber.</dd>
        </div>
        <div className="flex gap-2">
          <dt className="font-mono shrink-0">Freshness</dt>
          <dd>Second dot mirrors Evidence tab tiers: green ≤6mo, amber 6–18mo, red &gt;18mo.</dd>
        </div>
      </dl>
    </div>
  );
}
