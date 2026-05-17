"use client";

import { useRouter } from "next/navigation";

import type { SessionApiResult } from "@/lib/onboarding/state";

const SURFACES = [
  {
    slug: "pulse",
    name: "The Pulse",
    description: "Personalised event feed — implications first.",
  },
  {
    slug: "thread",
    name: "The Thread",
    description: "Full Event Intelligence Card when you go deeper.",
  },
  {
    slug: "map",
    name: "The Map",
    description: "Sector learning across the Indian economy.",
  },
  {
    slug: "mirror",
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

function startingSurfaceLabel(surface: string): string {
  return surface === "map" ? "The Map" : "The Pulse";
}

type Step4ModeResultProps = {
  result: SessionApiResult;
};

export function Step4ModeResult({ result }: Step4ModeResultProps) {
  const router = useRouter();

  const targetPath = result.starting_surface === "map" ? "/map" : "/pulse";
  const startingLabel = startingSurfaceLabel(result.starting_surface);

  function handleEnter() {
    router.push(targetPath);
  }

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
        <p className="mt-1 text-xs text-slate-500">
          Preview of what&apos;s inside — your starting surface is{" "}
          <span className="font-medium text-slate-700">{startingLabel}</span>.
        </p>
        <ul className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {SURFACES.map((s) => {
            const isStarting = s.slug === result.starting_surface;
            return (
              <li
                key={s.name}
                className={`rounded-lg border bg-white px-3 py-2.5 text-left ${
                  isStarting
                    ? "border-finnwise-blue ring-2 ring-finnwise-blue/20"
                    : "border-slate-200"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-xs font-semibold text-slate-900">{s.name}</p>
                  {isStarting ? (
                    <span className="shrink-0 rounded bg-finnwise-blue-tint px-1.5 py-0.5 font-mono text-[8px] uppercase tracking-wide text-finnwise-blue">
                      Starts here
                    </span>
                  ) : null}
                </div>
                <p className="mt-0.5 text-[11px] text-slate-500">{s.description}</p>
              </li>
            );
          })}
        </ul>
      </div>

      <button
        type="button"
        onClick={handleEnter}
        className="rounded-lg bg-[#185FA5] px-8 py-3.5 text-sm font-medium text-[#E6F1FB] transition-colors hover:bg-[#144a84]"
      >
        Go to {startingLabel} →
      </button>
    </div>
  );
}
