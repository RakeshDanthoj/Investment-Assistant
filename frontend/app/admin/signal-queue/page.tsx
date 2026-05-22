import { Suspense } from "react";

import SignalQueueClient from "./SignalQueueClient";

function SignalQueueLoading() {
  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-8 px-4 py-10">
      <h1 className="font-display text-3xl text-slate-900">Loading signal queue…</h1>
    </main>
  );
}

export default function SignalQueuePage() {
  return (
    <Suspense fallback={<SignalQueueLoading />}>
      <SignalQueueClient />
    </Suspense>
  );
}
