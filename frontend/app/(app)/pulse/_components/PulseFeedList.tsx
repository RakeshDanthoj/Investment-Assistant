import Link from "next/link";

import type { PulseCard } from "@/lib/cards/pulseTypes";

import { EventCardSurface } from "./EventCardSurface";

type PulseFeedListProps = {
  cards: PulseCard[];
};

/** Mobile-first feed: server HTML + links, no client hydration for card rows. */
export function PulseFeedList({ cards }: PulseFeedListProps) {
  return (
    <section
      className="mx-auto min-w-0 flex-1 space-y-4 px-4 py-6 min-[860px]:hidden"
      aria-label="Event feed"
    >
      {cards.map((card) => (
        <Link
          key={card.id}
          href={`/thread/${card.id}`}
          prefetch={false}
          className="block rounded-lg transition-colors hover:border-border/80"
        >
          <EventCardSurface card={card} />
        </Link>
      ))}
    </section>
  );
}
