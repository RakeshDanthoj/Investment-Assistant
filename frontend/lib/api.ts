/** Backend origin for browser-side fetch — set NEXT_PUBLIC_API_BASE_URL in `.env.local`. */
export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim().replace(/\/$/, "");
  const fallback = "http://127.0.0.1:8000";

  if (typeof window === "undefined") {
    return configured || fallback;
  }

  const host = window.location.hostname;
  const isLocalHost = host === "localhost" || host === "127.0.0.1";

  if (configured && !isLocalHost && !isLoopbackUrl(configured)) {
    return "/backend";
  }

  return configured || fallback;
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
