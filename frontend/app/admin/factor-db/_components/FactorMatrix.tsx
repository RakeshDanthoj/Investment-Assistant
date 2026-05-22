"use client";

import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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

function mmjBadgeVariant(tag: string): "measured" | "modelled" | "judged" | "outline" {
  const upper = tag.toUpperCase();
  if (upper === "MEASURED") return "measured";
  if (upper === "MODELLED") return "modelled";
  if (upper === "JUDGED") return "judged";
  return "outline";
}

export default function FactorMatrix({ sectorName, factors, instruments, sensitivities }: Props) {
  const factorSlugs = useMemo(() => factors.map((f) => f.slug), [factors]);
  const [activeFactorSlug, setActiveFactorSlug] = useState<string>("all");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-4">
        <div className="flex flex-col gap-1">
          <Label className="text-xs text-slate-600">Sector</Label>
          <span className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900">
            {sectorName}
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="factor-column-filter" className="text-xs text-slate-600">
            Highlight factor column
          </Label>
          <Select value={activeFactorSlug} onValueChange={setActiveFactorSlug}>
            <SelectTrigger id="factor-column-filter" aria-label="Factor column filter">
              <SelectValue placeholder="All factors" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All factors</SelectItem>
              {factors.map((f) => (
                <SelectItem key={f.slug} value={f.slug}>
                  {f.display_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="relative max-w-full overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <Table className="min-w-[720px] border-collapse text-left text-sm">
          <TableHeader className="bg-slate-50 text-[11px] font-medium uppercase tracking-wide text-slate-600">
            <TableRow className="hover:bg-transparent">
              <TableHead className="sticky left-0 z-30 border-b border-slate-200 bg-slate-50 px-4 py-3 whitespace-nowrap">
                Instrument
              </TableHead>
              {factors.map((f) => (
                <TableHead
                  key={f.slug}
                  className={`border-b border-slate-200 px-3 py-3 text-center whitespace-nowrap ${
                    activeFactorSlug !== "all" && activeFactorSlug !== f.slug ? "opacity-40" : ""
                  }`}
                >
                  <span className="font-normal normal-case">{f.display_name}</span>
                  <span className="mt-1 block text-[10px] text-slate-400">{f.slug.replace(/_/g, " ")}</span>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody className="text-slate-800">
            {instruments.map((ins, idx) => (
              <TableRow
                key={ins.id ?? ins.ticker}
                className={idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"}
              >
                <TableCell className="sticky left-0 z-10 border-t border-slate-100 bg-inherit px-4 py-2 align-middle">
                  <div className="flex flex-col">
                    <span className="font-medium">{ins.display_name}</span>
                    <span className="font-mono text-xs text-slate-500">
                      {ins.ticker}
                      {ins.isin ? ` · ${ins.isin}` : ""}
                    </span>
                  </div>
                </TableCell>
                {factorSlugs.map((slug) => {
                  const cell = sensitivities[ins.ticker]?.[slug];
                  if (!cell)
                    return (
                      <TableCell
                        key={slug}
                        className={`border-t border-slate-100 px-3 py-2 text-center align-middle font-mono text-xs text-slate-400 ${
                          activeFactorSlug !== "all" && activeFactorSlug !== slug ? "opacity-40" : ""
                        }`}
                      >
                        –
                      </TableCell>
                    );

                  return (
                    <TableCell
                      key={slug}
                      title={`${cell.mmj_tag} · freshness ${cell.freshness}`}
                      className={`border-t border-slate-100 px-3 py-2 text-center align-middle ${
                        activeFactorSlug !== "all" && activeFactorSlug !== slug ? "opacity-40" : ""
                      }`}
                    >
                      <div className="flex flex-col items-center gap-1">
                        <span className="font-mono text-xs font-semibold">{cell.sensitivity}</span>
                        <span className="inline-flex items-center gap-1">
                          <Badge variant={mmjBadgeVariant(cell.mmj_tag)}>{cell.mmj_tag}</Badge>
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
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
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
