import type { CategoryOption } from "@/lib/cards/categories";

export type LensExample = {
  category: CategoryOption["id"];
  categoryLabel: string;
  question: string;
};

/** Static 2×3 grid — PRD §5 Screen 5 example categories. */
export const LENS_EXAMPLES: readonly LensExample[] = [
  {
    category: "macro",
    categoryLabel: "Macro",
    question:
      "What would a US recession mean for Indian IT exporters over the next two years?",
  },
  {
    category: "rbi_policy",
    categoryLabel: "RBI Policy",
    question:
      "If RBI holds rates through monsoon despite sticky food inflation, how do banks reprice credit?",
  },
  {
    category: "regulatory",
    categoryLabel: "Regulatory",
    question:
      "How would tighter mutual-fund risk norms change liquidity for mid-cap industrials?",
  },
  {
    category: "india_specific",
    categoryLabel: "India-specific",
    question:
      "What mechanisms link a weak monsoon to rural two-wheeler demand and fertiliser margins?",
  },
  {
    category: "geopolitical",
    categoryLabel: "Geopolitical",
    question:
      "If Red Sea shipping disruptions persist, which Indian import chains face the widest pass-through?",
  },
  {
    category: "budget",
    categoryLabel: "Budget",
    question:
      "How might a higher capex allocation to railways affect cement and logistics equities?",
  },
] as const;
