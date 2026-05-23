"use client";

import { cn } from "@/lib/utils";

type ResolvedBadgeProps = {
  count: number;
  onClick?: () => void;
};

export function ResolvedBadge({ count, onClick }: ResolvedBadgeProps) {
  if (count < 1) return null;

  const label =
    count === 1
      ? "1 card resolved — ready to grade"
      : `${count} cards resolved — ready to grade`;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-2 rounded-full border border-[#BFDBFE] bg-[#EFF6FF] px-3 py-1.5",
        "text-left transition-colors hover:bg-[#DBEAFE]",
      )}
      aria-label={label}
      data-testid="mirror-resolved-badge"
    >
      <span
        className="thread-signal-pulse inline-block h-2.5 w-2.5 shrink-0 rounded-full bg-[#1A4FCC]"
        data-testid="mirror-resolved-badge-pulse"
      />
      <span className="font-mono text-[10px] font-medium uppercase tracking-wide text-[#1A4FCC]">
        {label}
      </span>
    </button>
  );
}
