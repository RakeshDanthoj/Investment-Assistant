import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { fetchMirrorInitialData } from "@/lib/api/mirrorServer";
import { createClient } from "@/lib/supabase/server";

import MirrorClient from "./_components/MirrorClient";

function MirrorFallback() {
  return (
    <div className="flex flex-1 flex-col">
      <div className="border-b border-border px-4 py-4">
        <Skeleton className="h-7 w-40" />
      </div>
      <div className="mx-auto mt-6 w-full max-w-6xl space-y-4 px-4">
        <Skeleton className="h-24 rounded-lg" />
        <Skeleton className="h-40 rounded-lg" />
      </div>
    </div>
  );
}

function statusFilterFromSearchParams(statusParam?: string): string | null {
  if (!statusParam || statusParam === "all") return null;
  return statusParam;
}

export default async function MirrorPage({
  searchParams,
}: {
  searchParams?: { status?: string };
}) {
  const statusFilter = statusFilterFromSearchParams(searchParams?.status);

  let initialPayload = null;
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session?.access_token) {
    try {
      initialPayload = await fetchMirrorInitialData(session.access_token, statusFilter);
    } catch {
      initialPayload = null;
    }
  }

  return (
    <Suspense fallback={<MirrorFallback />}>
      <MirrorClient initialPayload={initialPayload} initialStatusFilter={statusFilter} />
    </Suspense>
  );
}
