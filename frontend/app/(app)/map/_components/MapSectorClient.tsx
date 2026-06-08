"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import type { MapSectorSummaryDetail } from "@/lib/map/types";
import {
  fetchMapSectorMatrixClient,
  fetchMapSectorSummaryClient,
  mapQueryKeys,
  MAP_STALE_TIME_MS,
} from "@/lib/map/mapQueries";
import { createClient } from "@/lib/supabase/client";

import { MapModule as MapModuleCard } from "./MapModule";
import { SensitivityMatrix } from "./SensitivityMatrix";

type MapSectorClientProps = {
  summary: MapSectorSummaryDetail;
};

function MatrixSkeleton() {
  return (
    <div className="space-y-3" data-testid="sensitivity-matrix-skeleton">
      <Skeleton className="h-6 w-48" />
      <Skeleton className="h-64 w-full rounded-lg" />
    </div>
  );
}

function SensitivityMatrixSection({
  slug,
  instrumentCount,
}: {
  slug: string;
  instrumentCount: number;
}) {
  const [visible, setVisible] = useState(false);
  const sectionRef = useRef<HTMLElement>(null);
  const supabase = useMemo(() => createClient(), []);

  useEffect(() => {
    const node = sectionRef.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "120px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const { data, isLoading, isError } = useQuery({
    queryKey: mapQueryKeys.sectorMatrix(slug),
    queryFn: async ({ signal }) => {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session?.access_token) {
        throw new Error("Sign in to load factor sensitivities.");
      }
      return fetchMapSectorMatrixClient(session.access_token, slug, signal);
    },
    enabled: visible,
    staleTime: MAP_STALE_TIME_MS,
  });

  return (
    <section ref={sectionRef} data-testid="sensitivity-matrix-section">
      {!visible || isLoading ? <MatrixSkeleton /> : null}
      {isError ? (
        <p className="text-[13px] text-rose-700">Could not load factor sensitivities.</p>
      ) : null}
      {data ? (
        <SensitivityMatrix
          factors={data.factors}
          instruments={data.instruments}
          sensitivities={data.sensitivities}
          totalInstrumentCount={data.instrument_count ?? instrumentCount}
        />
      ) : null}
    </section>
  );
}

export function MapSectorClient({ summary: initialSummary }: MapSectorClientProps) {
  const searchParams = useSearchParams();
  const highlightId = searchParams.get("module");
  const supabase = useMemo(() => createClient(), []);
  const slug = initialSummary.sector.slug;

  const { data: summary } = useQuery({
    queryKey: mapQueryKeys.sectorSummary(slug),
    queryFn: async ({ signal }) => {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session?.access_token) {
        throw new Error("Sign in to explore The Map.");
      }
      return fetchMapSectorSummaryClient(session.access_token, slug, signal);
    },
    initialData: initialSummary,
    staleTime: MAP_STALE_TIME_MS,
    refetchOnMount: false,
  });

  return (
    <div className="mx-auto w-full max-w-6xl space-y-8 px-4 py-8">
      <header>
        <Link href="/map" className="text-[13px] font-medium text-finnwise-blue hover:underline">
          ← All sectors
        </Link>
        <h1 className="font-display mt-3 text-2xl font-bold text-slate-900">{summary.sector.name}</h1>
        <p className="mt-2 text-[13px] text-slate-600">
          {summary.instrument_count} NSE instruments · 8 macro factors (PRD §7.1)
        </p>
      </header>

      <section className="space-y-4" data-testid="sector-modules">
        <h2 className="font-display text-lg font-semibold text-slate-900">Learning modules</h2>
        {summary.modules.map((mod) => (
          <MapModuleCard
            key={mod.id}
            module={mod}
            highlighted={highlightId === mod.id}
          />
        ))}
      </section>

      <SensitivityMatrixSection slug={slug} instrumentCount={summary.instrument_count} />
    </div>
  );
}
