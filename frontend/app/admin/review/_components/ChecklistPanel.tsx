"use client";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
            <div className="flex items-start gap-3">
              <Checkbox
                id={`checklist-${key}`}
                checked={checks[key]}
                onCheckedChange={() => toggle(key)}
                className="mt-0.5"
              />
              <Label
                htmlFor={`checklist-${key}`}
                className="cursor-pointer text-sm leading-snug font-normal text-slate-800"
              >
                {LABELS[key]}
              </Label>
            </div>
          </li>
        ))}
      </ul>

      <div className="flex flex-col gap-3 border-t border-slate-200 pt-6">
        <Button
          type="button"
          data-testid="publish-draft-btn"
          disabled={!allChecked || publishing || regenerating}
          onClick={() => void handlePublish()}
          className="h-auto rounded-lg py-3 font-semibold"
        >
          {publishing ? "Publishing…" : "Publish card"}
        </Button>
        {!allChecked ? (
          <p className="text-[11px] text-slate-500">
            Publish stays disabled until all five checklist items are confirmed.
          </p>
        ) : null}
      </div>

      <div className="flex flex-col gap-3 border-t border-slate-200 pt-6">
        <Label
          htmlFor="regenerate-notes"
          className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400"
        >
          Send back — editor notes for regeneration
        </Label>
        <Textarea
          id="regenerate-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={5}
          placeholder="Concrete fixes you want synthesis to honour…"
          className="rounded-lg shadow-inner"
        />
        <Button
          type="button"
          variant="outline"
          data-testid="regenerate-draft-btn"
          disabled={regenerating || publishing}
          onClick={() => void onRegenerate(notes)}
          className="h-auto rounded-lg py-2.5 font-medium"
        >
          {regenerating ? "Regenerating…" : "Regenerate draft"}
        </Button>
      </div>
    </div>
  );
}
