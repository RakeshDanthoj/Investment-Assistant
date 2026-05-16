import type { Cadence } from "@/lib/onboarding/state";

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
      <div className="flex gap-1 rounded-lg bg-slate-100 p-0.5">
        <button
          type="button"
          className={`flex-1 rounded-md px-4 py-1.5 text-xs font-medium transition-colors ${
            cadence === "monthly"
              ? "border border-slate-200 bg-white text-slate-900 shadow-sm"
              : "text-slate-500"
          }`}
          onClick={() => onCadenceChange("monthly")}
        >
          monthly
        </button>
        <button
          type="button"
          className={`flex-1 rounded-md px-4 py-1.5 text-xs font-medium transition-colors ${
            cadence === "one_time"
              ? "border border-slate-200 bg-white text-slate-900 shadow-sm"
              : "text-slate-500"
          }`}
          onClick={() => onCadenceChange("one_time")}
        >
          one-time
        </button>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-base text-slate-500">₹</span>
        <input
          type="text"
          inputMode="numeric"
          autoComplete="off"
          placeholder="15,000"
          value={display}
          onChange={(e) => onAmountChange(e.target.value)}
          className="min-w-0 flex-1 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none ring-finnwise-blue focus:ring-2"
          aria-label="Investment amount in rupees"
        />
        <span className="whitespace-nowrap text-xs text-slate-500">
          {cadence === "monthly" ? "/ month" : "one-time"}
        </span>
      </div>
      <p className="text-xs text-slate-400">minimum ₹1,000 · no maximum</p>
    </div>
  );
}
