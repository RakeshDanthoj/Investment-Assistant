"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import type { MapSectorDetailResponse } from "@/lib/map/types";

import { MapModule as MapModuleCard } from "./MapModule";
import { SensitivityMatrix } from "./SensitivityMatrix";

type MapSectorClientProps = {
  detail: MapSectorDetailResponse;
};

export function MapSectorClient({ detail }: MapSectorClientProps) {
  const searchParams = useSearchParams();
  const highlightId = searchParams.get("module");

  return (
    <div className="mx-auto w-full max-w-6xl space-y-8 px-4 py-8">
      <header>
        <Link href="/map" className="text-[13px] font-medium text-finnwise-blue hover:underline">
          ← All sectors
        </Link>
        <h1 className="font-display mt-3 text-2xl font-bold text-slate-900">{detail.sector.name}</h1>
        <p className="mt-2 text-[13px] text-slate-600">
          {detail.instrument_count} NSE instruments · 8 macro factors (PRD §7.1)
        </p>
      </header>

      <section className="space-y-4" data-testid="sector-modules">
        <h2 className="font-display text-lg font-semibold text-slate-900">Learning modules</h2>
        {detail.modules.map((mod) => (
          <MapModuleCard
            key={mod.id}
            module={mod}
            highlighted={highlightId === mod.id}
          />
        ))}
      </section>

      <SensitivityMatrix
        factors={detail.factors}
        instruments={detail.instruments}
        sensitivities={detail.sensitivities}
        totalInstrumentCount={detail.instrument_count}
      />
    </div>
  );
}
