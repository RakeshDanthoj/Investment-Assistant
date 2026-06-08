"use client";

import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";

import type { MapSectorSummary } from "@/lib/map/types";
import {
  fetchMapSectorSummaryClient,
  mapQueryKeys,
  MAP_STALE_TIME_MS,
} from "@/lib/map/mapQueries";
import { useIntentPrefetch } from "@/lib/perf/useIntentPrefetch";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

const ACCENT_STYLES: Record<string, string> = {
  sky: "from-sky-500/20 to-sky-600/5 border-sky-200/80",
  violet: "from-violet-500/20 to-violet-600/5 border-violet-200/80",
  amber: "from-amber-500/20 to-amber-600/5 border-amber-200/80",
  emerald: "from-emerald-500/20 to-emerald-600/5 border-emerald-200/80",
  rose: "from-rose-500/20 to-rose-600/5 border-rose-200/80",
  teal: "from-teal-500/20 to-teal-600/5 border-teal-200/80",
  slate: "from-slate-500/20 to-slate-600/5 border-slate-200/80",
  indigo: "from-indigo-500/20 to-indigo-600/5 border-indigo-200/80",
  orange: "from-orange-500/20 to-orange-600/5 border-orange-200/80",
};

type SectorTileProps = {
  sector: MapSectorSummary;
};

export function SectorTile({ sector }: SectorTileProps) {
  const accent = ACCENT_STYLES[sector.cover_accent] ?? ACCENT_STYLES.slate;
  const initial = sector.name.trim().charAt(0).toUpperCase();
  const queryClient = useQueryClient();
  const supabase = useMemo(() => createClient(), []);
  const { onPointerEnter, onPointerLeave } = useIntentPrefetch();

  const prefetchSummary = useCallback(
    async (signal: AbortSignal) => {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session?.access_token) return;

      await queryClient.prefetchQuery({
        queryKey: mapQueryKeys.sectorSummary(sector.slug),
        queryFn: () => fetchMapSectorSummaryClient(session.access_token, sector.slug, signal),
        staleTime: MAP_STALE_TIME_MS,
      });
    },
    [queryClient, sector.slug, supabase],
  );

  return (
    <Link
      href={`/map/${sector.slug}`}
      className={cn(
        "group flex min-h-[140px] flex-col justify-between rounded-xl border bg-gradient-to-br p-5 shadow-sm transition hover:shadow-md",
        accent,
      )}
      data-testid={`sector-tile-${sector.slug}`}
      onPointerEnter={() => onPointerEnter(sector.slug, prefetchSummary)}
      onPointerLeave={onPointerLeave}
    >
      <div className="flex items-start justify-between gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/80 font-display text-lg font-bold text-slate-800 shadow-sm">
          {initial}
        </span>
        <span className="font-mono text-[10px] uppercase tracking-wide text-slate-500">
          {sector.instrument_count} stocks
        </span>
      </div>
      <div>
        <h2 className="font-display text-lg font-semibold text-slate-900 group-hover:text-finnwise-blue">
          {sector.name}
        </h2>
        <p className="mt-1 text-[13px] text-slate-600">Factor sensitivities + event reactions</p>
      </div>
    </Link>
  );
}
