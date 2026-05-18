"use client";

import type { PulseCard } from "@/lib/cards/pulseTypes";
import { categoryLabel, categoryPillClass } from "@/lib/cards/categories";

function dotClass(tier: string): string {
  if (tier === "high") return "bg-finnwise-blue";
  if (tier === "moderate") return "bg-finnwise-amber";
  return "bg-slate-300";
}

function chipClass(signalType: string): string {
  const s = signalType.toLowerCase();
  if (s.includes("headwind")) return "bg-[#FEE2E2] text-finnwise-red";
  if (s.includes("opportunity")) return "bg-finnwise-modelled-bg text-finnwise-green";
  return "bg-finnwise-judged-bg text-finnwise-amber";
}

type EventCardProps = {
  card: PulseCard;
  selected: boolean;
  onSelect: () => void;
};

export function EventCard({ card, selected, onSelect }: EventCardProps) {
  const resolved = card.lifecycle_state === "resolved";

  return (
    <article>
      <button
        type="button"
        onClick={onSelect}
        className={`w-full rounded-lg border border-slate-200 bg-white p-4 text-left transition-all duration-150 ease-in-out hover:border-slate-300 ${
          selected
            ? "border-l-[3px] border-l-finnwise-blue bg-finnwise-blue-tint/50 shadow-sm"
            : "border-l-[3px] border-l-transparent"
        }`}
      >
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span
            className={`rounded px-2 py-0.5 font-mono text-[9px] font-medium uppercase tracking-wide ${categoryPillClass(card.category)}`}
          >
            {categoryLabel(card.category)}
          </span>
          {resolved ? (
            <span className="rounded-full bg-finnwise-modelled-bg px-2 py-0.5 font-mono text-[9px] font-medium uppercase tracking-wide text-finnwise-green">
              Resolved
            </span>
          ) : null}
        </div>
        <h2 className="font-display text-[15px] font-bold leading-snug text-slate-900">
          {card.headline}
        </h2>
        <p className="mt-2 text-xs italic leading-relaxed text-slate-500">
          {card.event_context}
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9px] uppercase tracking-wide text-slate-400">
              Direction
            </span>
            <span className="flex items-center gap-1.5 font-mono text-[9px] text-slate-600">
              <span
                className={`inline-block h-2 w-2 shrink-0 rounded-full ${dotClass(card.direction_confidence.tier)}`}
                aria-hidden
              />
              {card.direction_confidence.label}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9px] uppercase tracking-wide text-slate-400">
              Magnitude
            </span>
            <span className="flex items-center gap-1.5 font-mono text-[9px] text-slate-600">
              <span
                className={`inline-block h-2 w-2 shrink-0 rounded-full ${dotClass(card.magnitude_confidence.tier)}`}
                aria-hidden
              />
              {card.magnitude_confidence.label}
            </span>
          </div>
        </div>
        {card.instruments?.length ? (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {card.instruments.slice(0, 4).map((i) => (
              <span
                key={`${card.id}-${i.instrument_id}`}
                className={`rounded px-2 py-0.5 font-mono text-[9px] ${chipClass(i.signal_type)}`}
              >
                {i.instrument_id}
              </span>
            ))}
          </div>
        ) : null}
      </button>
    </article>
  );
}
