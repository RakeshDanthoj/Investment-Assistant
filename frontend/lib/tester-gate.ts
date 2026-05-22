/** Pure gate helpers for tester briefing middleware (P1-S14). */

export const TESTER_BRIEFING_PATH = "/tester-briefing";

const EXEMPT_PREFIXES = [
  "/onboarding",
  "/sign-in",
  "/callback",
  TESTER_BRIEFING_PATH,
] as const;

/** App routes that require acceptance when the user is signed in. */
export function pathRequiresTesterAcceptance(pathname: string): boolean {
  if (pathname === "/") return false;
  if (EXEMPT_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))) {
    return false;
  }
  const gatedPrefixes = [
    "/pulse",
    "/thread",
    "/mirror",
    "/lens",
    "/map",
    "/admin",
    "/api/protected",
  ];
  return gatedPrefixes.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function shouldRedirectToTesterBriefing(
  pathname: string,
  hasUser: boolean,
  hasAccepted: boolean,
): boolean {
  if (!hasUser || hasAccepted) return false;
  return pathRequiresTesterAcceptance(pathname);
}
