import { fetchMirrorInitialData } from "@/lib/api/mirrorServer";
import { createClient } from "@/lib/supabase/server";

import MirrorClient from "./_components/MirrorClient";
import { MirrorSignInRequired } from "./_components/MirrorSignInRequired";

type MirrorContentSectionProps = {
  statusFilter: string | null;
};

/** Async RSC boundary: streams Mirror payload after shell HTML (P2.5-S3 / PC-2.1). */
export async function MirrorContentSection({ statusFilter }: MirrorContentSectionProps) {
  let initialPayload = null;
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    return <MirrorSignInRequired statusFilter={statusFilter} />;
  }

  try {
    initialPayload = await fetchMirrorInitialData(session.access_token, statusFilter);
  } catch {
    initialPayload = null;
  }

  return (
    <MirrorClient initialPayload={initialPayload} initialStatusFilter={statusFilter} />
  );
}
