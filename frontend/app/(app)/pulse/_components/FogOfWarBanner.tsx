"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export function FogOfWarBanner() {
  return (
    <Alert
      role="status"
      className="rounded-none border-x-0 border-t-0 border-amber-200 bg-gradient-to-r from-[#FEF3C7] to-[#FFFBEB] px-4 py-3"
    >
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
        <title>Fog of War</title>
        <path
          d="M10 3L2 17h16L10 3z"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinejoin="round"
          className="text-finnwise-amber"
        />
        <path
          d="M10 7v4M10 13h.01"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          className="text-finnwise-amber"
        />
      </svg>
      <AlertTitle className="font-mono text-[11px] font-semibold uppercase tracking-wide text-finnwise-amber">
        Fog of War
      </AlertTitle>
      <AlertDescription className="mt-1 text-sm leading-snug text-slate-800">
        Several major events are active at once with overlapping themes. Model confidence is
        intentionally capped — read dissent and evidence before acting on direction or magnitude.
      </AlertDescription>
    </Alert>
  );
}
