import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { categoryLabel, categoryPillClass } from "@/lib/cards/categories";
import type { PulseCard } from "@/lib/cards/pulseTypes";
import { cn } from "@/lib/utils";

function dotClass(tier: string): string {
  if (tier === "high") return "bg-finnwise-blue";
  if (tier === "moderate") return "bg-finnwise-amber";
  return "bg-slate-300";
}

function chipClass(signalType: string): string {
  const s = signalType.toLowerCase();
  if (s.includes("headwind")) return "bg-[#FEE2E2] text-finnwise-red";
  if (s.includes("opportunity")) return "bg-finnwise-modelled-bg text-finnwise-green";
  return "bg-finnwise-judged-bg text-finnwise-amber";
}

function categoryBadgeVariant(
  category: string,
): "measured" | "modelled" | "judged" | "outline" {
  switch (category) {
    case "macro":
      return "measured";
    case "rbi_policy":
      return "modelled";
    case "regulatory":
      return "judged";
    default:
      return "outline";
  }
}

export type EventCardSurfaceProps = {
  card: PulseCard;
  selected?: boolean;
  className?: string;
};

/** Presentational event card markup — safe for Server Components. */
export function EventCardSurface({ card, selected = false, className }: EventCardSurfaceProps) {
  const resolved = card.lifecycle_state === "resolved";
  const badgeVariant = categoryBadgeVariant(card.category);

  return (
    <Card
      className={cn(
        "w-full gap-0 rounded-lg border border-border bg-background py-0 text-left shadow-none ring-0 [content-visibility:auto] [contain-intrinsic-size:152px]",
        selected
          ? "border-l-[3px] border-l-finnwise-blue bg-finnwise-blue-tint/50 shadow-sm"
          : "border-l-[3px] border-l-transparent",
        className,
      )}
    >
      <CardContent className="p-4">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <Badge
            variant={badgeVariant}
            className={cn(
              "rounded px-2 py-0.5 font-mono text-[9px] font-medium uppercase tracking-wide",
              badgeVariant === "outline" && cn("border-0", categoryPillClass(card.category)),
            )}
          >
            {categoryLabel(card.category)}
          </Badge>
          {resolved ? (
            <Badge
              variant="modelled"
              className="rounded-full px-2 py-0.5 font-mono text-[9px] font-medium uppercase tracking-wide"
            >
              Resolved
            </Badge>
          ) : null}
        </div>
        <h2 className="font-display text-[15px] font-bold leading-snug text-foreground">
          {card.headline}
        </h2>
        <p className="mt-2 text-xs italic leading-relaxed text-muted-foreground">
          {card.event_context}
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9px] uppercase tracking-wide text-muted-foreground">
              Direction
            </span>
            <span className="flex items-center gap-1.5 font-mono text-[9px] text-foreground/80">
              <span
                className={`inline-block h-2 w-2 shrink-0 rounded-full ${dotClass(card.direction_confidence.tier)}`}
                aria-hidden
              />
              {card.direction_confidence.label}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9px] uppercase tracking-wide text-muted-foreground">
              Magnitude
            </span>
            <span className="flex items-center gap-1.5 font-mono text-[9px] text-foreground/80">
              <span
                className={`inline-block h-2 w-2 shrink-0 rounded-full ${dotClass(card.magnitude_confidence.tier)}`}
                aria-hidden
              />
              {card.magnitude_confidence.label}
            </span>
          </div>
        </div>
        {card.instruments?.length ? (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {card.instruments.slice(0, 4).map((i) => (
              <Badge
                key={`${card.id}-${i.instrument_id}`}
                variant="outline"
                className={cn(
                  "rounded border-0 px-2 py-0.5 font-mono text-[9px] font-normal normal-case tracking-normal",
                  chipClass(i.signal_type),
                )}
              >
                {i.instrument_id}
              </Badge>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
