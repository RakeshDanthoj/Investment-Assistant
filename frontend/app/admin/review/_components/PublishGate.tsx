"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";

export type UngroundedNumber = {
  sentence: string;
  number: string;
  index: number;
};

export type MissingProvenance = {
  evidence_id: string;
  missing_fields: string[];
};

export type NumberValidationPayload = {
  status: "PASS" | "FAIL";
  ungrounded: UngroundedNumber[];
  missing_provenance: MissingProvenance[];
  comparative_flags: string[];
};

export type ChecklistItemPayload = {
  key: string;
  label: string;
  automated: boolean;
  status: "PASS" | "FAIL" | "PENDING";
  message?: string | null;
  details?: Record<string, unknown> | null;
};

export type EditorialChecklistPayload = {
  items: ChecklistItemPayload[];
  all_automated_pass: boolean;
};

export type PublishGateProps = {
  validation: NumberValidationPayload | null;
  checklist?: EditorialChecklistPayload | null;
  loading?: boolean;
  error?: string | null;
};

export function isNumberValidationPass(
  validation: NumberValidationPayload | null | undefined,
): boolean {
  return validation?.status === "PASS";
}

export function isEditorialChecklistReady(
  checklist: EditorialChecklistPayload | null | undefined,
): boolean {
  return checklist?.all_automated_pass === true;
}

export function automatedChecklistFailures(
  checklist: EditorialChecklistPayload | null | undefined,
): ChecklistItemPayload[] {
  if (!checklist) {
    return [];
  }
  return checklist.items.filter((item) => item.automated && item.status === "FAIL");
}

export default function PublishGate({ validation, checklist, loading, error }: PublishGateProps) {
  if (loading) {
    return (
      <div
        className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600"
        data-testid="publish-gate-loading"
        aria-busy="true"
      >
        Running editorial checklist and number validator…
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" data-testid="publish-gate-error">
        <AlertDescription>
          Editorial checks unavailable: {error}. Publish stays disabled until the check succeeds.
        </AlertDescription>
      </Alert>
    );
  }

  if (!validation || !checklist) {
    return (
      <Alert variant="destructive" data-testid="publish-gate-error">
        <AlertDescription>
          Editorial checklist did not return a result. Publish stays disabled.
        </AlertDescription>
      </Alert>
    );
  }

  const failedAuto = automatedChecklistFailures(checklist);
  const numbersPass = validation.status === "PASS";
  const checklistPass = checklist.all_automated_pass;
  const gatePass = numbersPass && checklistPass;

  if (gatePass) {
    return (
      <div
        className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900"
        data-testid="publish-gate-pass"
      >
        <p className="font-medium">Editorial gate — PASS</p>
        <p className="mt-1 text-xs text-emerald-800">
          All four automated checklist items passed, including number grounding.
        </p>
        {validation.comparative_flags.length > 0 ? (
          <p className="mt-2 text-xs text-amber-800" data-testid="publish-gate-soft-warnings">
            Soft flags (non-blocking): {validation.comparative_flags.join(", ")}
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <div
      className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-950"
      data-testid="publish-gate-fail"
    >
      <p className="font-semibold">Editorial gate — FAIL</p>
      <p className="mt-1 text-xs text-red-800">
        Publish is blocked until every automated checklist item passes.
      </p>

      {failedAuto.length > 0 ? (
        <div className="mt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-red-700">
            Checklist failures
          </p>
          <ul className="mt-2 flex flex-col gap-2" data-testid="publish-gate-checklist-failures">
            {failedAuto.map((item) => (
              <li
                key={item.key}
                className="rounded border border-red-100 bg-white px-3 py-2 text-xs text-slate-700"
              >
                <span className="font-semibold text-red-700">{item.label}</span>
                {item.message ? <p className="mt-1 leading-relaxed">{item.message}</p> : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!numbersPass && validation.ungrounded.length > 0 ? (
        <div className="mt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-red-700">
            Ungrounded numbers
          </p>
          <ul className="mt-2 flex flex-col gap-2" data-testid="publish-gate-ungrounded-list">
            {validation.ungrounded.map((item, idx) => (
              <li
                key={`${item.index}-${item.number}-${idx}`}
                className="rounded border border-red-100 bg-white px-3 py-2 text-xs"
              >
                <span className="font-mono font-semibold text-red-700">{item.number}</span>
                <span className="text-red-600"> — sentence {item.index + 1}</span>
                <p className="mt-1 leading-relaxed text-slate-700">{item.sentence}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!numbersPass && validation.missing_provenance.length > 0 ? (
        <div className="mt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-red-700">
            Missing provenance
          </p>
          <ul className="mt-2 flex flex-col gap-2" data-testid="publish-gate-provenance-list">
            {validation.missing_provenance.map((item) => (
              <li
                key={item.evidence_id}
                className="rounded border border-red-100 bg-white px-3 py-2 text-xs text-slate-700"
              >
                <span className="font-mono">{item.evidence_id}</span>
                <span className="text-red-600"> — missing {item.missing_fields.join(", ")}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {validation.comparative_flags.length > 0 ? (
        <p className="mt-3 text-xs text-amber-800" data-testid="publish-gate-soft-warnings">
          Soft flags (non-blocking): {validation.comparative_flags.join(", ")}
        </p>
      ) : null}
    </div>
  );
}
