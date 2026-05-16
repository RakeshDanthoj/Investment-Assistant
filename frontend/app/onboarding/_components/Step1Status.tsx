import type { InvestmentStatus } from "@/lib/onboarding/state";

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
          <button
            key={opt.id}
            type="button"
            onClick={() => onSelect(opt.id)}
            className={`w-full rounded-xl border px-5 py-3.5 text-left transition-colors ${
              isSelected
                ? "border-[1.5px] border-finnwise-blue bg-finnwise-blue-tint"
                : "border border-slate-200 bg-white hover:border-finnwise-blue/60"
            } `}
          >
            <p className="text-sm font-medium text-slate-900">{opt.title}</p>
            <span className="mt-1 block text-xs text-slate-500">{opt.subtitle}</span>
          </button>
        );
      })}
    </div>
  );
}
