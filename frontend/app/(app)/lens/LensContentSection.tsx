import { createClient } from "@/lib/supabase/server";

import LensClient from "./_components/LensClient";

/** Async RSC boundary: static Lens shell streams before client hydration (P2.5-S4 / P2.5-S5). */
export async function LensContentSection() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return <LensClient signedIn={Boolean(session?.access_token)} />;
}
