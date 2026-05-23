import { NextResponse } from "next/server";

import { resolveSiteOrigin } from "@/lib/auth-redirect";
import { createClient } from "@/lib/supabase/server";

function redirectOrigin(request: Request): string {
  const { origin } = new URL(request.url);
  return (
    resolveSiteOrigin({
      forwardedHost: request.headers.get("x-forwarded-host"),
      forwardedProto: request.headers.get("x-forwarded-proto"),
      windowOrigin: origin,
    }) || origin
  );
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const origin = redirectOrigin(request);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/pulse";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  return NextResponse.redirect(`${origin}/sign-in?error=auth`);
}
