import { Suspense } from "react";

import PulseClient from "./_components/PulseClient";

function PulseFallback() {
  return (
    <div className="flex flex-1 flex-col">
      <div className="border-b border-slate-200 bg-white px-4 py-4">
        <div className="h-7 w-40 animate-pulse rounded bg-slate-200" />
      </div>
      <div className="mx-auto mt-6 w-full max-w-6xl space-y-4 px-4">
        <div className="h-40 animate-pulse rounded-lg bg-slate-200/80" />
        <div className="h-40 animate-pulse rounded-lg bg-slate-200/80" />
      </div>
    </div>
  );
}

export default function PulsePage() {
  return (
    <Suspense fallback={<PulseFallback />}>
      <PulseClient />
    </Suspense>
  );
}
