"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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

function mmjVariant(mmj: string): "measured" | "modelled" | "judged" {
  const k = mmj.toUpperCase();
  if (k === "MODELLED") return "modelled";
  if (k === "JUDGED") return "judged";
  return "measured";
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
    <Card className="w-full min-w-0 rounded-[10px] py-0 shadow-none ring-slate-200">
      <CardContent className="min-w-0 space-y-4 p-6">
        <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">Evidence</p>
        <p className="text-[12px] leading-relaxed text-slate-600">
          Human-sourced references only — model outputs never appear as rows in this table (PRD §5).
        </p>
        <Table className="min-w-[560px] text-[12px]">
          <TableHeader>
            <TableRow className="border-slate-200 bg-slate-50 hover:bg-slate-50">
              <TableHead className="px-2 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-500">
                Claim
              </TableHead>
              <TableHead className="px-2 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-500">
                Source
              </TableHead>
              <TableHead className="px-2 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-500">
                Date
              </TableHead>
              <TableHead className="px-2 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-500">
                Fresh
              </TableHead>
              <TableHead className="px-2 py-2 font-mono text-[10px] uppercase tracking-wide text-slate-500">
                MMJ
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tableRows.map((r, idx) => (
              <TableRow key={`${idx}-${r.claim.slice(0, 24)}`} className="border-slate-100">
                <TableCell className="px-2 py-2 align-top font-medium whitespace-normal text-slate-800">
                  {r.claim}
                </TableCell>
                <TableCell className="px-2 py-2 align-top whitespace-normal text-slate-600">
                  {r.source_name}
                </TableCell>
                <TableCell className="px-2 py-2 align-top whitespace-normal text-slate-600">
                  {r.date_label}
                </TableCell>
                <TableCell className="px-2 py-2 align-top">
                  <FreshDot tone={r.freshness} />
                </TableCell>
                <TableCell className="px-2 py-2 align-top">
                  <Badge variant={mmjVariant(r.mmj)}>{r.mmj.toLowerCase()}</Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {markdown.trim() ? (
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-4 font-mono text-[11px] leading-relaxed whitespace-pre-wrap text-slate-700">
            {markdown}
          </div>
        ) : null}
        {macroStub.trim() ? (
          <p className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-[12px] leading-relaxed text-slate-600">
            {macroStub}
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}
