import { Suspense } from "react";

import { Skeleton } from "@/components/ui/skeleton";

import { LensContentSection } from "./LensContentSection";
import { LensTopbar } from "./_components/LensTopbar";

function LensBodyFallback() {
  return (
    <div className="mx-auto w-full max-w-[680px] flex-1 space-y-4 px-4 py-6">
      <Skeleton className="h-32 rounded-lg" />
      <Skeleton className="h-24 rounded-lg" />
    </div>
  );
}

/** SSR static shell (topbar) paints before client hydrates Lens body (P2.5-S4 / P2.5-S5). */
export default function LensPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <LensTopbar />
      <Suspense fallback={<LensBodyFallback />}>
        <LensContentSection />
      </Suspense>
    </div>
  );
}
