import { Badge } from "@/components/ui/badge";

/** Always-visible Phase 1 tester pill — cannot be dismissed (P1-S14). */
export function PhaseBadge() {
  return (
    <Badge
      variant="outline"
      className="shrink-0 border-[#BFDBFE] bg-[#EFF6FF] font-mono text-[9px] uppercase tracking-wide text-[#1D4ED8]"
      aria-label="Phase 1 tester build"
    >
      Phase 1 tester
    </Badge>
  );
}
