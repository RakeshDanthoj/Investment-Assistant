import { describeHttpFailure, getLongRunningApiBaseUrl } from "@/lib/api";

/** synthesis layers (up to 2) + instruments + dissent + framework — see card_pipeline */
const DRAFT_PIPELINE_LLM_CALLS = 6;

/** Backend fails with llm_timeout slightly before this buffer elapses. */
const DRAFT_TIMEOUT_BUFFER_MS = 45_000;

function perCallTimeoutSeconds(): number {
  const raw = process.env.NEXT_PUBLIC_LLM_REQUEST_TIMEOUT_SECONDS?.trim();
  const parsed = raw ? Number(raw) : 90;
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 90;
}

function maxLlmRetries(): number {
  const raw = process.env.NEXT_PUBLIC_LLM_MAX_RETRIES?.trim();
  const parsed = raw ? Number(raw) : 2;
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 2;
}

/**
 * Browser-side ceiling for the full draft pipeline.
 * Default: per-call timeout × retries × 5 LLM slots + 45s buffer (matches backend deadline).
 * Override with NEXT_PUBLIC_DRAFT_FROM_EVENT_TIMEOUT_MS on Vercel.
 */
export function draftFromEventTimeoutMs(): number {
  const override = process.env.NEXT_PUBLIC_DRAFT_FROM_EVENT_TIMEOUT_MS?.trim();
  if (override) {
    const parsed = Number(override);
    if (Number.isFinite(parsed) && parsed > 0) {
      return parsed;
    }
  }
  return (
    perCallTimeoutSeconds() *
    maxLlmRetries() *
    DRAFT_PIPELINE_LLM_CALLS *
    1000 +
    DRAFT_TIMEOUT_BUFFER_MS
  );
}

export type DraftFromEventResult =
  | { ok: true; cardId: string }
  | { ok: false; message: string };

type FastApiDetailObject = {
  code?: string;
  message?: string;
  unavailable_critical_facts?: string[];
};

function messageForDetailCode(
  code: string,
  fallback: string,
  unavailableCritical?: string[],
): string {
  switch (code) {
    case "critical_facts_held": {
      const ids = (unavailableCritical ?? []).filter((id) => id.trim()).join(", ");
      const unavailableDetail = ids ? ` Unavailable: ${ids}.` : "";
      return (
        "Card drafting is on hold — critical market facts are unavailable." +
        unavailableDetail +
        " Check the market facts banner above and try again when facts recover."
      );
    }
    case "llm_daily_cap":
      return "Daily LLM card limit reached. Try again after the UTC day resets.";
    case "llm_quota_exceeded":
      return (
        "NVIDIA API quota exceeded. Wait about a minute and try again, or check " +
        "credits and rate limits at build.nvidia.com."
      );
    case "llm_provider_error":
      return fallback || "The LLM provider returned an error. Check backend logs and API key.";
    case "llm_monthly_budget":
      return "Monthly LLM budget exceeded. Contact ops before generating more drafts.";
    case "llm_timeout":
      return (
        "Draft generation timed out waiting on the LLM. Switch to a faster model " +
        "(e.g. nvidia/nemotron-3-nano-30b-a3b) or raise LLM_REQUEST_TIMEOUT_SECONDS, then retry."
      );
    case "llm_output_truncated":
      return (
        "Draft generation failed because the model ran out of output tokens before " +
        "finishing structured JSON. Retry once; if it persists, use " +
        "nvidia/nemotron-3-nano-30b-a3b or raise LLM_SYNTHESIS_LAYERS_MAX_TOKENS " +
        "and LLM_SYNTHESIS_INSTRUMENTS_MAX_TOKENS on the backend."
      );
    case "event_not_found":
      return "This event was not found. Refresh the queue and try again.";
    case "draft_pipeline_failed":
      if (/quantitative sentence missing/i.test(fallback)) {
        return (
          "Draft generation failed: a quantitative sentence is missing an editorial " +
          "[MEASURED], [MODELLED], or [JUDGED] tag. Retry generation; if it persists, " +
          "check backend logs."
        );
      }
      return fallback || "Draft generation failed validation. Try another event or check backend logs.";
    default:
      return fallback;
  }
}

export function parseDraftFromEventError(status: number, body: string): string {
  const trimmed = body.trim();
  try {
    const parsed = JSON.parse(trimmed) as { detail?: unknown };
    const detail = parsed.detail;
    if (typeof detail === "object" && detail !== null) {
      const obj = detail as FastApiDetailObject;
      const message =
        typeof obj.message === "string" && obj.message.trim()
          ? obj.message.trim()
          : "Draft generation failed.";
      if (typeof obj.code === "string") {
        const unavailable =
          Array.isArray(obj.unavailable_critical_facts) &&
          obj.unavailable_critical_facts.every((id) => typeof id === "string")
            ? obj.unavailable_critical_facts
            : undefined;
        return messageForDetailCode(obj.code, message, unavailable);
      }
      return message;
    }
    if (typeof detail === "string" && detail.trim()) {
      return detail.trim();
    }
  } catch {
    // fall through to generic HTTP helper
  }

  if (
    trimmed.includes("FUNCTION_INVOCATION_TIMEOUT") ||
    (status === 504 && trimmed.toLowerCase().includes("timeout"))
  ) {
    return (
      "Draft generation timed out in the hosting proxy (usually 10–60s). " +
      "LLM synthesis needs about 30–90 seconds — retry after the frontend redeploys with direct API access."
    );
  }

  return describeHttpFailure(status, body, "generate a draft card");
}

export async function requestDraftFromEvent(eventId: string): Promise<DraftFromEventResult> {
  const base = getLongRunningApiBaseUrl().replace(/\/$/, "");
  const timeoutMs = draftFromEventTimeoutMs();
  let response: Response;
  try {
    response = await fetch(`${base}/api/cards/draft-from-event`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_id: eventId, editor_notes: null }),
      cache: "no-store",
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError") {
      const minutes = Math.round(timeoutMs / 60_000);
      return {
        ok: false,
        message:
          `Draft generation timed out in the browser after about ${minutes} minutes. ` +
          "The backend may still be running on an older deploy — restart it and confirm " +
          "LLM_REQUEST_TIMEOUT_SECONDS / LLM_MAX_RETRIES are set. " +
          "A current backend returns llm_timeout (504) before this browser limit.",
      };
    }
    const message =
      error instanceof Error ? error.message : "Could not reach the server to generate a draft.";
    return { ok: false, message };
  }

  const body = await response.text().catch(() => "");
  if (!response.ok) {
    return { ok: false, message: parseDraftFromEventError(response.status, body) };
  }

  try {
    const parsed = JSON.parse(body) as { card_id?: string };
    if (typeof parsed.card_id === "string" && parsed.card_id.trim()) {
      return { ok: true, cardId: parsed.card_id };
    }
  } catch {
    // fall through
  }

  return { ok: false, message: "Draft generation succeeded but the response was invalid." };
}
