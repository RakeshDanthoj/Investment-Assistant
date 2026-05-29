"use client";

import { useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getApiBaseUrl } from "@/lib/api";
import { deferAfterPaint } from "@/lib/deferAfterPaint";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

/** Four discrete prediction paths — no allocation advice (PRD §5 Screen 3). */
export const PREDICTION_OPTIONS = [
  "Primary thesis unfolds — mechanisms align with the stated horizon.",
  "Direction plausible but slower — drag persists beyond the card window.",
  "Thesis weakens — a key assumption breaks earlier than modeled.",
  "Mixed — competing mechanisms cancel; outcome stays ambiguous.",
] as const;

/** PRD §5 Screen 3 Prediction Logger disclaimer — exact copy. */
export const PREDICTION_DISCLAIMER =
  "This is tracked for your learning. It does not constitute an investment decision. Reviewed in The Mirror when the card resolves.";

export const PREDICTION_CONFIRMATION =
  "Your view logged — reviewed in The Mirror when this resolves.";

type PredictionLoggerProps = {
  cardId: string;
};

type LoggerPhase = "form" | "loading" | "logged" | "error";

export function PredictionLogger({ cardId }: PredictionLoggerProps) {
  const [selected, setSelected] = useState<number | null>(null);
  const [phase, setPhase] = useState<LoggerPhase>("form");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setSelected(null);
    setPhase("form");
    setErrorMessage(null);
  }, [cardId]);

  useEffect(() => {
    let cancelled = false;

    async function loadExisting() {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session?.access_token || cancelled) return;

      try {
        const base = getApiBaseUrl();
        const res = await fetch(`${base}/api/predictions/me`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
          cache: "no-store",
        });
        if (!res.ok || cancelled) return;
        const data = (await res.json()) as {
          items: Array<{ card_id: string }>;
        };
        if (data.items.some((row) => row.card_id === cardId)) {
          setPhase("logged");
        }
      } catch {
        /* ignore — form remains available */
      }
    }

    void deferAfterPaint(() => {
      if (!cancelled) void loadExisting();
    });
    return () => {
      cancelled = true;
    };
  }, [cardId]);

  async function submit() {
    if (selected === null) return;
    setPhase("loading");
    setErrorMessage(null);

    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) {
      setPhase("error");
      setErrorMessage("Sign in to log your prediction.");
      return;
    }

    try {
      const base = getApiBaseUrl();
      const res = await fetch(`${base}/api/predictions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          card_id: cardId,
          prediction_text: PREDICTION_OPTIONS[selected],
        }),
      });
      if (res.status === 409) {
        setPhase("logged");
        return;
      }
      if (!res.ok) {
        const raw = await res.text();
        throw new Error(raw || `Log failed (${res.status})`);
      }
      setPhase("logged");
    } catch (e) {
      setPhase("error");
      setErrorMessage(e instanceof Error ? e.message : "Could not log prediction.");
    }
  }

  if (phase === "logged") {
    return (
      <Card
        className="w-full min-w-0 rounded-[10px] border-[#BFDBFE] bg-[#F0F4FF] py-0 shadow-none ring-0"
        aria-live="polite"
      >
        <CardContent className="p-5">
          <p className="font-mono text-[12px] leading-relaxed text-slate-700">
            {PREDICTION_CONFIRMATION}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full min-w-0 rounded-[10px] border-[#BFDBFE] bg-[#F0F4FF] py-0 shadow-none ring-0">
      <CardContent className="p-5">
        <p className="font-display text-sm font-semibold text-foreground">
          Before you open the causal chain — what do you think happens next for this event?
        </p>
        <div className="mt-3 flex min-w-0 flex-col gap-2" role="listbox" aria-label="Prediction choices">
          {PREDICTION_OPTIONS.map((opt, i) => (
            <Button
              key={opt}
              type="button"
              role="option"
              variant={selected === i ? "selected" : "outline"}
              aria-selected={selected === i}
              onClick={() => {
                setSelected(i);
                setPhase("form");
                setErrorMessage(null);
              }}
              className={cn(
                "h-auto w-full max-w-full justify-start whitespace-normal rounded-lg px-3 py-2.5 text-left font-mono text-[12px] font-normal leading-snug",
                selected !== i && "border-slate-200 bg-white/70 text-slate-700 hover:border-primary/60",
              )}
            >
              {opt}
            </Button>
          ))}
        </div>
        <Button
          disabled={selected === null || phase === "loading"}
          onClick={() => {
            void submit();
          }}
          className="mt-4 font-mono text-[11px] font-semibold uppercase tracking-wide"
        >
          {phase === "loading" ? "Logging…" : "Log my prediction →"}
        </Button>
        <p className="mt-3 font-mono text-[10px] leading-relaxed text-muted-foreground">
          {PREDICTION_DISCLAIMER}
        </p>
        {errorMessage ? (
          <Alert variant="destructive" className="mt-2">
            <AlertDescription className="font-mono text-[11px]">{errorMessage}</AlertDescription>
          </Alert>
        ) : null}
      </CardContent>
    </Card>
  );
}
