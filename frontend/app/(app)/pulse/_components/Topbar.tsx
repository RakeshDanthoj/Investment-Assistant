"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { formatFinnwiseTime } from "@/lib/format/dateTime";

import { FilterPills } from "./FilterPills";

type TopbarProps = {
  counts: number;
  lastUpdated: string | null;
  categoryOptions: readonly { id: string; label: string }[];
  selectedCategories: string[];
  onCategoriesChange: (next: string[]) => void;
};

function filterSummaryLabel(
  selectedCategories: string[],
  categoryOptions: readonly { id: string; label: string }[],
): string {
  if (selectedCategories.length === 0) return "All";
  if (selectedCategories.length === 1) {
    const match = categoryOptions.find((option) => option.id === selectedCategories[0]);
    return match?.label ?? "1 filter";
  }
  return `${selectedCategories.length} filters`;
}

export function Topbar({
  counts,
  lastUpdated,
  categoryOptions,
  selectedCategories,
  onCategoriesChange,
}: TopbarProps) {
  const [filtersOpen, setFiltersOpen] = useState(false);
  const filterLabel = useMemo(
    () => filterSummaryLabel(selectedCategories, categoryOptions),
    [selectedCategories, categoryOptions],
  );
  const eventMeta = `${counts} event${counts === 1 ? "" : "s"} · Updated ${formatFinnwiseTime(lastUpdated)}`;

  return (
    <div className="mx-auto max-w-6xl px-4 py-2 min-[860px]:py-3">
      <div className="flex min-[860px]:hidden flex-col gap-2">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h1 className="font-display text-lg font-semibold text-foreground">The Pulse</h1>
            <p className="mt-0.5 font-mono text-[9px] text-muted-foreground">{eventMeta}</p>
          </div>
          <Collapsible open={filtersOpen} onOpenChange={setFiltersOpen}>
            <CollapsibleTrigger asChild>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="shrink-0 font-mono text-[10px] uppercase tracking-wide"
                aria-expanded={filtersOpen}
              >
                Filters · {filterLabel}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2">
              <FilterPills
                options={categoryOptions}
                selected={selectedCategories}
                onChange={onCategoriesChange}
              />
            </CollapsibleContent>
          </Collapsible>
        </div>
      </div>

      <div className="hidden min-[860px]:flex min-[860px]:flex-row min-[860px]:items-center min-[860px]:justify-between min-[860px]:gap-3">
        <div className="flex flex-wrap items-baseline gap-4">
          <h1 className="font-display text-xl font-semibold text-foreground">The Pulse</h1>
          <div className="min-w-0 flex-1">
            <FilterPills
              options={categoryOptions}
              selected={selectedCategories}
              onChange={onCategoriesChange}
            />
          </div>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-0.5 font-mono text-[10px] text-muted-foreground min-[860px]:text-right">
          <span>
            {counts} event{counts === 1 ? "" : "s"}
          </span>
          <span>Updated {formatFinnwiseTime(lastUpdated)}</span>
        </div>
      </div>
    </div>
  );
}
