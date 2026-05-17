import { type NextRequest, NextResponse } from "next/server";

import { isAuthSkipped } from "@/lib/env";
import { updateSession } from "@/lib/supabase/middleware";

const PROTECTED_PREFIXES = [
  "/pulse",
  "/thread",
  "/mirror",
  "/lens",
  "/map",
] as const;
const PROTECTED_API_PREFIX = "/api/protected";

function isProtectedPath(pathname: string): boolean {
  if (pathname.startsWith(PROTECTED_API_PREFIX)) return true;
  return PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export async function middleware(request: NextRequest) {
  const { supabaseResponse, user } = await updateSession(request);

  if (
    !isAuthSkipped() &&
    isProtectedPath(request.nextUrl.pathname) &&
    !user
  ) {
    const url = request.nextUrl.clone();
    url.pathname = "/sign-in";
    url.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(url);
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
    "/api/protected/:path*",
  ],
};
