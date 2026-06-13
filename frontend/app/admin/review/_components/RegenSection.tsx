"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { getLongRunningApiBaseUrl } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useCallback, useState } from "react";

import type { NumberValidationPayload } from "./PublishGate";

export type RegenSectionKey = "insight" | "context" | "evidence" | "dissent" | "framework";

export type ConsistencyCheckPayload = {
  status: "PASS" | "FAIL";
  conflicts: Array<{ entity: string; message: string }>;
};

export type RegenSectionResponse = {
  card_id: string;
  section: RegenSectionKey;
  previous_hash: string;
  new_hash: string;
  number_validation: NumberValidationPayload;
  consistency_check: ConsistencyCheckPayload;
};

export type RegenSectionProps = {
  cardId: string;
  fullRegenCount: number;
  poRegenFlagCleared: boolean;
  disabled?: boolean;
  onSectionRegenComplete: () => Promise<void>;
  onFullRegenComplete: () => Promise<void>;
};

const SECTION_OPTIONS: Array<{ value: RegenSectionKey; label: string }> = [
  { value: "insight", label: "Insight" },
  { value: "context", label: "Context" },
  { value: "evidence", label: "Evidence" },
  { value: "dissent", label: "Dissent" },
  { value: "framework", label: "Framework" },
];

function statusBadgeClass(status: "PASS" | "FAIL"): string {
  return status === "PASS"
    ? "border-emerald-200 bg-emerald-50 text-emerald-800"
    : "border-red-200 bg-red-50 text-red-800";
}

