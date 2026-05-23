import { Badge } from "@/components/ui/badge";

/** Purple Phase 2 pill for The Lens topbar (PRD §5 Screen 5). */
export function PhaseBadge() {
  return (
    <Badge
      variant="phase2"
      className="shrink-0 px-2 py-0.5 text-[10px]"
      aria-label="Phase 2 feature"
    >
      Phase 2
    </Badge>
  );
}
