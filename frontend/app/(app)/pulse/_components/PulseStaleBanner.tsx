"use client";

import { Button } from "@/components/ui/button";

type PulseStaleBannerProps = {
  onRefresh: () => void;
  isRefreshing?: boolean;
};

export function PulseStaleBanner({ onRefresh, isRefreshing = false }: PulseStaleBannerProps) {
  return (
    <div
      className="border-b border-amber-200/80 bg-amber-50 px-4 py-2 text-center text-sm text-amber-950"
      role="status"
    >
      <span>Feed data is more than 24 hours old. </span>
      <Button
        type="button"
        variant="link"
        className="h-auto p-0 text-amber-950 underline"
        disabled={isRefreshing}
        onClick={onRefresh}
      >
        Refresh now
      </Button>
    </div>
  );
}
