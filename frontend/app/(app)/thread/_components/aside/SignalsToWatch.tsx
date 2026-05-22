"use client";

import { useState } from "react";

import { Card, CardContent } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { InstrumentDetail, SignalRow } from "@/lib/cards/threadTypes";

type SignalsToWatchProps = {
  signals: SignalRow[];
  instruments: InstrumentDetail[];
};

function dotClass(state: string, pulse: boolean): string {
  const s = state.toLowerCase();
  if (s === "triggered")
    return pulse ? "bg-amber-500 thread-signal-pulse" : "bg-amber-500";
  if (s === "resolved") return "bg-emerald-500";
  return "bg-slate-300";
}

export function SignalsToWatch({ signals, instruments }: SignalsToWatchProps) {
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  if (!signals.length) {
    return (
      <Card className="w-full min-w-0 rounded-[10px] py-0 shadow-none ring-slate-200" size="sm">
        <CardContent className="p-4">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
            Signals to watch
          </p>
          <p className="mt-3 text-[12px] text-slate-600">No monitored signals on this card yet.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full min-w-0 rounded-[10px] py-0 shadow-none ring-slate-200" size="sm">
      <CardContent className="p-4">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
          Signals to watch
        </p>
        <ul className="mt-3 space-y-2">
          {signals.map((sig, idx) => {
            const pulse = sig.state.toLowerCase() === "triggered";
            return (
              <li key={`${sig.signal_text}-${idx}`} className="border-b border-slate-100 pb-2 last:border-0">
                <Collapsible
                  open={openIdx === idx}
                  onOpenChange={(open) => {
                    setOpenIdx(open ? idx : null);
                  }}
                >
                  <CollapsibleTrigger className="flex w-full min-w-0 gap-2 text-left">
                    <span
                      className={`mt-1 h-2 w-2 shrink-0 rounded-full ${dotClass(sig.state, pulse)}`}
                      aria-hidden
                    />
                    <span className="min-w-0 flex-1 font-mono text-[12px] leading-snug break-words text-slate-700">
                      {sig.signal_text}
                    </span>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <div className="mt-2 rounded-lg bg-slate-50 p-3 font-mono text-[10px] leading-relaxed text-slate-700">
                      <p className="font-semibold uppercase tracking-wide text-slate-500">
                        Consequence map
                      </p>
                      <ul className="mt-2 list-disc space-y-1 pl-4">
                        {instruments.length ? (
                          instruments.map((i) => (
                            <li key={i.instrument_id}>
                              <span className="font-semibold">{i.instrument_id}</span> — {i.signal_label}: if
                              this signal fires, revisit entry conditions vs. this narrative before adjusting
                              exposure.
                            </li>
                          ))
                        ) : (
                          <li>Instrument assessments will map here as this card fills out.</li>
                        )}
                      </ul>
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              </li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}
