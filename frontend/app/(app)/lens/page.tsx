import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";

import LensClient from "./_components/LensClient";

function LensFallback() {
  return (
    <div className="flex flex-1 flex-col">
      <div className="border-b border-border px-4 py-4">
        <Skeleton className="h-7 w-32" />
      </div>
      <div className="mx-auto mt-6 w-full max-w-[680px] space-y-4 px-4">
        <Skeleton className="h-40 rounded-lg" />
        <Skeleton className="h-24 rounded-lg" />
      </div>
    </div>
  );
}

export default function LensPage() {
  return (
    <Suspense fallback={<LensFallback />}>
      <LensClient />
    </Suspense>
  );
}
