import { type NextRequest } from "next/server";

import { updateSession } from "@/lib/supabase/middleware";

/** Refreshes Supabase session cookies; Phase 1 does not redirect unauthenticated users. */
export async function middleware(request: NextRequest) {
  const { supabaseResponse } = await updateSession(request);
  return supabaseResponse;
}

export const config = {
  matcher: [
    "/pulse",
    "/pulse/:path*",
    "/thread",
    "/thread/:path*",
    "/mirror",
    "/mirror/:path*",
    "/lens",
    "/lens/:path*",
    "/map",
    "/map/:path*",
    "/admin",
    "/admin/:path*",
    "/api/protected/:path*",
  ],
};
