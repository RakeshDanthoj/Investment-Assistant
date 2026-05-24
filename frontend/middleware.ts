import { type NextRequest, NextResponse } from "next/server";

import {
  pathRequiresTesterAcceptance,
  shouldRedirectToTesterBriefing,
  TESTER_BRIEFING_PATH,
} from "@/lib/tester-gate";
import { updateSession } from "@/lib/supabase/middleware";

/** Refreshes Supabase session cookies; invited users must accept tester briefing. */
export async function middleware(request: NextRequest) {
  const { supabaseResponse, user, supabase } = await updateSession(request);
  const pathname = request.nextUrl.pathname;

  if (user && pathRequiresTesterAcceptance(pathname)) {
    const { data } = await supabase
      .from("tester_acceptances")
      .select("user_id")
      .eq("user_id", user.id)
      .maybeSingle();

    const hasAccepted = Boolean(data);
    if (
      shouldRedirectToTesterBriefing(pathname, true, hasAccepted) &&
      pathname !== TESTER_BRIEFING_PATH
    ) {
      const url = request.nextUrl.clone();
      url.pathname = TESTER_BRIEFING_PATH;
      return NextResponse.redirect(url);
    }
  }

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
    "/account",
    "/account/:path*",
    "/admin",
    "/admin/:path*",
    "/tester-briefing",
    "/tester-briefing/:path*",
    "/api/protected/:path*",
  ],
};
