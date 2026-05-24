"use client";

import { formatFinnwiseTime } from "@/lib/format/dateTime";

import { FilterPills } from "./FilterPills";

type TopbarProps = {
  counts: number;
  lastUpdated: string | null;
  categoryOptions: readonly { id: string; label: string }[];
  selectedCategories: string[];
  onCategoriesChange: (next: string[]) => void;
};

export function Topbar({
  counts,
  lastUpdated,
  categoryOptions,
  selectedCategories,
  onCategoriesChange,
}: TopbarProps) {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-background">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 min-[860px]:flex-row min-[860px]:items-center min-[860px]:justify-between">
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
    </header>
  );
}
