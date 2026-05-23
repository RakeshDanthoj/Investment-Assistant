"use client";

import type { PulseCard } from "@/lib/cards/pulseTypes";
import { cn } from "@/lib/utils";

import { EventCardSurface } from "./EventCardSurface";

type EventCardProps = {
  card: PulseCard;
  selected: boolean;
  onSelect: () => void;
};

/** Desktop feed row — interactive selection for the insight panel. */
export function EventCard({ card, selected, onSelect }: EventCardProps) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect();
        }
      }}
      className="rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <EventCardSurface
        card={card}
        selected={selected}
        className={cn(
          "cursor-pointer transition-all duration-150 ease-in-out hover:border-border/80",
        )}
      />
    </div>
  );
}
