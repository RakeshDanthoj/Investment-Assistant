"use client";

import { useEffect, useRef, useState } from "react";

import { LENS_DISCLAIMER, LENS_PIPELINE_STEPS } from "@/lib/lens/pipelineSteps";
import { useLensStream } from "@/lib/lens/useLensStream";
import { createClient } from "@/lib/supabase/client";

import { PipelineStep } from "./PipelineStep";

type LoadingCardProps = {
  queryId: string;
  queryText: string;
  onComplete: (cardId: string, generationSeconds: number) => void;
  onError: (message: string) => void;
};

export function LoadingCard({
  queryId,
  queryText,
  onComplete,
  onError,
}: LoadingCardProps) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const startedAtRef = useRef<number | null>(null);

  useEffect(() => {
    startedAtRef.current = Date.now();
  }, [queryId]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!cancelled) {
        setAccessToken(session?.access_token ?? null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleComplete = (cardId: string) => {
    const started = startedAtRef.current ?? Date.now();
    const seconds = Math.max(1, Math.round((Date.now() - started) / 1000));
    onComplete(cardId, seconds);
  };

  const { stepStatuses, progressPercent, streamError } = useLensStream({
    queryId,
    accessToken,
    enabled: Boolean(accessToken),
    onComplete: handleComplete,
    onError,
  });

  return (
    <div className="mx-auto w-full max-w-[560px] rounded-xl border border-border bg-card p-6 shadow-sm">
      <blockquote className="border-l-4 border-[#1A4FCC] pl-4 font-display text-lg italic text-foreground">
        {queryText}
      </blockquote>

      <div
        className="mt-6 h-1.5 w-full overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-valuenow={Math.round(progressPercent)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Card generation progress"
      >
        <div
          className="h-full rounded-full bg-[#1A4FCC] transition-[width] duration-500 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <ol className="mt-6 space-y-3" aria-label="Generation pipeline steps">
        {LENS_PIPELINE_STEPS.map((label, index) => (
          <PipelineStep
            key={label}
            index={index}
            label={label}
            status={stepStatuses[index] ?? "pending"}
          />
        ))}
      </ol>

      {streamError ? (
        <p className="mt-4 text-sm text-destructive" role="alert">
          {streamError}
        </p>
      ) : null}

      <p className="mt-8 font-mono text-[10px] text-slate-500">{LENS_DISCLAIMER}</p>
    </div>
  );
}
