/** Formats a 0..1 score as a percentage. A metric that could not be computed shows "n/a", never "0%". */
export function formatMetric(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "n/a";
  return `${Math.round(value * 100)}%`;
}
