import { fetchLensHistory } from "@/lib/api/lensServer";
import { createClient } from "@/lib/supabase/server";
import type { LensQueryItem } from "@/lib/lens/types";

import LensClient from "./_components/LensClient";

/** Async RSC boundary: SSR Lens history before client hydration (PI-S3 / P2.5-S4). */
export async function LensContentSection() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const signedIn = Boolean(session?.access_token);
  let initialHistory: LensQueryItem[] | null = null;

  if (signedIn && session?.access_token) {
    try {
      const payload = await fetchLensHistory(session.access_token);
      initialHistory = payload.items;
    } catch {
      initialHistory = null;
    }
  }

  return <LensClient signedIn={signedIn} initialHistory={initialHistory} />;
}
