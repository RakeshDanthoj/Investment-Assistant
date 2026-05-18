"use client";

import { useMemo, useState } from "react";

export type ChecklistPanelProps = {
  onPublish: (editorReviewSeconds: number) => Promise<void>;
  onRegenerate: (notes: string) => Promise<void>;
  openedAtMs: number;
  publishing?: boolean;
  regenerating?: boolean;
};

const ITEM_KEYS = [
  "numbers_mmj",
  "dissent",
  "confidence_freshness",
  "language",
  "no_rec_language",
] as const;

type ItemKey = (typeof ITEM_KEYS)[number];

const LABELS: Record<ItemKey, string> = {
  numbers_mmj:
    "Every quantitative claim carries [MEASURED], [MODELLED], or [JUDGED] and ties back to Evidence.",
  dissent: "A specific dissenting mechanism is present — not a generic disclaimer.",
  confidence_freshness:
    "Direction/magnitude confidence reads consistently with source freshness and caveats.",
  language: "Language is accessible to a non-expert reader (plain explanations, minimal jargon).",
  no_rec_language:
    "No buy / sell / hold or personalised recommendation language appears on the card.",
};

export default function ChecklistPanel({
  onPublish,
  onRegenerate,
  openedAtMs,
  publishing,
  regenerating,
}: ChecklistPanelProps) {
  const [checks, setChecks] = useState<Record<ItemKey, boolean>>({
    numbers_mmj: false,
    dissent: false,
    confidence_freshness: false,
    language: false,
    no_rec_language: false,
  });
  const [notes, setNotes] = useState("");

  const allChecked = useMemo(() => ITEM_KEYS.every((k) => checks[k]), [checks]);

  function toggle(key: ItemKey) {
    setChecks((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  async function handlePublish() {
    const elapsedSec = Math.max(0, Math.floor((Date.now() - openedAtMs) / 1000));
    await onPublish(elapsedSec);
  }

  return (
    <div className="flex flex-col gap-8">
      <header>
        <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">
          Editorial checklist
        </p>
        <h2 className="font-display mt-1 text-lg font-semibold text-slate-900">
          Non-expert review (PRD §6.1)
        </h2>
        <p className="mt-2 text-xs leading-relaxed text-slate-600">
          Tick every item before publishing. Publish logs anonymous time-on-page only (seconds since
          open).
        </p>
      </header>

      <ul className="flex flex-col gap-4">
        {ITEM_KEYS.map((key) => (
          <li key={key}>
            <label className="flex cursor-pointer gap-3 text-sm leading-snug text-slate-800">
              <input
                type="checkbox"
                checked={checks[key]}
                onChange={() => toggle(key)}
                className="mt-1 h-4 w-4 shrink-0 rounded border-slate-300 text-finnwise-blue focus:ring-finnwise-blue"
              />
              <span>{LABELS[key]}</span>
            </label>
          </li>
        ))}
      </ul>

      <div className="flex flex-col gap-3 border-t border-slate-200 pt-6">
        <button
          type="button"
          data-testid="publish-draft-btn"
          disabled={!allChecked || publishing || regenerating}
          onClick={() => void handlePublish()}
          className="rounded-lg bg-finnwise-blue px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:opacity-95 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500"
        >
          {publishing ? "Publishing…" : "Publish card"}
        </button>
        {!allChecked ? (
          <p className="text-[11px] text-slate-500">
            Publish stays disabled until all five checklist items are confirmed.
          </p>
        ) : null}
      </div>

      <div className="flex flex-col gap-3 border-t border-slate-200 pt-6">
        <label className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">
          Send back — editor notes for regeneration
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={5}
          placeholder="Concrete fixes you want synthesis to honour…"
          className="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-800 shadow-inner outline-none focus:border-finnwise-blue"
        />
        <button
          type="button"
          data-testid="regenerate-draft-btn"
          disabled={regenerating || publishing}
          onClick={() => void onRegenerate(notes)}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-800 hover:border-finnwise-blue hover:text-finnwise-blue disabled:cursor-not-allowed disabled:opacity-60"
        >
          {regenerating ? "Regenerating…" : "Regenerate draft"}
        </button>
      </div>
    </div>
  );
}
