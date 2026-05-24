import { redirect } from "next/navigation";
import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { fetchMapSectorList } from "@/lib/api/mapServer";
import { getServerApiBaseUrl } from "@/lib/api/server";
import type { MapModule } from "@/lib/map/types";
import { createClient } from "@/lib/supabase/server";

import { MapIndexClient } from "./_components/MapIndexClient";

function MapFallback() {
  return (
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-8">
      <Skeleton className="h-8 w-48" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-[140px] rounded-xl" />
        ))}
      </div>
    </div>
  );
}

async function fetchHighlightedModule(
  accessToken: string,
  moduleId: string,
): Promise<MapModule | null> {
  const endpoint = `${getServerApiBaseUrl()}/api/map/modules/${encodeURIComponent(moduleId)}`;
  const response = await fetch(endpoint, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });
  if (!response.ok) {
    return null;
  }
  return (await response.json()) as MapModule;
}

export default async function MapPage({
  searchParams,
}: {
  searchParams?: { module?: string };
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

  let sectors = [];
  let highlightedModule: MapModule | null = null;
  const moduleId = searchParams?.module?.trim();

  try {
    const list = await fetchMapSectorList(session.access_token);
    sectors = list.sectors;
    if (moduleId) {
      highlightedModule = await fetchHighlightedModule(session.access_token, moduleId);
      if (highlightedModule?.sector_slug) {
        redirect(`/map/${highlightedModule.sector_slug}?module=${moduleId}`);
      }
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : "Could not load The Map.";
    return (
      <main className="p-8">
        <p className="text-[13px] text-rose-700">{message}</p>
      </main>
    );
  }

  return (
    <Suspense fallback={<MapFallback />}>
      <MapIndexClient sectors={sectors} highlightedModule={highlightedModule} />
    </Suspense>
  );
}
