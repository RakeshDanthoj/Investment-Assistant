import { NextResponse } from "next/server";

import {
  PERSONALISATION_TOKEN_COOKIE,
  SESSION_ID_COOKIE,
  sessionCookieOptions,
  type SessionCookiePayload,
} from "@/lib/sessionCookies.shared";

export async function POST(request: Request) {
  let body: SessionCookiePayload;
  try {
    body = (await request.json()) as SessionCookiePayload;
  } catch {
    return NextResponse.json({ message: "Invalid JSON body." }, { status: 400 });
  }

  const response = NextResponse.json({ ok: true });
  const options = sessionCookieOptions();

  if (typeof body.sessionId === "string" && body.sessionId.trim()) {
    response.cookies.set(SESSION_ID_COOKIE, body.sessionId.trim(), options);
  }

  if (body.personalisationToken === null) {
    response.cookies.delete(PERSONALISATION_TOKEN_COOKIE);
  } else if (
    typeof body.personalisationToken === "string" &&
    body.personalisationToken.trim()
  ) {
    response.cookies.set(
      PERSONALISATION_TOKEN_COOKIE,
      body.personalisationToken.trim(),
      options,
    );
  }

  return response;
}
