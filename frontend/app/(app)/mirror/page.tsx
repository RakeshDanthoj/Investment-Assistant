import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";

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

export default function MirrorPage() {
  return (
    <Suspense fallback={<MirrorFallback />}>
      <MirrorClient />
    </Suspense>
  );
}
