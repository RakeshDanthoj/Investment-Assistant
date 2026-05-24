"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getApiBaseUrl, describeFetchFailure } from "@/lib/api";
import { categoryLabel } from "@/lib/cards/categories";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

export type SavedThreadItem = {
  card_id: string;
  card_title: string;
  event_category: string;
  saved_at: string;
};

type SavedThreadsNavProps = {
  pathname: string;
};

export function SavedThreadsNav({ pathname }: SavedThreadsNavProps) {
  const [items, setItems] = useState<SavedThreadItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      setItems([]);
      setLoading(false);
      return;
    }

    try {
      const base = getApiBaseUrl();
      const res = await fetch(`${base}/api/saved-threads`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
        cache: "no-store",
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `Request failed (${res.status})`);
      }
      const json = (await res.json()) as { items: SavedThreadItem[] };
      setItems(json.items);
    } catch (err) {
      setError(describeFetchFailure(err, "load saved cards"));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const handler = () => void load();
    window.addEventListener("saved-threads-changed", handler);
    return () => window.removeEventListener("saved-threads-changed", handler);
  }, [load]);

  if (!loading && items.length === 0 && !error) {
    return null;
  }

  return (
    <div className="mt-6 px-2">
      <p className="px-2 font-mono text-[9px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
        Saved
      </p>
      {loading ? (
        <div className="mt-2 space-y-1 px-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
      ) : null}
      {error ? (
        <p className="mt-2 px-2 text-[11px] text-destructive">{error}</p>
      ) : null}
      <ul className="mt-2 space-y-0.5">
        {items.map((item) => {
          const href = `/thread/${item.card_id}`;
          const isActive = pathname === href;
          return (
            <li key={item.card_id}>
              <Button
                variant="ghost"
                asChild
                className={cn(
                  "h-auto min-h-9 w-full flex-col items-start gap-0.5 px-2.5 py-2 text-left text-[12px] font-normal",
                  isActive &&
                    "bg-sidebar-accent font-medium text-sidebar-accent-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                )}
              >
                <Link href={href} title={item.card_title}>
                  <span className="line-clamp-2 w-full leading-snug">{item.card_title}</span>
                  <span className="font-mono text-[9px] text-muted-foreground">
                    {categoryLabel(item.event_category)}
                  </span>
                </Link>
              </Button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
