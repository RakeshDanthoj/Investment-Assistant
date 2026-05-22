import type { Cadence } from "@/lib/onboarding/state";

import { Input } from "@/components/ui/input";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

type Step2AmountProps = {
  amountDigits: string;
  cadence: Cadence;
  onAmountChange: (raw: string) => void;
  onCadenceChange: (c: Cadence) => void;
};

export function Step2Amount({
  amountDigits,
  cadence,
  onAmountChange,
  onCadenceChange,
}: Step2AmountProps) {
  const display = amountDigits.replace(/\B(?=(\d{3})+(?!\d))/g, ",");

  return (
    <div className="flex flex-col gap-3">
      <ToggleGroup
        type="single"
        value={cadence}
        onValueChange={(value) => {
          if (value === "monthly" || value === "one_time") onCadenceChange(value);
        }}
        variant="outline"
        className="w-full rounded-lg bg-muted p-0.5"
        spacing={0}
      >
        <ToggleGroupItem value="monthly" className="flex-1 rounded-md text-xs">
          monthly
        </ToggleGroupItem>
        <ToggleGroupItem value="one_time" className="flex-1 rounded-md text-xs">
          one-time
        </ToggleGroupItem>
      </ToggleGroup>

      <div className="flex items-center gap-2">
        <span className="text-base text-muted-foreground">₹</span>
        <Input
          type="text"
          inputMode="numeric"
          autoComplete="off"
          placeholder="15,000"
          value={display}
          onChange={(e) => onAmountChange(e.target.value)}
          className="min-w-0 flex-1 rounded-lg py-3"
          aria-label="Investment amount in rupees"
        />
        <span className="whitespace-nowrap text-xs text-muted-foreground">
          {cadence === "monthly" ? "/ month" : "one-time"}
        </span>
      </div>
      <p className="text-xs text-muted-foreground">minimum ₹1,000 · no maximum</p>
    </div>
  );
}
