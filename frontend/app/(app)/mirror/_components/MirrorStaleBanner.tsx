"use client";

type MirrorStaleBannerProps = {
  visible: boolean;
  refreshing?: boolean;
};

/** Shown when Mirror data is older than 24h (PI-S2 / D2). */
export function MirrorStaleBanner({ visible, refreshing = false }: MirrorStaleBannerProps) {
  if (!visible) return null;

  return (
    <div
      role="status"
      className="border-b border-amber-500/30 bg-amber-500/10 px-4 py-2 text-center text-sm text-amber-950 dark:text-amber-100"
    >
      {refreshing
        ? "Refreshing your Mirror data in the background…"
        : "Your Mirror data is more than a day old. It will refresh shortly without clearing the page."}
    </div>
  );
}
