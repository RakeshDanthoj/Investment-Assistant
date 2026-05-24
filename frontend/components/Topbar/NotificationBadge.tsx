"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { fetchSignalFiredCardId } from "@/lib/api/notificationAlert";
import { getApiBaseUrl } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

export function NotificationBadge() {
  const router = useRouter();
  const [targetCardId, setTargetCardId] = useState<string | null>(null);

  useEffect(() => {
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
  }, []);

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
