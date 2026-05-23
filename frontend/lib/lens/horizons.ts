import type { Horizon } from "@/lib/onboarding/state";

export const LENS_HORIZON_OPTIONS: { id: Horizon; label: string }[] = [
  { id: "under_1y", label: "Under 1 year" },
  { id: "1_3y", label: "1 to 3 years" },
  { id: "3_7y", label: "3 to 7 years" },
  { id: "7_plus", label: "7 years or more" },
];

export function horizonLabel(id: Horizon | null | undefined): string {
  if (!id) return "";
  return LENS_HORIZON_OPTIONS.find((o) => o.id === id)?.label ?? id;
}
