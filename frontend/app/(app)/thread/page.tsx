import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function ThreadPlaceholderPage() {
  return (
    <main className="mx-auto flex min-h-full max-w-2xl flex-col justify-center p-8">
      <Card className="py-0 shadow-none">
        <CardContent className="space-y-4 p-8 text-center">
          <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-slate-400">The Thread</p>
          <h1 className="font-display text-2xl font-bold text-slate-900">Open a card to read the full analysis</h1>
          <p className="text-sm leading-relaxed text-slate-500">
            The Thread is the deep-dive view for a single Event Intelligence Card — Insight, Context,
            and Evidence layers with instruments, dissent, and lifecycle tracking.
          </p>
          <p className="text-sm text-slate-500">
            Select a card on <strong className="font-medium text-slate-700">The Pulse</strong> to open
            its Thread, or use &ldquo;Read full analysis&rdquo; from the insight panel.
          </p>
          <Button asChild className="mt-2">
            <Link href="/pulse">Go to The Pulse</Link>
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
