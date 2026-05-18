"use client";

import { useState } from "react";

import { getApiBaseUrl } from "@/lib/api";

/** Four discrete prediction paths — no allocation advice (PRD §5 Screen 3). */
export const PREDICTION_OPTIONS = [
  "Primary thesis unfolds — mechanisms align with the stated horizon.",
  "Direction plausible but slower — drag persists beyond the card window.",
  "Thesis weakens — a key assumption breaks earlier than modeled.",
  "Mixed — competing mechanisms cancel; outcome stays ambiguous.",
] as const;

type PredictionLoggerProps = {
  cardId: string;
};

function devUserId(): string | null {
  const fromEnv = process.env.NEXT_PUBLIC_FINNWISE_USER_ID?.trim();
  return fromEnv || null;
}

export function PredictionLogger({ cardId }: PredictionLoggerProps) {
  const [selected, setSelected] = useState<number | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);

  const userId = devUserId();

  async function submit() {
    if (selected === null || !userId) return;
    setStatus("loading");
    setMessage(null);
    try {
      const base = getApiBaseUrl();
      const res = await fetch(`${base}/api/predictions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          card_id: cardId,
          user_id: userId,
          prediction_text: PREDICTION_OPTIONS[selected],
        }),
      });
      if (!res.ok) {
        const raw = await res.text();
        throw new Error(raw || `Log failed (${res.status})`);
      }
      setStatus("success");
      setMessage("Prediction logged for your learning track.");
    } catch (e) {
      setStatus("error");
      setMessage(e instanceof Error ? e.message : "Could not log prediction.");
    }
  }

  return (
    <section className="rounded-[10px] border border-[#BFDBFE] bg-[#F0F4FF] p-5">
      <p className="font-display text-sm font-semibold text-slate-900">
        Before you open the causal chain — what do you think happens next for this event?
      </p>
      <div className="mt-3 flex flex-col gap-2" role="listbox" aria-label="Prediction choices">
        {PREDICTION_OPTIONS.map((opt, i) => (
          <button
            key={opt}
            type="button"
            role="option"
            aria-selected={selected === i}
            onClick={() => {
              setSelected(i);
              setStatus("idle");
              setMessage(null);
            }}
            className={`rounded-lg border px-3 py-2.5 text-left font-mono text-[12px] leading-snug transition-colors ${
              selected === i
                ? "border-finnwise-blue bg-white text-finnwise-blue"
                : "border-slate-200 bg-white/70 text-slate-700 hover:border-finnwise-blue/60"
            }`}
          >
            {opt}
          </button>
        ))}
      </div>
      <button
        type="button"
        disabled={selected === null || !userId || status === "loading" || status === "success"}
        onClick={() => {
          void submit();
        }}
        className="mt-4 inline-flex items-center justify-center rounded-lg bg-finnwise-blue px-4 py-2 font-mono text-[11px] font-semibold uppercase tracking-wide text-white disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        {status === "loading" ? "Logging…" : "Log my prediction →"}
      </button>
      {!userId ? (
        <p className="mt-2 font-mono text-[10px] text-slate-600">
          Set <code className="rounded bg-white px-1">NEXT_PUBLIC_FINNWISE_USER_ID</code> to your auth
          user UUID to enable logging (Phase 1 dev bridge).
        </p>
      ) : null}
      <p className="mt-3 font-mono text-[10px] leading-relaxed text-slate-600">
        This is tracked for your learning. It does not constitute an investment decision. Reviewed in
        The Mirror when the card resolves.
      </p>
      {message ? (
        <p
          className={`mt-2 font-mono text-[11px] ${status === "error" ? "text-finnwise-red" : "text-finnwise-green"}`}
        >
          {message}
        </p>
      ) : null}
    </section>
  );
}
