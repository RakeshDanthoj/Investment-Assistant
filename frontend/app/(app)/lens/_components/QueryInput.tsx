"use client";

import type { Horizon } from "@/lib/onboarding/state";
import { PULSE_CATEGORY_OPTIONS } from "@/lib/cards/categories";
import { LENS_HORIZON_OPTIONS } from "@/lib/lens/horizons";
import { canSubmitLensQuery } from "@/lib/lens/useLensState";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

const PLACEHOLDER =
  "Describe an event or ask a question — e.g. 'What would a US recession mean for Indian IT exporters?'";

type QueryInputProps = {
  queryText: string;
  sector: string | null;
  horizon: Horizon | null;
  submitting?: boolean;
  onQueryChange: (text: string) => void;
  onSectorChange: (sector: string | null) => void;
  onHorizonChange: (horizon: Horizon | null) => void;
  onSubmit: () => void;
};

export function QueryInput({
  queryText,
  sector,
  horizon,
  submitting = false,
  onQueryChange,
  onSectorChange,
  onHorizonChange,
  onSubmit,
}: QueryInputProps) {
  const canSubmit = canSubmitLensQuery(queryText) && !submitting;

  return (
    <div className="space-y-2">
      <div className="rounded-xl border border-border bg-card shadow-sm focus-within:border-[#1A4FCC] focus-within:shadow-[0_0_0_3px_rgba(26,79,204,0.15)]">
        <Textarea
          value={queryText}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder={PLACEHOLDER}
          rows={4}
          className="min-h-[80px] resize-y border-0 bg-transparent px-4 py-3 text-[15px] leading-relaxed shadow-none focus-visible:ring-0"
          aria-label="Lens query"
        />
        <div className="flex flex-wrap items-center gap-2 border-t border-border px-3 py-2">
          <Select
            value={sector ?? "any"}
            onValueChange={(value) => onSectorChange(value === "any" ? null : value)}
          >
            <SelectTrigger className="h-8 w-[140px] font-mono text-[11px]" aria-label="Sector">
              <SelectValue placeholder="Sector (optional)" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="any">Sector (optional)</SelectItem>
              {PULSE_CATEGORY_OPTIONS.map((opt) => (
                <SelectItem key={opt.id} value={opt.id}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={horizon ?? "any"}
            onValueChange={(value) =>
              onHorizonChange(value === "any" ? null : (value as Horizon))
            }
          >
            <SelectTrigger className="h-8 w-[150px] font-mono text-[11px]" aria-label="Horizon">
              <SelectValue placeholder="Horizon (optional)" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="any">Horizon (optional)</SelectItem>
              {LENS_HORIZON_OPTIONS.map((opt) => (
                <SelectItem key={opt.id} value={opt.id}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            type="button"
            className="ml-auto h-8 shrink-0"
            disabled={!canSubmit}
            onClick={onSubmit}
          >
            Generate card →
          </Button>
        </div>
      </div>
      <p className="font-mono text-[10px] text-slate-400">
        Cards take 30–90 seconds to generate.
      </p>
    </div>
  );
}
