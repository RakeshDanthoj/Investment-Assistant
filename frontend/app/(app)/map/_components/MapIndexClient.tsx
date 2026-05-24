"use client";

import Link from "next/link";

import type { MapModule, MapSectorSummary } from "@/lib/map/types";

import { MapModule as MapModuleCard } from "./MapModule";
import { SectorTile } from "./SectorTile";

type MapIndexClientProps = {
  sectors: MapSectorSummary[];
  highlightedModule: MapModule | null;
};

export function MapIndexClient({ sectors, highlightedModule }: MapIndexClientProps) {
  return (
    <div className="mx-auto w-full max-w-6xl space-y-8 px-4 py-8">
      <header>
        <p className="font-mono text-[10px] font-semibold uppercase tracking-wide text-slate-500">
          Portfolio Builder
        </p>
        <h1 className="font-display text-2xl font-bold text-slate-900">The Map</h1>
        <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-slate-600">
          Eight sectors of the Indian economy — factor sensitivities and how each sector typically
          reacts to macro and policy events before you trade the live feed.
        </p>
      </header>

      {highlightedModule ? (
        <section className="space-y-3" data-testid="highlighted-gap-module">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Linked module
          </p>
          <MapModuleCard module={highlightedModule} highlighted />
          {highlightedModule.sector_slug ? (
            <Link
              href={`/map/${highlightedModule.sector_slug}`}
              className="text-[13px] font-medium text-finnwise-blue hover:underline"
            >
              View {highlightedModule.sector_slug} sector →
            </Link>
          ) : null}
        </section>
      ) : null}

      <section
        className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
        data-testid="sector-tile-grid"
      >
        {sectors.map((sector) => (
          <SectorTile key={sector.slug} sector={sector} />
        ))}
      </section>
    </div>
  );
}
