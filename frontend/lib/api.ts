/** Backend origin for browser-side fetch — set NEXT_PUBLIC_API_BASE_URL in `.env.local`. */
export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, "");
  const fallback = "http://127.0.0.1:8000";

  if (typeof window === "undefined") {
    return configured || fallback;
  }

  const host = window.location.hostname;
  const isLocalHost = host === "localhost" || host === "127.0.0.1";

  // Production browsers call same-origin `/backend/...`; `app/backend/[...path]/route.ts` proxies to Render.
  if (configured && !isLocalHost && !isLoopbackUrl(configured)) {
    return "/backend";
  }

  return configured || fallback;
}

/**
 * Backend origin for long-running browser calls (LLM draft/regen, ~30–90s).
 * Bypasses the Vercel `/backend` proxy, which times out before Render responds.
 * Requires FastAPI CORS to allow this site's origin (see `allow_origin_regex` in main.py).
 */
export function getLongRunningApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, "");
  return configured || "http://127.0.0.1:8000";
}

function isLoopbackUrl(url: string): boolean {
  return /\/\/(localhost|127\.0\.0\.1)(:|\/|$)/i.test(url);
}

/** True when the browser bundle still targets loopback outside local dev. */
export function isApiMisconfiguredForProduction(): boolean {
  if (typeof window === "undefined") return false;
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1") return false;

  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  return !configured || isLoopbackUrl(configured);
}

/** Map non-JSON HTTP error bodies (including Next.js HTML 404 pages) to user-facing copy. */
export function describeHttpFailure(
  status: number,
  body: string,
  context = "complete the request",
): string {
  const trimmed = body.trim();
  const looksLikeHtml =
    trimmed.startsWith("<!DOCTYPE") ||
    trimmed.startsWith("<html") ||
    trimmed.includes("<html") ||
    trimmed.includes("next-error-h1");

  if (looksLikeHtml) {
    if (status === 404) {
      return (
        `Could not ${context}. The /backend API proxy returned 404 — confirm ` +
        "NEXT_PUBLIC_API_BASE_URL is set in Vercel and redeploy the frontend."
      );
    }
    return `Could not ${context}. The server returned an HTML error page (${status}).`;
  }

  try {
    const parsed = JSON.parse(trimmed) as { detail?: unknown; message?: unknown };
    if (typeof parsed.detail === "string") return parsed.detail;
    if (typeof parsed.message === "string") return parsed.message;
  } catch {
    // not JSON
  }

  if (trimmed.length > 280) {
    return `Could not ${context}. Request failed (${status}).`;
  }

  return trimmed || `Could not ${context}. Request failed (${status}).`;
}

/**
 * Turn raw fetch failures into actionable copy (network / CORS / misconfigured API URL).
 */
export function describeFetchFailure(error: unknown, context = "reach the server"): string {
  const raw = error instanceof Error ? error.message : String(error);
  const lower = raw.toLowerCase();

  if (isApiMisconfiguredForProduction()) {
    return (
      "The app is not configured for production yet. Set NEXT_PUBLIC_API_BASE_URL in your " +
      "Vercel project to your live API URL (for example your Render service), then redeploy."
    );
  }

  if (lower === "failed to fetch" || lower.includes("networkerror") || lower.includes("load failed")) {
    return (
      `Could not ${context}. Check that the API is running, NEXT_PUBLIC_API_BASE_URL points to it ` +
      "(HTTPS in production), and CORS_ORIGINS on the backend includes this site's origin."
    );
  }

  return raw || "Something went wrong. Please try again.";
}
