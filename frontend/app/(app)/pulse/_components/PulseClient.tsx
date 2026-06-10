"use client";

import dynamic from "next/dynamic";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useEffect, useMemo, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { PULSE_CATEGORY_OPTIONS } from "@/lib/cards/categories";
import type { PulseFeedResponse } from "@/lib/cards/pulseTypes";
import { usePulseFeed } from "@/lib/cards/usePulseFeed";
import { dispatchPulseFeedReady } from "@/lib/pulse/feedReady";

import { EventCard } from "./EventCard";
import { PulseStaleBanner } from "./PulseStaleBanner";
import { PulseStickyHeader } from "./PulseStickyHeader";
import { Topbar } from "./Topbar";

const FogOfWarBanner = dynamic(
  () => import("./FogOfWarBanner").then((m) => ({ default: m.FogOfWarBanner })),
  { ssr: false },
);

const InsightPanel = dynamic(
  () => import("./InsightPanel").then((m) => ({ default: m.InsightPanel })),
  { ssr: false },
);

const MarketFactsStrip = dynamic(
  () =>
    import("@/components/market-facts/MarketFactsStrip").then((m) => ({
      default: m.MarketFactsStrip,
    })),
  { ssr: false },
);

function FeedSkeletonRow() {
  return (
    <div
      className="h-[152px] w-full rounded-lg border border-border bg-background p-4"
      aria-hidden
    >
      <div className="mb-2 flex gap-2">
        <Skeleton className="h-5 w-16 rounded" />
        <Skeleton className="h-5 w-14 rounded-full" />
      </div>
      <Skeleton className="h-4 w-full max-w-md" />
      <Skeleton className="mt-2 h-3 w-full max-w-sm" />
      <div className="mt-3 flex gap-4">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
  );
}

function FeedSkeleton() {
  return (
    <div className="mx-auto w-full max-w-[380px] space-y-4 py-6 min-[860px]:max-w-6xl min-[860px]:px-4">
      {[1, 2, 3].map((k) => (
        <FeedSkeletonRow key={k} />
      ))}
    </div>
  );
}

type PulseClientProps = {
  initialData?: PulseFeedResponse | null;
  initialCategoryQuery?: string;
  initialSessionId?: string | null;
  initialPersonalisationToken?: string | null;
  children?: ReactNode;
};

export default function PulseClient({
  initialData = null,
  initialCategoryQuery = "",
  initialSessionId = null,
  initialPersonalisationToken = null,
  children = null,
}: PulseClientProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const selectedCategories = useMemo(() => {
    const raw = searchParams.get("category");
    return raw ? raw.split(",").filter(Boolean) : [];
  }, [searchParams]);

  const {
    status,
    data,
    errorMessage,
    selectedId,
    setSelectedId,
    selectedCard,
    refetch,
    showStaleBanner,
    isFetching,
  } = usePulseFeed(selectedCategories, {
    initialData,
    initialCategoryQuery,
    initialSessionId,
    initialPersonalisationToken,
  });

  const feedReady = status === "success" && Boolean(data);

  useEffect(() => {
    if (feedReady) dispatchPulseFeedReady();
  }, [feedReady]);

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
      <PulseStickyHeader>
        <Topbar
          counts={data?.counts ?? 0}
          lastUpdated={data?.last_updated ?? null}
          categoryOptions={PULSE_CATEGORY_OPTIONS}
          selectedCategories={selectedCategories}
          onCategoriesChange={onCategoriesChange}
        />
        {feedReady ? (
          <MarketFactsStrip className="border-b-0 py-1.5 min-[860px]:py-2" compact enabled />
        ) : null}
      </PulseStickyHeader>
      {showStaleBanner ? (
        <PulseStaleBanner onRefresh={() => void refetch()} isRefreshing={isFetching} />
      ) : null}
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

      {children}

      {data?.cards?.length ? (
        <div className="mx-auto hidden w-full max-w-6xl flex-1 gap-0 min-[860px]:flex">
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
