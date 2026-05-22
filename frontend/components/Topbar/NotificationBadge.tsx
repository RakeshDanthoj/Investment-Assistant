"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { getApiBaseUrl } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

type NotificationDto = {
  card_id: string;
  kind: string;
};

export function NotificationBadge() {
  const router = useRouter();
  const [targetCardId, setTargetCardId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session?.access_token || cancelled) return;
      const base = getApiBaseUrl().replace(/\/$/, "");
      try {
        const res = await fetch(`${base}/api/notifications?limit=50`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (!res.ok || cancelled) return;
        const body = (await res.json()) as { items?: NotificationDto[] };
        const hit = body.items?.find((x) => x.kind === "signal_fired");
        if (hit?.card_id && !cancelled) setTargetCardId(hit.card_id);
      } catch {
        /* missing backend / network — hide badge */
      }
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
