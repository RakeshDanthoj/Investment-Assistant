import { NextResponse } from "next/server";

import { createClient } from "@/lib/supabase/server";

export async function GET() {
  const supabase = await createClient();
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    return NextResponse.json({
      id: "anonymous",
      email: null,
    });
  }

  return NextResponse.json({
    id: user.id,
    email: user.email,
  });
}
