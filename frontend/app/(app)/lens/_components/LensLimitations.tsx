"use client";

/** PRD §5 Screen 5 — mandatory Lens limitations aside (exact copy). */
export const LENS_LIMITATIONS_TITLE =
  "This is a Lens-generated card, not an editorial card";

export const LENS_LIMITATIONS_BODY =
  "This card has not gone through editorial review. Numbers are validated against the Evidence layer but the analytical framing has not been reviewed by a human editor. Treat with appropriate caution relative to The Thread cards which are editorially reviewed before publication.";

export const LENS_CONFIDENCE_NOTE =
  "Higher Judged proportion than editorial cards. Hypothetical scenarios depend more on historical analogues than current measured data.";

export function LensLimitations() {
  return (
    <section
      data-testid="lens-limitations"
      className="rounded-[10px] border border-slate-200 bg-[#F8FAFC] p-4"
    >
      <h3 className="text-[13px] font-semibold leading-snug text-slate-900">
        {LENS_LIMITATIONS_TITLE}
      </h3>
      <p className="mt-2 text-[12px] leading-relaxed text-slate-600">{LENS_LIMITATIONS_BODY}</p>
    </section>
  );
}
