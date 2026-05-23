"use client";

type LoadingPlaceholderProps = {
  queryText: string;
};

/** Minimal loading shell until P2-S7 wires the six-step pipeline stream. */
export function LoadingPlaceholder({ queryText }: LoadingPlaceholderProps) {
  return (
    <div className="mx-auto w-full max-w-[560px] rounded-xl border border-border bg-card p-6 shadow-sm">
      <blockquote className="border-l-4 border-[#1A4FCC] pl-4 font-display text-lg italic text-foreground">
        {queryText}
      </blockquote>
      <p className="mt-6 text-sm text-muted-foreground">Preparing your card…</p>
      <p className="mt-8 font-mono text-[10px] text-slate-500">
        Every number is validated against the Evidence layer before display.
      </p>
    </div>
  );
}
