"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { fetchSignalFiredCardId } from "@/lib/api/notificationAlert";
import { getApiBaseUrl } from "@/lib/api";
import { PULSE_FEED_READY_EVENT } from "@/lib/pulse/feedReady";
import { createClient } from "@/lib/supabase/client";

type NotificationBadgeProps = {
  /** On Pulse, wait for feed paint before fetching (PC-1.2 / PI-S4). */
  deferUntilFeedReady?: boolean;
};

export function NotificationBadge({ deferUntilFeedReady = false }: NotificationBadgeProps) {
  const router = useRouter();
  const [targetCardId, setTargetCardId] = useState<string | null>(null);
  const [mayFetch, setMayFetch] = useState(!deferUntilFeedReady);

  useEffect(() => {
    if (!deferUntilFeedReady) return;
    const onReady = () => setMayFetch(true);
    window.addEventListener(PULSE_FEED_READY_EVENT, onReady, { once: true });
    return () => window.removeEventListener(PULSE_FEED_READY_EVENT, onReady);
  }, [deferUntilFeedReady]);

  useEffect(() => {
    if (!mayFetch) return;
    let cancelled = false;
    void (async () => {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session?.access_token || cancelled) return;
      const base = getApiBaseUrl().replace(/\/$/, "");
      const cardId = await fetchSignalFiredCardId(
        fetch,
        `${base}/api/notifications?limit=50`,
        session.access_token,
      );
      if (!cancelled && cardId) setTargetCardId(cardId);
    })();
    return () => {
      cancelled = true;
    };
  }, [mayFetch]);

  if (!targetCardId) return null;

  return (
    <Button
      variant="outline"
      size="icon-sm"
      onClick={() => router.push(`/thread/${targetCardId}`)}
      aria-label="Open thread for signal alert"
      className="relative"
    >
      <span
        className="inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-primary"
        style={{ animationDuration: "1.5s" }}
      />
    </Button>
  );
}
