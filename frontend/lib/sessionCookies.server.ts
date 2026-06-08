import "server-only";

import { cookies } from "next/headers";

import {
  PERSONALISATION_TOKEN_COOKIE,
  SESSION_ID_COOKIE,
  type ServerSessionCookies,
} from "@/lib/sessionCookies.shared";

export type { ServerSessionCookies };

/** Read session cookies during RSC / route handlers. */
export async function getServerSessionCookies(): Promise<ServerSessionCookies> {
  const store = await cookies();
  return {
    sessionId: store.get(SESSION_ID_COOKIE)?.value ?? null,
    personalisationToken: store.get(PERSONALISATION_TOKEN_COOKIE)?.value ?? null,
  };
}
