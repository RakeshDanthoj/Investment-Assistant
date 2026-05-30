"use client";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { useMemo, useState } from "react";

import PublishGate, {
  isEditorialChecklistReady,
  isNumberValidationPass,
  type EditorialChecklistPayload,
  type NumberValidationPayload,
} from "./PublishGate";
import RegenSection from "./RegenSection";

export type ChecklistPanelProps = {
  draftId: string;
  onPublish: (editorReviewSeconds: number) => Promise<void>;
  onRegenerate: (notes: string) => Promise<void>;
  onReload: () => Promise<void>;
  openedAtMs: number;
  publishing?: boolean;
  regenerating?: boolean;
  numberValidation?: NumberValidationPayload | null;
  editorialChecklist?: EditorialChecklistPayload | null;
  numberValidationLoading?: boolean;
  numberValidationError?: string | null;
  fullRegenCount?: number;
  poRegenFlagCleared?: boolean;
};

function statusBadgeClass(status: "PASS" | "FAIL" | "PENDING"): string {
  if (status === "PASS") {
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }
  if (status === "FAIL") {
    return "border-red-200 bg-red-50 text-red-800";
  }
  return "border-slate-200 bg-slate-50 text-slate-600";
}

export default function ChecklistPanel({
  draftId,
  onPublish,
  onRegenerate,
  onReload,
  openedAtMs,
  publishing,
  regenerating,
  numberValidation,
  editorialChecklist,
  numberValidationLoading,
  numberValidationError,
  fullRegenCount = 0,
  poRegenFlagCleared = false,
}: ChecklistPanelProps) {
  const [plainEnglishConfirmed, setPlainEnglishConfirmed] = useState(false);
  const [notes, setNotes] = useState("");

  const checklistItems = editorialChecklist?.items ?? [];
  const automatedItems = checklistItems.filter((item) => item.automated);
  const manualItem = checklistItems.find((item) => !item.automated);

  const numbersPass = isNumberValidationPass(numberValidation);
  const automatedPass = isEditorialChecklistReady(editorialChecklist);
  const canPublish =
    numbersPass &&
    automatedPass &&
    plainEnglishConfirmed &&
    !numberValidationLoading &&
    !numberValidationError &&
    numberValidation != null &&
    editorialChecklist != null;

  const manualStatus = useMemo(() => {
    if (plainEnglishConfirmed) {
      return "PASS" as const;
    }
    return manualItem?.status ?? ("PENDING" as const);
  }, [manualItem?.status, plainEnglishConfirmed]);

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
          Four items auto-check on load. Confirm plain English, then publish. Publish logs anonymous
          time-on-page only (seconds since open).
        </p>
      </header>

      <ul className="flex flex-col gap-4">
        {automatedItems.map((item) => (
          <li key={item.key}>
            <div className="flex items-start gap-3">
              <span
                className={cn(
                  "mt-0.5 inline-flex min-w-[3.25rem] justify-center rounded border px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide",
                  statusBadgeClass(item.status),
                )}
                data-testid={`checklist-status-${item.key}`}
              >
                {item.status}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm leading-snug text-slate-800">{item.label}</p>
                {item.message ? (
                  <p className="mt-1 text-xs leading-relaxed text-slate-500">{item.message}</p>
                ) : null}
              </div>
            </div>
          </li>
        ))}

        {manualItem ? (
          <li key={manualItem.key}>
            <div className="flex items-start gap-3">
              <Checkbox
                id={`checklist-${manualItem.key}`}
                checked={plainEnglishConfirmed}
                onCheckedChange={() => setPlainEnglishConfirmed((prev) => !prev)}
                className="mt-0.5"
              />
              <div className="min-w-0 flex-1">
                <Label
                  htmlFor={`checklist-${manualItem.key}`}
                  className="cursor-pointer text-sm leading-snug font-normal text-slate-800"
                >
                  {manualItem.label}
                </Label>
                <p className="mt-1 text-xs text-slate-500">
                  Manual confirmation required — status:{" "}
                  <span
                    className={cn(
                      "inline-flex rounded border px-1.5 py-0.5 font-mono text-[10px] uppercase",
                      statusBadgeClass(manualStatus),
                    )}
                    data-testid="checklist-status-plain_english"
                  >
                    {manualStatus}
                  </span>
                </p>
              </div>
            </div>
          </li>
        ) : null}
      </ul>

      <PublishGate
        validation={numberValidation ?? null}
        checklist={editorialChecklist ?? null}
        loading={numberValidationLoading}
        error={numberValidationError}
      />

      <div className="flex flex-col gap-3 border-t border-slate-200 pt-6">
        <Button
          type="button"
          data-testid="publish-draft-btn"
          disabled={!canPublish || publishing || regenerating}
          onClick={() => void handlePublish()}
          className="h-auto rounded-lg py-3 font-semibold"
        >
          {publishing ? "Publishing…" : "Publish card"}
        </Button>
        {!canPublish ? (
          <p className="text-[11px] text-slate-500">
            Publish stays disabled until all four automated checks pass and plain English is
            confirmed.
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
          {regenerating ? "Regenerating…" : "Regenerate draft (new card)"}
        </Button>
      </div>

      <RegenSection
        cardId={draftId}
        fullRegenCount={fullRegenCount}
        poRegenFlagCleared={poRegenFlagCleared}
        disabled={publishing || regenerating}
        onSectionRegenComplete={onReload}
        onFullRegenComplete={onReload}
      />
    </div>
  );
}
