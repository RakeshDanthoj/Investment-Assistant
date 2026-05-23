import { NextResponse } from "next/server";

import { getServerApiBaseUrl } from "@/lib/api/server";
import { createClient } from "@/lib/supabase/server";

/** Proxy tester acceptance to the FastAPI backend using the server-side session. */
export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { session },
    error: sessionError,
  } = await supabase.auth.getSession();

  if (sessionError || !session?.access_token) {
    return NextResponse.json(
      { message: "Sign in with your invite link before accepting the briefing." },
      { status: 401 },
    );
  }

  const base = getServerApiBaseUrl().replace(/\/$/, "");
  const forwardedFor = request.headers.get("x-forwarded-for");
  const headers: Record<string, string> = {
    Authorization: `Bearer ${session.access_token}`,
  };
  if (forwardedFor) {
    headers["X-Forwarded-For"] = forwardedFor;
  }

  let backendRes: Response;
  try {
    backendRes = await fetch(`${base}/api/tester/accept`, {
      method: "POST",
      headers,
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      {
        message:
          "Could not reach the API. Confirm the backend is running and NEXT_PUBLIC_API_BASE_URL is set.",
      },
      { status: 503 },
    );
  }

  if (backendRes.status === 409) {
    return NextResponse.json({ ok: true, alreadyAccepted: true });
  }

  const body = await backendRes.text();
  const contentType = backendRes.headers.get("Content-Type") ?? "application/json";

  return new NextResponse(body || null, {
    status: backendRes.status,
    headers: body ? { "Content-Type": contentType } : undefined,
  });
}
