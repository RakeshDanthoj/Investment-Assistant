"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { InstrumentDetail } from "@/lib/cards/threadTypes";

function signalBadgeClass(label: string): string {
  const s = label.toLowerCase();
  if (s.includes("opportunity")) return "bg-[#F0FDF4] text-finnwise-green border-emerald-200";
  if (s.includes("headwind")) return "bg-[#FEF2F2] text-finnwise-red border-red-200";
  return "bg-[#FFF7ED] text-finnwise-amber border-amber-200";
}

type InstrumentCardProps = {
  row: InstrumentDetail;
};

export function InstrumentCard({ row }: InstrumentCardProps) {
  return (
    <Card className="w-full min-w-0 rounded-[10px] py-0 shadow-none ring-slate-200" size="sm">
      <CardContent className="p-4">
        <p className="font-display text-[15px] font-semibold text-slate-900">{row.instrument_id}</p>
        <p className="mt-1 font-mono text-[10px] uppercase tracking-wide text-slate-400">
          Instrument assessment
        </p>
        <Badge
          variant="outline"
          className={`mt-3 rounded-full px-2.5 py-0.5 font-mono text-[10px] font-semibold ${signalBadgeClass(row.signal_label)}`}
        >
          {row.signal_label}
        </Badge>
        {row.reasoning ? (
          <p className="mt-3 text-[13px] leading-relaxed text-slate-600">{row.reasoning}</p>
        ) : null}
        <div className="mt-4 grid min-w-0 gap-3 sm:grid-cols-2">
          <Card className="rounded-lg border-emerald-100 bg-[#F0FDF4] py-0 shadow-none ring-emerald-100">
            <CardContent className="p-3">
              <p className="font-mono text-[10px] font-semibold uppercase tracking-wide text-emerald-800">
                Entry conditions
              </p>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-[12px] leading-snug text-emerald-950">
                {(row.entry_conditions.length ? row.entry_conditions : ["—"]).map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
          <Card className="rounded-lg border-amber-100 bg-[#FFF7ED] py-0 shadow-none ring-amber-100">
            <CardContent className="p-3">
              <p className="font-mono text-[10px] font-semibold uppercase tracking-wide text-amber-900">
                Exit conditions
              </p>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-[12px] leading-snug text-amber-950">
                {(row.exit_conditions.length ? row.exit_conditions : ["—"]).map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      </CardContent>
    </Card>
  );
}
