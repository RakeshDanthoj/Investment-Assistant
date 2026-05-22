"use client";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { cn } from "@/lib/utils";

type CurrentOriginalToggleProps = {
  view: "current" | "original";
  onChange: (view: "current" | "original") => void;
};

export function CurrentOriginalToggle({ view, onChange }: CurrentOriginalToggleProps) {
  return (
    <ToggleGroup
      type="single"
      value={view}
      onValueChange={(value) => {
        if (value === "current" || value === "original") onChange(value);
      }}
      variant="outline"
      spacing={0}
      aria-label="View mode"
      className="rounded-lg border border-slate-200 bg-white p-0.5 shadow-sm"
    >
      <ToggleGroupItem
        value="current"
        className={cn(
          "rounded-md px-3 py-1.5 font-mono text-[11px] font-medium data-[state=on]:bg-finnwise-blue data-[state=on]:text-white",
        )}
      >
        Current
      </ToggleGroupItem>
      <ToggleGroupItem
        value="original"
        className={cn(
          "rounded-md px-3 py-1.5 font-mono text-[11px] font-medium data-[state=on]:bg-finnwise-blue data-[state=on]:text-white",
        )}
      >
        Original
      </ToggleGroupItem>
    </ToggleGroup>
  );
}
