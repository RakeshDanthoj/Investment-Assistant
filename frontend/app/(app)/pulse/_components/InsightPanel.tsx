"use client";

import Link from "next/link";

import type { PulseCard } from "@/lib/cards/pulseTypes";
import { categoryLabel, categoryPillClass } from "@/lib/cards/categories";

function dotClass(tier: string): string {
  if (tier === "high") return "bg-finnwise-blue";
  if (tier === "moderate") return "bg-finnwise-amber";
  return "bg-slate-300";
}

function formatTime(iso: string | null): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

type InsightPanelProps = {
  card: PulseCard | null;
};

export function InsightPanel({ card }: InsightPanelProps) {
  if (!card) {
    return (
      <aside className="hidden min-h-[200px] border-l border-slate-200 bg-white p-6 min-[860px]:block">
        <p className="text-sm text-slate-500">Select an event to preview analysis.</p>
      </aside>
    );
  }

  return (
    <aside className="sticky top-14 hidden h-[calc(100vh-3.5rem)] overflow-y-auto border-l border-slate-200 bg-white p-6 min-[860px]:block">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span
          className={`rounded px-2 py-0.5 font-mono text-[9px] font-medium uppercase tracking-wide ${categoryPillClass(card.category)}`}
        >
          {categoryLabel(card.category)}
        </span>
      </div>
      <h2 className="font-display text-xl font-semibold leading-snug text-slate-900">
        {card.headline}
      </h2>
      <p className="mt-3 text-sm italic leading-relaxed text-slate-500">{card.event_context}</p>

      <div className="mt-6 grid grid-cols-3 gap-2">
        <div className="rounded-md border border-slate-200 bg-finnwise-surface p-2">
          <p className="font-mono text-[8px] uppercase tracking-wide text-slate-400">Direction</p>
          <p className="mt-1 flex items-center gap-1.5 font-mono text-[10px] text-slate-700">
            <span className={`h-2 w-2 rounded-full ${dotClass(card.direction_confidence.tier)}`} />
            {card.direction_confidence.label}
          </p>
        </div>
        <div className="rounded-md border border-slate-200 bg-finnwise-surface p-2">
          <p className="font-mono text-[8px] uppercase tracking-wide text-slate-400">Magnitude</p>
          <p className="mt-1 flex items-center gap-1.5 font-mono text-[10px] text-slate-700">
            <span className={`h-2 w-2 rounded-full ${dotClass(card.magnitude_confidence.tier)}`} />
            {card.magnitude_confidence.label}
          </p>
        </div>
        <div className="rounded-md border border-slate-200 bg-finnwise-surface p-2">
          <p className="font-mono text-[8px] uppercase tracking-wide text-slate-400">Last reviewed</p>
          <p className="mt-1 font-mono text-[10px] text-slate-700">
            {formatTime(card.last_reviewed_at ?? card.created_at)}
          </p>
        </div>
      </div>

      <div className="mt-6 space-y-3">
        <p className="font-mono text-[9px] font-medium uppercase tracking-wide text-slate-400">
          Instruments
        </p>
        {(card.instruments ?? []).slice(0, 4).map((i) => (
          <div
            key={`${card.id}-panel-${i.instrument_id}`}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2"
          >
            <p className="text-sm font-semibold text-slate-900">{i.instrument_id}</p>
            <p className="mt-0.5 font-mono text-[9px] uppercase tracking-wide text-slate-500">
              {i.signal_type.replace(/_/g, " ")}
            </p>
          </div>
        ))}
        {!(card.instruments ?? []).length ? (
          <p className="text-xs text-slate-500">No instruments linked on this card yet.</p>
        ) : null}
      </div>

      <div className="mt-8 border-t border-slate-200 pt-6">
        <Link
          href={`/thread/${card.id}`}
          className="text-sm font-medium text-finnwise-blue transition-colors hover:underline"
        >
          Read full analysis in The Thread →
        </Link>
        <p className="mt-2 font-mono text-[9px] text-slate-400">
          Updated {formatTime(card.last_reviewed_at ?? card.created_at)}
        </p>
      </div>
    </aside>
  );
}
