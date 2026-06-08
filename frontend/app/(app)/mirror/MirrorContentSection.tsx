import { fetchMirrorInitialData } from "@/lib/api/mirrorServer";
import { createClient } from "@/lib/supabase/server";

import MirrorClient from "./_components/MirrorClient";

type MirrorContentSectionProps = {
  statusFilter: string | null;
};

/** Async RSC boundary: streams Mirror payload after shell HTML (P2.5-S3 / PC-2.1). */
export async function MirrorContentSection({ statusFilter }: MirrorContentSectionProps) {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const signedIn = Boolean(session?.access_token);
  let initialPayload = null;

  if (signedIn && session?.access_token) {
    try {
      initialPayload = await fetchMirrorInitialData(session.access_token, statusFilter);
    } catch {
      initialPayload = null;
    }
  }

  return (
    <MirrorClient
      signedIn={signedIn}
      initialPayload={initialPayload}
      initialStatusFilter={statusFilter}
    />
  );
}
