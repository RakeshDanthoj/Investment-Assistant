"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";

export type HoldingIntersection = {
  instrument_id: string;
  holdingDisplayName: string;
  signal_label?: string;
  signal_type?: string;
};

type HoldingCalloutProps = {
  intersections: HoldingIntersection[];
};

function signalText(row: HoldingIntersection): string {
  return row.signal_label || row.signal_type || "assessment";
}

export function HoldingCallout({ intersections }: HoldingCalloutProps) {
  if (!intersections.length) return null;

  return (
    <Alert className="border-finnwise-blue/30 bg-[#EFF6FF]">
      <AlertDescription className="text-sm text-slate-800">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-wide text-finnwise-blue">
          Your holdings
        </p>
        <ul className="mt-2 space-y-2">
          {intersections.map((row) => (
            <li key={row.instrument_id}>
              <span className="font-medium text-slate-900">
                What this means for your {row.holdingDisplayName}
              </span>
              <span className="text-slate-600">
                {" "}
                ({row.instrument_id}) — {signalText(row)} on this card.
              </span>
            </li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  );
}
