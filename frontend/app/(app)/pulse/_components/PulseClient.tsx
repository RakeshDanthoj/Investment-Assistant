"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useMemo } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { PULSE_CATEGORY_OPTIONS } from "@/lib/cards/categories";
import type { PulseFeedResponse } from "@/lib/cards/pulseTypes";
import { usePulseFeed } from "@/lib/cards/usePulseFeed";

import { EventCard } from "./EventCard";
import { FogOfWarBanner } from "./FogOfWarBanner";
import { InsightPanel } from "./InsightPanel";
import { Topbar } from "./Topbar";

function FeedSkeleton() {
  return (
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-6">
      {[1, 2, 3].map((k) => (
        <Skeleton key={k} className="h-40 rounded-lg border border-border" />
      ))}
    </div>
  );
}

type PulseClientProps = {
  initialData?: PulseFeedResponse | null;
  initialCategoryQuery?: string;
};

export default function PulseClient({
  initialData = null,
  initialCategoryQuery = "",
}: PulseClientProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const selectedCategories = useMemo(() => {
    const raw = searchParams.get("category");
    return raw ? raw.split(",").filter(Boolean) : [];
  }, [searchParams]);

  const { status, data, errorMessage, selectedId, setSelectedId, selectedCard, refetch } =
    usePulseFeed(selectedCategories, { initialData, initialCategoryQuery });

  function onCategoriesChange(next: string[]) {
    const p = new URLSearchParams(searchParams.toString());
    if (next.length) p.set("category", [...next].sort().join(","));
    else p.delete("category");
    const q = p.toString();
    router.replace(q ? `${pathname}?${q}` : pathname, { scroll: false });
  }

  function handleSelectCard(cardId: string) {
    if (
      typeof window !== "undefined" &&
      window.matchMedia("(max-width: 859px)").matches
    ) {
      router.push(`/thread/${cardId}`);
      return;
    }
    setSelectedId(cardId);
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <Topbar
        counts={data?.counts ?? 0}
        lastUpdated={data?.last_updated ?? null}
        categoryOptions={PULSE_CATEGORY_OPTIONS}
        selectedCategories={selectedCategories}
        onCategoriesChange={onCategoriesChange}
      />
      {data?.fog_of_war ? <FogOfWarBanner /> : null}

      {status === "loading" && !data ? <FeedSkeleton /> : null}

      {status === "error" ? (
        <div className="mx-auto max-w-xl px-4 py-12 text-center">
          <p className="text-sm text-foreground">{errorMessage}</p>
          <Button type="button" onClick={() => void refetch()} className="mt-4">
            Retry
          </Button>
        </div>
      ) : null}

      {status === "success" && data && data.cards.length === 0 ? (
        <div className="mx-auto max-w-xl px-4 py-16 text-center">
          <p className="font-display text-lg text-foreground">No events match your filters</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Try clearing category filters or check back after the next editorial publish.
          </p>
        </div>
      ) : null}

      {data?.cards?.length ? (
        <div className="mx-auto flex w-full max-w-6xl flex-1 gap-0 min-[860px]:gap-0">
          <section
            className="min-w-0 flex-1 space-y-4 px-4 py-6 min-[860px]:basis-[60%]"
            aria-label="Event feed"
          >
            {data.cards.map((card) => (
              <EventCard
                key={card.id}
                card={card}
                selected={card.id === selectedId}
                onSelect={() => handleSelectCard(card.id)}
              />
            ))}
          </section>
          <div className="hidden min-w-0 basis-[40%] min-[860px]:block">
            <InsightPanel card={selectedCard} />
          </div>
        </div>
      ) : null}
    </div>
  );
}
