export const SESSION_ID_COOKIE = "finnwise_session_id";
export const PERSONALISATION_TOKEN_COOKIE = "finnwise_personalisation_token";

const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365;

export type SessionCookiePayload = {
  sessionId?: string | null;
  personalisationToken?: string | null;
};

export type ServerSessionCookies = {
  sessionId: string | null;
  personalisationToken: string | null;
};

/** Cookie options shared by the session sync route. */
export function sessionCookieOptions(): {
  httpOnly: boolean;
  secure: boolean;
  sameSite: "lax";
  path: string;
  maxAge: number;
} {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: ONE_YEAR_SECONDS,
  };
}

/** Mirror localStorage session + holdings token into HTTP-only cookies for SSR. */
export async function syncSessionCookies(payload: SessionCookiePayload): Promise<void> {
  if (typeof window === "undefined") return;
  try {
    await fetch("/api/session/cookies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "same-origin",
    });
  } catch {
    /* non-blocking; SSR falls back to anonymous feed */
  }
}
