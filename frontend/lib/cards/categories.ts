export type CategoryOption = { id: string; label: string };

/** Matches backend `event_category` / PRD pills. */
export const PULSE_CATEGORY_OPTIONS: readonly CategoryOption[] = [
  { id: "macro", label: "Macro" },
  { id: "rbi_policy", label: "RBI policy" },
  { id: "regulatory", label: "Regulatory" },
  { id: "india_specific", label: "India-specific" },
  { id: "geopolitical", label: "Geopolitical" },
  { id: "budget", label: "Budget" },
];

export function categoryLabel(id: string): string {
  return PULSE_CATEGORY_OPTIONS.find((c) => c.id === id)?.label ?? id;
}

export function categoryPillClass(category: string): string {
  switch (category) {
    case "macro":
      return "bg-finnwise-measured-bg text-finnwise-blue";
    case "rbi_policy":
      return "bg-finnwise-modelled-bg text-finnwise-green";
    case "regulatory":
      return "bg-finnwise-judged-bg text-finnwise-amber";
    case "india_specific":
      return "bg-slate-100 text-slate-700";
    case "geopolitical":
      return "bg-[#FEE2E2] text-finnwise-red";
    case "budget":
      return "bg-[#F0F4FF] text-finnwise-blue";
    default:
      return "bg-slate-100 text-slate-600";
  }
}
