"use client";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

type FilterPillsProps = {
  options: readonly { id: string; label: string }[];
  selected: string[];
  onChange: (next: string[]) => void;
};

const pillClassName =
  "rounded-full px-2.5 py-1 font-mono text-[10px] uppercase tracking-wide data-[state=on]:border-finnwise-blue data-[state=on]:bg-finnwise-blue data-[state=on]:text-white";

export function FilterPills({ options, selected, onChange }: FilterPillsProps) {
  const allActive = selected.length === 0;

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <ToggleGroup
        type="single"
        value={allActive ? "__all__" : ""}
        onValueChange={(value) => {
          if (value === "__all__") onChange([]);
        }}
        variant="outline"
        size="sm"
        spacing={0}
        className="flex-wrap gap-1.5 border-0 bg-transparent p-0 shadow-none"
      >
        <ToggleGroupItem value="__all__" className={pillClassName}>
          All
        </ToggleGroupItem>
      </ToggleGroup>
      <ToggleGroup
        type="multiple"
        value={selected}
        onValueChange={onChange}
        variant="outline"
        size="sm"
        spacing={0}
        className="flex-wrap gap-1.5 border-0 bg-transparent p-0 shadow-none"
      >
        {options.map((opt) => (
          <ToggleGroupItem key={opt.id} value={opt.id} className={pillClassName}>
            {opt.label}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
    </div>
  );
}
