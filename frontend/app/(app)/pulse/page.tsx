import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { fetchPulseFeed } from "@/lib/api/server";

import PulseClient from "./_components/PulseClient";

function PulseFallback() {
  return (
    <div className="flex flex-1 flex-col">
      <div className="border-b border-border bg-background px-4 py-4">
        <Skeleton className="h-7 w-40" />
      </div>
      <div className="mx-auto mt-6 w-full max-w-6xl space-y-4 px-4">
        <Skeleton className="h-40 rounded-lg" />
        <Skeleton className="h-40 rounded-lg" />
      </div>
    </div>
  );
}

function categoryQueryFromSearchParams(categoryParam?: string): string {
  if (!categoryParam) return "";
  return categoryParam
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
    .sort()
    .join(",");
}

export default async function PulsePage({
  searchParams,
}: {
  searchParams?: { category?: string };
}) {
  const categoryQuery = categoryQueryFromSearchParams(searchParams?.category);

  let initialData = null;
  try {
    initialData = await fetchPulseFeed(
      categoryQuery ? { category: categoryQuery } : undefined,
    );
  } catch {
    initialData = null;
  }

  return (
    <Suspense fallback={<PulseFallback />}>
      <PulseClient initialData={initialData} initialCategoryQuery={categoryQuery} />
    </Suspense>
  );
}
