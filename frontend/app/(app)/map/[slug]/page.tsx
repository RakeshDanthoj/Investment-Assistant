import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { fetchMapSectorSummary } from "@/lib/api/mapServer";
import { createClient } from "@/lib/supabase/server";
import { notFound } from "next/navigation";

import { MapSectorClient } from "../_components/MapSectorClient";

function SectorFallback() {
  return (
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-8">
      <Skeleton className="h-6 w-32" />
      <Skeleton className="h-10 w-64" />
      <Skeleton className="h-40 rounded-lg" />
      <Skeleton className="h-64 rounded-lg" />
    </div>
  );
}

export default async function MapSectorPage({
  params,
}: {
  params: { slug: string };
}) {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    return (
      <main className="p-8">
        <p className="text-[13px] text-slate-600">Sign in to explore The Map.</p>
      </main>
    );
  }

  let summary;
  try {
    summary = await fetchMapSectorSummary(session.access_token, params.slug);
  } catch {
    notFound();
  }

  return (
    <Suspense fallback={<SectorFallback />}>
      <MapSectorClient summary={summary} />
    </Suspense>
  );
}
