import { NextResponse } from "next/server";

import { isAuthSkipped } from "@/lib/env";
import { createClient } from "@/lib/supabase/server";

export async function GET() {
  if (isAuthSkipped()) {
    return NextResponse.json({
      id: "local-dev-placeholder",
      email: "dev@local",
    });
  }

  const supabase = await createClient();
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  return NextResponse.json({
    id: user.id,
    email: user.email,
  });
}
