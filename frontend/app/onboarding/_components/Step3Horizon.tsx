import type { Horizon } from "@/lib/onboarding/state";

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
          <button
            key={cell.id}
            type="button"
            onClick={() => onSelect(cell.id)}
            className={`rounded-xl border px-4 py-3 text-left transition-colors ${
              isSelected
                ? "border-[1.5px] border-finnwise-blue bg-finnwise-blue-tint"
                : "border border-slate-200 bg-white hover:border-finnwise-blue/60"
            }`}
          >
            <p className="text-sm font-semibold text-slate-900">{cell.title}</p>
            <p className="mt-1 font-mono text-[10px] uppercase tracking-wide text-slate-500">
              {cell.subtitle}
            </p>
          </button>
        );
      })}
    </div>
  );
}
