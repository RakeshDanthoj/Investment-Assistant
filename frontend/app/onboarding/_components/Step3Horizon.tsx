import type { Horizon } from "@/lib/onboarding/state";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const CELLS: { id: Horizon; title: string; subtitle: string }[] = [
  {
    id: "under_1y",
    title: "Under 1 year",
    subtitle: "Short-term — capital preservation matters",
  },
  {
    id: "1_3y",
    title: "1 to 3 years",
    subtitle: "Medium horizon — growth with flexibility",
  },
  {
    id: "3_7y",
    title: "3 to 7 years",
    subtitle: "Ride cycles — growth focus",
  },
  {
    id: "7_plus",
    title: "7 years or more",
    subtitle: "Long horizon — full equity potential",
  },
];

type Step3HorizonProps = {
  selected: Horizon | null;
  onSelect: (h: Horizon) => void;
};

export function Step3Horizon({ selected, onSelect }: Step3HorizonProps) {
  return (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
      {CELLS.map((cell) => {
        const isSelected = selected === cell.id;
        return (
          <Button
            key={cell.id}
            type="button"
            variant={isSelected ? "selected" : "outline"}
            onClick={() => onSelect(cell.id)}
            aria-pressed={isSelected}
            className={cn(
              "h-auto justify-start rounded-xl px-4 py-3 text-left",
              !isSelected && "hover:border-primary/60",
            )}
          >
            <span className="flex flex-col items-start gap-1">
              <span className="text-sm font-semibold text-foreground">{cell.title}</span>
              <span className="font-mono text-[10px] font-normal uppercase tracking-wide text-muted-foreground">
                {cell.subtitle}
              </span>
            </span>
          </Button>
        );
      })}
    </div>
  );
}
