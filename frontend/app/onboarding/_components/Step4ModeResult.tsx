"use client";

import { useRouter } from "next/navigation";

import type { SessionApiResult } from "@/lib/onboarding/state";

const SURFACES = [
  {
    name: "The Pulse",
    description: "Personalised event feed — implications first.",
  },
  {
    name: "The Thread",
    description: "Full Event Intelligence Card when you go deeper.",
  },
  {
    name: "The Map",
    description: "Sector learning across the Indian economy.",
  },
  {
    name: "The Mirror",
    description: "Your learning history & accuracy (Phase 2).",
  },
] as const;

function modeHeadline(mode: string): string {
  switch (mode) {
    case "portfolio_builder":
      return "Portfolio Builder";
    case "portfolio_protector":
      return "Portfolio Protector";
    default:
      return "Curious";
  }
}

type Step4ModeResultProps = {
  result: SessionApiResult;
};

export function Step4ModeResult({ result }: Step4ModeResultProps) {
  const router = useRouter();

  const targetPath = result.starting_surface === "map" ? "/map" : "/pulse";

  return (
    <div className="flex flex-col gap-6">
      <div className="text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-finnwise-blue-tint">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden>
            <title>Complete</title>
            <path
              d="M4 11.5L9 16.5L18 6"
              stroke="#1A4FCC"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <h2 className="font-display mt-4 text-xl font-medium leading-snug text-slate-900">
          You&apos;re {modeHeadline(result.mode)}
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">{result.rationale}</p>
      </div>

      <div>
        <p className="font-mono text-[9px] font-medium uppercase tracking-wider text-slate-400">
          Your surfaces
        </p>
        <ul className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {SURFACES.map((s) => (
            <li
              key={s.name}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-left"
            >
              <p className="text-xs font-semibold text-slate-900">{s.name}</p>
              <p className="mt-0.5 text-[11px] text-slate-500">{s.description}</p>
            </li>
          ))}
        </ul>
      </div>

      <button
        type="button"
        onClick={() => router.push(targetPath)}
        className="rounded-lg bg-[#185FA5] px-8 py-3.5 text-sm font-medium text-[#E6F1FB] transition-colors hover:bg-[#144a84]"
      >
        Enter FinnWise →
      </button>
    </div>
  );
}
