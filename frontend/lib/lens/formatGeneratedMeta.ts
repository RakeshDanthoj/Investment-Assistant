/** Meta row: "Generated in Xs · Date" (P2-S8). */

export function formatGeneratedMeta(
  generationSeconds: number | null | undefined,
  isoDate: string,
): string {
  const date = new Date(isoDate);
  const dateLabel = date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
  if (generationSeconds == null || generationSeconds < 1) {
    return dateLabel;
  }
  return `Generated in ${generationSeconds}s · ${dateLabel}`;
}
