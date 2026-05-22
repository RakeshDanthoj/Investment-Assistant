"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { PulseCard } from "@/lib/cards/pulseTypes";
import { categoryLabel, categoryPillClass } from "@/lib/cards/categories";
import { cn } from "@/lib/utils";

function dotClass(tier: string): string {
  if (tier === "high") return "bg-finnwise-blue";
  if (tier === "moderate") return "bg-finnwise-amber";
  return "bg-slate-300";
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

function formatTime(iso: string | null): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

type InsightPanelProps = {
  card: PulseCard | null;
};

export function InsightPanel({ card }: InsightPanelProps) {
  if (!card) {
    return (
      <aside className="hidden min-h-[200px] border-l border-border bg-background p-6 min-[860px]:block">
        <p className="text-sm text-muted-foreground">Select an event to preview analysis.</p>
      </aside>
    );
  }

  const badgeVariant = categoryBadgeVariant(card.category);

  return (
    <aside className="sticky top-14 hidden h-[calc(100vh-3.5rem)] overflow-y-auto border-l border-border bg-background p-6 min-[860px]:block">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Badge
          variant={badgeVariant}
          className={cn(
            "rounded px-2 py-0.5 font-mono text-[9px] font-medium uppercase tracking-wide",
            badgeVariant === "outline" && cn("border-0", categoryPillClass(card.category)),
          )}
        >
          {categoryLabel(card.category)}
        </Badge>
      </div>
      <h2 className="font-display text-xl font-semibold leading-snug text-foreground">
        {card.headline}
      </h2>
      <p className="mt-3 text-sm italic leading-relaxed text-muted-foreground">
        {card.event_context}
      </p>

      <div className="mt-6 grid grid-cols-3 gap-2">
        <Card size="sm" className="gap-0 rounded-md border-border bg-finnwise-surface py-0 shadow-none ring-0">
          <CardContent className="p-2">
            <p className="font-mono text-[8px] uppercase tracking-wide text-muted-foreground">
              Direction
            </p>
            <p className="mt-1 flex items-center gap-1.5 font-mono text-[10px] text-foreground/80">
              <span className={`h-2 w-2 rounded-full ${dotClass(card.direction_confidence.tier)}`} />
              {card.direction_confidence.label}
            </p>
          </CardContent>
        </Card>
        <Card size="sm" className="gap-0 rounded-md border-border bg-finnwise-surface py-0 shadow-none ring-0">
          <CardContent className="p-2">
            <p className="font-mono text-[8px] uppercase tracking-wide text-muted-foreground">
              Magnitude
            </p>
            <p className="mt-1 flex items-center gap-1.5 font-mono text-[10px] text-foreground/80">
              <span className={`h-2 w-2 rounded-full ${dotClass(card.magnitude_confidence.tier)}`} />
              {card.magnitude_confidence.label}
            </p>
          </CardContent>
        </Card>
        <Card size="sm" className="gap-0 rounded-md border-border bg-finnwise-surface py-0 shadow-none ring-0">
          <CardContent className="p-2">
            <p className="font-mono text-[8px] uppercase tracking-wide text-muted-foreground">
              Last reviewed
            </p>
            <p className="mt-1 font-mono text-[10px] text-foreground/80">
              {formatTime(card.last_reviewed_at ?? card.created_at)}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 space-y-3">
        <p className="font-mono text-[9px] font-medium uppercase tracking-wide text-muted-foreground">
          Instruments
        </p>
        {(card.instruments ?? []).slice(0, 4).map((i) => (
          <Card
            key={`${card.id}-panel-${i.instrument_id}`}
            size="sm"
            className="gap-0 rounded-lg border-border bg-background py-0 shadow-none ring-0"
          >
            <CardContent className="px-3 py-2">
              <p className="text-sm font-semibold text-foreground">{i.instrument_id}</p>
              <p className="mt-0.5 font-mono text-[9px] uppercase tracking-wide text-muted-foreground">
                {i.signal_type.replace(/_/g, " ")}
              </p>
            </CardContent>
          </Card>
        ))}
        {!(card.instruments ?? []).length ? (
          <p className="text-xs text-muted-foreground">No instruments linked on this card yet.</p>
        ) : null}
      </div>

      <div className="mt-8">
        <Separator className="mb-6" />
        <Button asChild variant="link" className="h-auto p-0 text-sm font-medium text-finnwise-blue">
          <Link href={`/thread/${card.id}`}>Read full analysis in The Thread →</Link>
        </Button>
        <p className="mt-2 font-mono text-[9px] text-muted-foreground">
          Updated {formatTime(card.last_reviewed_at ?? card.created_at)}
        </p>
      </div>
    </aside>
  );
}
