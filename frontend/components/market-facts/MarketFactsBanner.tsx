"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";

import type { MarketFactsResponse } from "@/lib/marketFacts/types";

type MarketFactsBannerProps = {
  data: MarketFactsResponse | null;
  loading?: boolean;
  errorMessage?: string | null;
};

export function MarketFactsBanner({ data, loading, errorMessage }: MarketFactsBannerProps) {
  if (loading && !data) {
    return (
      <Alert className="border-slate-200 bg-slate-50">
        <AlertDescription className="text-sm text-slate-600">
          Checking critical market fact freshness…
        </AlertDescription>
      </Alert>
    );
  }

  if (errorMessage) {
    return (
      <Alert variant="destructive" className="border-amber-200 bg-amber-50 text-amber-950">
        <AlertDescription>
          Could not load market fact freshness. Card generation may be held until facts recover.
          <span className="mt-1 block text-xs text-amber-800">{errorMessage}</span>
        </AlertDescription>
      </Alert>
    );
  }

  if (!data) {
    return null;
  }

  if (data.unavailable_critical.length) {
    return (
      <Alert variant="destructive" className="border-red-200 bg-red-50 text-red-950">
        <AlertDescription>
          Card generation is <strong>held</strong> — critical facts unavailable:{" "}
          {data.unavailable_critical.join(", ")}. Draft cards will not start until these recover.
        </AlertDescription>
      </Alert>
    );
  }

  if (data.has_stale_critical) {
    return (
      <Alert className="border-amber-200 bg-amber-50 text-amber-950">
        <AlertDescription>
          Some critical market facts are stale. Draft generation can proceed, but chips show amber
          dots — treat macro numbers with extra caution.
        </AlertDescription>
      </Alert>
    );
  }

  return null;
}
