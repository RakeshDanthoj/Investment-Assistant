"use client";

import { useReducer } from "react";

import { SebiFooter } from "@/components/SebiFooter";
import { describeFetchFailure, getApiBaseUrl } from "@/lib/api";
import {
  initialOnboardingState,
  onboardingReducer,
  type InvestmentStatus,
} from "@/lib/onboarding/state";

import { BrandPanel } from "./_components/BrandPanel";
import { ProgressDots } from "./_components/ProgressDots";
import { Step1Status } from "./_components/Step1Status";
import { Step2Amount } from "./_components/Step2Amount";
import { Step3Horizon } from "./_components/Step3Horizon";
import { Step4ModeResult } from "./_components/Step4ModeResult";

function statusSummary(status: InvestmentStatus): string {
  switch (status) {
    case "starting_fresh":
      return "Starting fresh";
    case "has_investments":
      return "Already investing";
    default:
      return "Just exploring";
  }
}

function SubmitBlockingDots() {
  return (
    <div className="flex justify-center gap-1 py-4" aria-busy aria-label="Saving profile">
      <span className="h-2 w-2 animate-pulse rounded-full bg-finnwise-blue" />
      <span className="h-2 w-2 animate-pulse rounded-full bg-finnwise-blue [animation-delay:150ms]" />
      <span className="h-2 w-2 animate-pulse rounded-full bg-finnwise-blue [animation-delay:300ms]" />
    </div>
  );
}

export default function OnboardingPage() {
  const [state, dispatch] = useReducer(onboardingReducer, null, initialOnboardingState);

  const stepLabel =
    state.step === 4 ? "done" : `step ${state.step} of 3`;

  async function submitSession() {
    if (!state.investmentStatus || !state.horizon) return;
    dispatch({ type: "SUBMIT_SESSION_START" });
    try {
      const base = getApiBaseUrl();
      const amountNum = state.amountInput ? Number(state.amountInput) : undefined;
      const res = await fetch(`${base}/onboarding/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          investment_status: state.investmentStatus,
          horizon: state.horizon,
          cadence: state.cadence,
          session_id: state.sessionId,
          amount_rupees: amountNum !== undefined && !Number.isNaN(amountNum) ? amountNum : null,
        }),
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || `Request failed (${res.status})`);
      }
      const data = (await res.json()) as {
        mode: string;
        starting_surface: string;
        rationale: string;
        session_id: string;
        amount_echo: number | null;
      };
      dispatch({
        type: "SUBMIT_SESSION_SUCCESS",
        result: {
          mode: data.mode,
          starting_surface: data.starting_surface,
          rationale: data.rationale,
          session_id: data.session_id,
          amount_echo: data.amount_echo,
        },
      });
    } catch (e) {
      dispatch({
        type: "SUBMIT_SESSION_ERROR",
        message: describeFetchFailure(e, "save your profile"),
      });
    }
  }

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <BrandPanel />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col bg-finnwise-surface">
        <div className="flex min-h-0 flex-1 flex-col px-4 py-8 pb-0 sm:px-8">
          <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-baseline gap-2 lg:hidden">
              <p className="font-display text-lg text-slate-900">
                finn<span className="text-finnwise-blue">wise</span>
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="font-mono text-xs lowercase tracking-wide text-slate-400">
                {stepLabel}
              </span>
              <ProgressDots flowStep={state.step} />
            </div>
          </header>

          <main className="mx-auto flex w-full max-w-xl flex-1 flex-col justify-center pb-6">
            {state.step === 1 && (
              <section className="flex flex-col gap-6" aria-labelledby="s1-title">
                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
                  <p className="text-sm text-slate-800">Welcome. Before we begin, one quick question —</p>
                  <p id="s1-title" className="mt-2 text-lg font-medium text-slate-900">
                    Do you already have investments, or are you starting fresh?
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    There&apos;s no right answer. This just helps us personalise what you see.
                  </p>
                </div>
                <Step1Status
                  selected={state.investmentStatus}
                  onSelect={(status) => dispatch({ type: "SELECT_STATUS", status })}
                />
                <button
                  type="button"
                  disabled={!state.investmentStatus}
                  onClick={() => dispatch({ type: "ADVANCE_FROM_STEP1" })}
                  className="self-start rounded-lg bg-[#185FA5] px-6 py-3 text-sm font-medium text-[#E6F1FB] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Continue →
                </button>
              </section>
            )}

            {state.step === 2 && state.investmentStatus && (
              <section className="flex flex-col gap-6">
                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
                  <div className="mb-3 flex justify-end">
                    <div className="max-w-[85%] rounded-2xl bg-finnwise-blue-tint px-4 py-2.5 text-left">
                      <p className="text-sm text-slate-800">{statusSummary(state.investmentStatus)}</p>
                    </div>
                  </div>
                  <p className="text-sm text-slate-800">Good to know. Now —</p>
                  <p className="mt-2 text-lg font-medium text-slate-900">
                    How much are you thinking of putting in?
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    Rough numbers are fine. This amount stays in your session only.
                  </p>
                </div>
                <Step2Amount
                  amountDigits={state.amountInput}
                  cadence={state.cadence}
                  onAmountChange={(raw) => dispatch({ type: "SET_AMOUNT", raw })}
                  onCadenceChange={(cadence) => dispatch({ type: "SET_CADENCE", cadence })}
                />
                <button
                  type="button"
                  onClick={() => dispatch({ type: "ADVANCE_FROM_STEP2" })}
                  className="self-start rounded-lg bg-[#185FA5] px-6 py-3 text-sm font-medium text-[#E6F1FB]"
                >
                  Continue →
                </button>
              </section>
            )}

            {state.step === 3 && state.investmentStatus && (
              <section className="flex flex-col gap-6">
                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
                  <div className="mb-3 flex justify-end">
                    <div className="max-w-[85%] rounded-2xl bg-finnwise-blue-tint px-4 py-2.5 text-left">
                      <p className="text-sm text-slate-800">
                        ₹
                        {state.amountInput.replace(/\B(?=(\d{3})+(?!\d))/g, ",") || "0"}{" "}
                        {state.cadence === "monthly" ? "/ month" : "one-time"}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-slate-800">Last one —</p>
                  <p className="mt-2 text-lg font-medium text-slate-900">
                    How long are you thinking of staying invested?
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    This shapes which surface we open first — you&apos;ll always see the full product
                    inside.
                  </p>
                </div>

                <Step3Horizon
                  selected={state.horizon}
                  onSelect={(horizon) => dispatch({ type: "SELECT_HORIZON", horizon })}
                />

                {state.submitState === "loading" && <SubmitBlockingDots />}

                {state.submitState === "error" && state.apiError && (
                  <p
                    role="alert"
                    className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
                  >
                    {state.apiError}
                  </p>
                )}

                <button
                  type="button"
                  disabled={!state.horizon || state.submitState === "loading"}
                  onClick={() => void submitSession()}
                  className="self-start rounded-lg bg-[#185FA5] px-6 py-3 text-sm font-medium text-[#E6F1FB] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Take me in →
                </button>
              </section>
            )}

            {state.step === 4 && state.apiResult && (
              <Step4ModeResult result={state.apiResult} />
            )}
          </main>
        </div>

        <SebiFooter />
      </div>
    </div>
  );
}
