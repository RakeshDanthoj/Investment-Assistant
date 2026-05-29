import { formatFinnwiseDate } from "@/lib/format/dateTime";

/** Meta row: "Generated in Xs · Date" (P2-S8 / PC-1.1). */

export function formatGeneratedMeta(
  generationSeconds: number | null | undefined,
  isoDate: string,
): string {
  const dateLabel = formatFinnwiseDate(isoDate);
  if (generationSeconds == null || generationSeconds < 1) {
    return dateLabel;
  }
  return `Generated in ${generationSeconds}s · ${dateLabel}`;
}
