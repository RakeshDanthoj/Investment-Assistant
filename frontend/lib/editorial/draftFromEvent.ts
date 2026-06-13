import { describeHttpFailure, getLongRunningApiBaseUrl } from "@/lib/api";

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
    case "event_not_found":
      return "This event was not found. Refresh the queue and try again.";
    case "draft_pipeline_failed":
      return fallback || "Draft generation failed validation. Try another event or check backend logs.";
    default:
      return fallback;
  }
}

export function parseDraftFromEventError(status: number, body: string): string {
  const trimmed = body.trim();
  if (
    trimmed.includes("FUNCTION_INVOCATION_TIMEOUT") ||
    (status === 504 && trimmed.toLowerCase().includes("timeout"))
  ) {
    return (
      "Draft generation timed out in the hosting proxy (usually 10–60s). " +
      "LLM synthesis needs about 30–90 seconds — retry after the frontend redeploys with direct API access."
    );
  }
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

  return describeHttpFailure(status, body, "generate a draft card");
}

export async function requestDraftFromEvent(eventId: string): Promise<DraftFromEventResult> {
  const base = getLongRunningApiBaseUrl().replace(/\/$/, "");
  let response: Response;
  try {
    response = await fetch(`${base}/api/cards/draft-from-event`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_id: eventId, editor_notes: null }),
      cache: "no-store",
    });
  } catch (error) {
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
