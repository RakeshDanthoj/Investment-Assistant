/**
 * Stable date/time formatting for SSR + client (P2-S12 / PC-1.1).
 * Fixed locale and UTC timezone avoid hydration mismatches from `undefined` locale.
 */

const LOCALE = "en-IN";
const TIME_ZONE = "UTC";

export function formatFinnwiseTime(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat(LOCALE, {
      timeZone: TIME_ZONE,
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function formatFinnwiseDateTime(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat(LOCALE, {
      timeZone: TIME_ZONE,
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function formatFinnwiseDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat(LOCALE, {
      timeZone: TIME_ZONE,
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}
