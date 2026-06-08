"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { SessionApiResult } from "@/lib/onboarding/state";
import { syncSessionCookies } from "@/lib/sessionCookies.shared";
import { setStoredSessionId } from "@/lib/sessionProfile";
import { cn } from "@/lib/utils";

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

  useEffect(() => {
    if (!result.session_id) return;
    setStoredSessionId(result.session_id);
    void syncSessionCookies({ sessionId: result.session_id });
  }, [result.session_id]);

  const targetPath = result.starting_surface === "map" ? "/map" : "/pulse";
  const startingLabel = startingSurfaceLabel(result.starting_surface);

  function handleEnter() {
    router.push(targetPath);
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-secondary">
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
        <h2 className="font-display mt-4 text-xl font-medium leading-snug text-foreground">
          You&apos;re {modeHeadline(result.mode)}
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{result.rationale}</p>
      </div>

      <div>
        <p className="font-mono text-[9px] font-medium uppercase tracking-wider text-muted-foreground">
          Your surfaces
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Preview of what&apos;s inside — your starting surface is{" "}
          <span className="font-medium text-foreground">{startingLabel}</span>.
        </p>
        <ul className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {SURFACES.map((s) => {
            const isStarting = s.slug === result.starting_surface;
            return (
              <li key={s.name}>
                <Card
                  size="sm"
                  className={cn(
                    "py-0 shadow-none",
                    isStarting && "ring-2 ring-primary/20",
                  )}
                >
                  <CardContent className="px-3 py-2.5">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-semibold text-foreground">{s.name}</p>
                      {isStarting ? (
                        <Badge variant="secondary" className="shrink-0 px-1.5 py-0.5 text-[8px]">
                          Starts here
                        </Badge>
                      ) : null}
                    </div>
                    <p className="mt-0.5 text-[11px] text-muted-foreground">{s.description}</p>
                  </CardContent>
                </Card>
              </li>
            );
          })}
        </ul>
      </div>

      <Button size="lg" onClick={handleEnter}>
        Go to {startingLabel} →
      </Button>
    </div>
  );
}