export default function RegenSection({
  cardId,
  fullRegenCount,
  poRegenFlagCleared,
  disabled,
  onSectionRegenComplete,
  onFullRegenComplete,
}: RegenSectionProps) {
  const [section, setSection] = useState<RegenSectionKey>("insight");
  const [editorNote, setEditorNote] = useState("");
  const [fullNotes, setFullNotes] = useState("");
  const [sectionLoading, setSectionLoading] = useState(false);
  const [fullLoading, setFullLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<RegenSectionResponse | null>(null);

  const noteTooLong = editorNote.length > 500;
  const canSubmitSection = editorNote.trim().length > 0 && !noteTooLong && !sectionLoading;

  const handleSectionRegen = useCallback(async () => {
    setSectionLoading(true);
    setError(null);
    setLastResult(null);
    try {
      const base = getLongRunningApiBaseUrl().replace(/\/$/, "");
      const res = await fetch(`${base}/api/admin/cards/${cardId}/regenerate-section`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ section, editor_note: editorNote.trim() }),
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        let message = text || `${res.status} ${res.statusText}`;
        try {
          const parsed = JSON.parse(text) as { detail?: { message?: string } };
          if (parsed.detail?.message) {
            message = parsed.detail.message;
          }
        } catch {
          // keep raw message
        }
        throw new Error(message);
      }
      const body = (await res.json()) as RegenSectionResponse;
      setLastResult(body);
      await onSectionRegenComplete();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Section regen failed.");
    } finally {
      setSectionLoading(false);
    }
  }, [cardId, editorNote, onSectionRegenComplete, section]);

  const handleFullRegen = useCallback(
    async (confirmed: boolean) => {
      setFullLoading(true);
      setError(null);
      try {
        const base = getLongRunningApiBaseUrl().replace(/\/$/, "");
        const res = await fetch(`${base}/api/admin/cards/${cardId}/regenerate-full`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ editor_notes: fullNotes, confirmed }),
        });
        if (res.status === 409) {
          const text = await res.text().catch(() => "");
          let message =
            "Full regen requires confirmation — this will regenerate all sections (~3× tokens).";
          try {
            const parsed = JSON.parse(text) as { detail?: { message?: string } };
            if (parsed.detail?.message) {
              message = parsed.detail.message;
            }
          } catch {
            // keep default
          }
          const ok = window.confirm(`${message}\n\nProceed with full regeneration?`);
          if (ok) {
            await handleFullRegen(true);
          }
          return;
        }
        if (res.status === 423) {
          throw new Error(
            "Full regen blocked — Product Owner review required (full_regen_count >= 2).",
          );
        }
        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new Error(text || `${res.status} ${res.statusText}`);
        }
        setLastResult(null);
        await onFullRegenComplete();
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Full regen failed.");
      } finally {
        setFullLoading(false);
      }
    },
    [cardId, fullNotes, onFullRegenComplete],
  );

  const fullRegenBlocked = fullRegenCount >= 2 && !poRegenFlagCleared;

  return (
    <div className="flex flex-col gap-4 border-t border-slate-200 pt-6">
      <header>
        <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">
          Targeted regen
        </p>
        <h3 className="font-display mt-1 text-base font-semibold text-slate-900">
          Regenerate one section
        </h3>
        <p className="mt-1 text-xs leading-relaxed text-slate-600">
          Re-run only the failing ICE section with your annotation. Approved sections stay
          unchanged. Post-regen number validator and consistency check run automatically.
        </p>
      </header>

      <div className="flex flex-col gap-2">
        <Label htmlFor="regen-section-select" className="text-xs text-slate-600">
          Section
        </Label>
        <Select
          value={section}
          onValueChange={(value) => setSection(value as RegenSectionKey)}
          disabled={disabled || sectionLoading || fullLoading}
        >
          <SelectTrigger id="regen-section-select" data-testid="regen-section-select">
            <SelectValue placeholder="Choose section" />
          </SelectTrigger>
          <SelectContent>
            {SECTION_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-col gap-2">
        <Label htmlFor="regen-editor-note" className="text-xs text-slate-600">
          Editor note (max 500 chars)
        </Label>
        <Textarea
          id="regen-editor-note"
          data-testid="regen-editor-note"
          value={editorNote}
          onChange={(e) => setEditorNote(e.target.value)}
          rows={4}
          placeholder="What is wrong with this section and how should it change?"
          className="rounded-lg shadow-inner"
          disabled={disabled || sectionLoading || fullLoading}
        />
        {noteTooLong ? (
          <p className="text-xs text-red-600">Editor note must be at most 500 characters.</p>
        ) : null}
      </div>

      <Button
        type="button"
        variant="secondary"
        data-testid="regen-section-submit"
        disabled={disabled || !canSubmitSection || fullLoading}
        onClick={() => void handleSectionRegen()}
        className="h-auto rounded-lg py-2.5 font-medium"
      >
        {sectionLoading ? "Regenerating section…" : "Regenerate section"}
      </Button>

      {lastResult ? (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
          <p className="font-semibold text-slate-900">Post-regen checks</p>
          <p className="mt-2">
            Number validator:{" "}
            <span
              className={cn(
                "inline-flex rounded border px-1.5 py-0.5 font-mono text-[10px] uppercase",
                statusBadgeClass(lastResult.number_validation.status),
              )}
              data-testid="regen-number-validation-status"
            >
              {lastResult.number_validation.status}
            </span>
          </p>
          <p className="mt-1">
            Consistency:{" "}
            <span
              className={cn(
                "inline-flex rounded border px-1.5 py-0.5 font-mono text-[10px] uppercase",
                statusBadgeClass(lastResult.consistency_check.status),
              )}
              data-testid="regen-consistency-status"
            >
              {lastResult.consistency_check.status}
            </span>
          </p>
          {lastResult.previous_hash !== lastResult.new_hash ? (
            <p className="mt-2 font-mono text-[10px] text-slate-500">
              Section content hash changed ({lastResult.section}).
            </p>
          ) : null}
          {lastResult.consistency_check.conflicts.length > 0 ? (
            <ul className="mt-2 list-disc pl-4">
              {lastResult.consistency_check.conflicts.map((c) => (
                <li key={c.entity}>{c.message}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      <div className="flex flex-col gap-3 border-t border-slate-100 pt-4">
        <Label htmlFor="full-regen-notes" className="text-xs text-slate-600">
          Full regen notes (optional)
        </Label>
        <Textarea
          id="full-regen-notes"
          value={fullNotes}
          onChange={(e) => setFullNotes(e.target.value)}
          rows={3}
          placeholder="Use when the whole card is fundamentally wrong…"
          className="rounded-lg shadow-inner"
          disabled={disabled || sectionLoading || fullLoading || fullRegenBlocked}
        />
        <Button
          type="button"
          variant="outline"
          data-testid="regen-full-submit"
          disabled={disabled || sectionLoading || fullLoading || fullRegenBlocked}
          onClick={() => void handleFullRegen(fullRegenCount < 1)}
          className="h-auto rounded-lg py-2.5 font-medium"
        >
          {fullLoading
            ? "Full regenerating…"
            : fullRegenCount >= 1
              ? "Full regen (confirmation required)"
              : "Full regen all sections"}
        </Button>
        {fullRegenCount >= 1 ? (
          <p className="text-[11px] text-slate-500">
            Full regen count: {fullRegenCount}. Second run prompts confirmation; third blocks until
            PO clears the flag.
          </p>
        ) : null}
        {fullRegenBlocked ? (
          <p className="text-[11px] text-red-600">
            Full regen blocked — contact Product Owner to clear the review flag.
          </p>
        ) : null}
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}
