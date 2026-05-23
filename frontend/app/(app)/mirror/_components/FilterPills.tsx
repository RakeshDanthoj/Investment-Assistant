"use client";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

import { MIRROR_FILTER_OPTIONS } from "@/lib/mirror/types";

const pillClassName =
  "rounded-full px-2.5 py-1 font-mono text-[10px] uppercase tracking-wide data-[state=on]:border-finnwise-blue data-[state=on]:bg-finnwise-blue data-[state=on]:text-white";

type FilterPillsProps = {
  status: string | null;
  onStatusChange: (next: string | null) => void;
};

export function FilterPills({ status, onStatusChange }: FilterPillsProps) {
  return (
    <div className="flex flex-wrap items-center gap-1.5" data-testid="mirror-filter-pills">
      <ToggleGroup
        type="single"
        value={status ?? "__all__"}
        onValueChange={(value) => {
          if (!value || value === "__all__") onStatusChange(null);
          else onStatusChange(value);
        }}
        variant="outline"
        size="sm"
        spacing={0}
        className="flex-wrap gap-1.5 border-0 bg-transparent p-0 shadow-none"
      >
        <ToggleGroupItem value="__all__" className={pillClassName}>
          All
        </ToggleGroupItem>
        {MIRROR_FILTER_OPTIONS.map((opt) => (
          <ToggleGroupItem key={opt.id} value={opt.id} className={pillClassName}>
            {opt.label}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
    </div>
  );
}
