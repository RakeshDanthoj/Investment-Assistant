import type { InvestmentStatus } from "@/lib/onboarding/state";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const OPTIONS: {
  id: InvestmentStatus;
  title: string;
  subtitle: string;
}[] = [
  {
    id: "starting_fresh",
    title: "Starting fresh",
    subtitle: "No investments yet — help me figure out where to begin",
  },
  {
    id: "has_investments",
    title: "I have some investments",
    subtitle: "SIPs, stocks, or anything else — I want to understand what's affecting them",
  },
  {
    id: "curious",
    title: "I'm just curious for now",
    subtitle: "Not ready to invest yet, but I want to understand how it all works",
  },
];

type Step1StatusProps = {
  selected: InvestmentStatus | null;
  onSelect: (s: InvestmentStatus) => void;
};

export function Step1Status({ selected, onSelect }: Step1StatusProps) {
  return (
    <div className="flex flex-col gap-2">
      {OPTIONS.map((opt) => {
        const isSelected = selected === opt.id;
        return (
          <Button
            key={opt.id}
            type="button"
            variant={isSelected ? "selected" : "outline"}
            onClick={() => onSelect(opt.id)}
            aria-pressed={isSelected}
            className={cn(
              "h-auto w-full justify-start rounded-xl px-5 py-3.5 text-left",
              !isSelected && "hover:border-primary/60",
            )}
          >
            <span className="flex flex-col items-start gap-1">
              <span className="text-sm font-medium text-foreground">{opt.title}</span>
              <span className="text-xs font-normal text-muted-foreground">{opt.subtitle}</span>
            </span>
          </Button>
        );
      })}
    </div>
  );
}
