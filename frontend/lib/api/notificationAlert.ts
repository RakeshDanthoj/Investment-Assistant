/**
 * Deduped, deferred fetch for the global signal-fired notification badge (PC-1.2).
 */

type NotificationDto = {
  card_id: string;
  kind: string;
};

let inFlight: Promise<string | null> | null = null;
let cachedCardId: string | null | undefined;

function defer<T>(fn: () => Promise<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    const run = () => {
      void fn().then(resolve, reject);
    };
    if (typeof requestIdleCallback === "function") {
      requestIdleCallback(() => run(), { timeout: 2000 });
    } else {
      setTimeout(run, 0);
    }
  });
}

export async function fetchSignalFiredCardId(
  fetchImpl: typeof fetch,
  url: string,
  accessToken: string,
): Promise<string | null> {
  if (cachedCardId !== undefined) return cachedCardId;
  if (inFlight) return inFlight;

  inFlight = defer(async () => {
    try {
      const res = await fetchImpl(url, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) {
        cachedCardId = null;
        return null;
      }
      const body = (await res.json()) as { items?: NotificationDto[] };
      const hit = body.items?.find((x) => x.kind === "signal_fired");
      cachedCardId = hit?.card_id ?? null;
      return cachedCardId;
    } catch {
      cachedCardId = null;
      return null;
    } finally {
      inFlight = null;
    }
  });

  return inFlight;
}

/** Test-only reset */
export function resetNotificationAlertCacheForTests(): void {
  inFlight = null;
  cachedCardId = undefined;
}
