"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { LifecycleStep } from "@/lib/cards/threadTypes";

type LifecycleTrackerProps = {
  steps: LifecycleStep[];
  pulseActive: boolean;
};

export function LifecycleTracker({ steps, pulseActive }: LifecycleTrackerProps) {
  return (
    <Card className="w-full min-w-0 rounded-[10px] py-0 shadow-none ring-slate-200" size="sm">
      <CardContent className="p-4">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
          Lifecycle
        </p>
        <ol className="mt-4 space-y-3">
          {steps.map((s) => (
            <li key={s.slug} className="flex items-start gap-3">
              <span className="relative mt-0.5 flex h-3 w-3 shrink-0 items-center justify-center">
                {s.status === "done" ? (
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" aria-hidden />
                ) : s.status === "current" ? (
                  <span
                    className={`h-2.5 w-2.5 rounded-full bg-finnwise-blue ${pulseActive ? "thread-lifecycle-pulse" : ""}`}
                    aria-hidden
                  />
                ) : (
                  <span className="h-2.5 w-2.5 rounded-full bg-slate-200" aria-hidden />
                )}
              </span>
              <div className="flex-1">
                <p className="font-mono text-[12px] leading-tight text-slate-800">{s.label}</p>
                {s.status === "current" ? (
                  <Badge variant="secondary" className="mt-0.5 font-mono text-[10px] text-finnwise-blue">
                    Current stage
                  </Badge>
                ) : null}
              </div>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}
