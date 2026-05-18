"use client";

export function FogOfWarBanner() {
  return (
    <div
      role="status"
      className="border-b border-amber-200 bg-gradient-to-r from-[#FEF3C7] to-[#FFFBEB] px-4 py-3"
    >
      <div className="mx-auto flex max-w-6xl items-start gap-3">
        <span className="mt-0.5 text-finnwise-amber" aria-hidden>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <title>Fog of War</title>
            <path
              d="M10 3L2 17h16L10 3z"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinejoin="round"
            />
            <path d="M10 7v4M10 13h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </span>
        <div>
          <p className="font-mono text-[11px] font-semibold uppercase tracking-wide text-finnwise-amber">
            Fog of War
          </p>
          <p className="mt-1 text-sm leading-snug text-slate-800">
            Several major events are active at once with overlapping themes. Model confidence is
            intentionally capped — read dissent and evidence before acting on direction or magnitude.
          </p>
        </div>
      </div>
    </div>
  );
}
