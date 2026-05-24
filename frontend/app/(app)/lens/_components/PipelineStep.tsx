import { Check } from "lucide-react";

import type { PipelineStepStatus } from "@/lib/lens/streamTypes";

type PipelineStepProps = {
  index: number;
  label: string;
  status: PipelineStepStatus;
};

export function PipelineStep({ index, label, status }: PipelineStepProps) {
  const isDone = status === "done";
  const isActive = status === "active";

  return (
    <li className="flex items-start gap-3 text-sm">
      <span
        className={[
          "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full font-mono text-[11px] font-medium",
          isDone
            ? "bg-emerald-50 text-emerald-700"
            : isActive
              ? "bg-[#1A4FCC]/10 text-[#1A4FCC] animate-pulse"
              : "bg-muted text-muted-foreground",
        ].join(" ")}
        aria-hidden
      >
        {isDone ? <Check className="h-3.5 w-3.5" strokeWidth={2.5} /> : index + 1}
      </span>
      <span
        className={[
          "pt-0.5",
          isDone
            ? "text-foreground"
            : isActive
              ? "font-medium text-[#1A4FCC]"
              : "text-muted-foreground",
        ].join(" ")}
      >
        {label}
      </span>
    </li>
  );
}
