import type { MapModule as MapModuleType } from "@/lib/map/types";

import { cn } from "@/lib/utils";

type MapModuleProps = {
  module: MapModuleType;
  highlighted?: boolean;
};

export function MapModule({ module, highlighted = false }: MapModuleProps) {
  return (
    <article
      id={`module-${module.id}`}
      className={cn(
        "rounded-lg border border-slate-200 bg-white p-5 shadow-sm",
        highlighted && "ring-2 ring-finnwise-blue/40",
      )}
      data-testid={`map-module-${module.id}`}
    >
      <h3 className="font-display text-base font-semibold text-slate-900">{module.title}</h3>
      <p className="mt-3 text-[13px] leading-relaxed text-slate-700">{module.body}</p>
    </article>
  );
}
