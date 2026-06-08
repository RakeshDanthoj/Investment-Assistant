/**
 * Session-only holdings store (P2-S9).
 * Persisted in sessionStorage with HMAC keyed by onboarding session id — never IndexedDB/cookies.
 */

import { buildPersonalisationToken, hmacSha256Hex } from "@/lib/personalisation/crypto";
import { syncSessionCookies } from "@/lib/sessionCookies.shared";
import { getStoredSessionId } from "@/lib/sessionProfile";

export const HOLDINGS_STORAGE_KEY = "finnwise_session_holdings_v1";
export const HOLDINGS_CHANGED_EVENT = "finnwise-holdings-changed";

export type SessionHolding = {
  instrumentId: string;
  displayName: string;
  exchange?: string;
};

type SealedPayload = {
  v: 1;
  holdings: SessionHolding[];
  sig: string;
};

function sessionSealKey(): string | null {
  return getStoredSessionId();
}

function emitHoldingsChanged(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(HOLDINGS_CHANGED_EVENT));
}

async function sealHoldings(holdings: SessionHolding[], sessionKey: string): Promise<string> {
  const body = JSON.stringify({ holdings });
  const sig = await hmacSha256Hex(sessionKey, body);
  const payload: SealedPayload = { v: 1, holdings, sig };
  return JSON.stringify(payload);
}

async function unsealHoldings(raw: string, sessionKey: string): Promise<SessionHolding[] | null> {
  try {
    const parsed = JSON.parse(raw) as SealedPayload;
    if (parsed.v !== 1 || !Array.isArray(parsed.holdings) || typeof parsed.sig !== "string") {
      return null;
    }
    const body = JSON.stringify({ holdings: parsed.holdings });
    const expected = await hmacSha256Hex(sessionKey, body);
    if (expected !== parsed.sig) return null;
    return parsed.holdings.filter(
      (h) =>
        h &&
        typeof h.instrumentId === "string" &&
        h.instrumentId.trim() &&
        typeof h.displayName === "string",
    );
  } catch {
    return null;
  }
}

export async function saveSessionHoldings(holdings: SessionHolding[]): Promise<void> {
  if (typeof window === "undefined") return;
  const sessionKey = sessionSealKey();
  if (!sessionKey) return;
  const sealed = await sealHoldings(holdings, sessionKey);
  window.sessionStorage.setItem(HOLDINGS_STORAGE_KEY, sealed);
  emitHoldingsChanged();
  const token = await buildPersonalisationToken(holdings.map((h) => h.instrumentId));
  void syncSessionCookies({ personalisationToken: token });
}

export async function getSessionHoldings(): Promise<SessionHolding[]> {
  if (typeof window === "undefined") return [];
  const sessionKey = sessionSealKey();
  if (!sessionKey) return [];
  const raw = window.sessionStorage.getItem(HOLDINGS_STORAGE_KEY);
  if (!raw) return [];
  const holdings = await unsealHoldings(raw, sessionKey);
  return holdings ?? [];
}

export async function clearSessionHoldings(): Promise<void> {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(HOLDINGS_STORAGE_KEY);
  emitHoldingsChanged();
  void syncSessionCookies({ personalisationToken: null });
}

export async function getPersonalisationToken(): Promise<string | null> {
  const holdings = await getSessionHoldings();
  if (!holdings.length) return null;
  return buildPersonalisationToken(holdings.map((h) => h.instrumentId));
}

export function intersectHoldingsWithInstruments<
  T extends { instrument_id: string; signal_label?: string; signal_type?: string },
>(holdings: SessionHolding[], instruments: T[]): Array<T & { holdingDisplayName: string }> {
  const byId = new Map(holdings.map((h) => [h.instrumentId.toUpperCase(), h]));
  const out: Array<T & { holdingDisplayName: string }> = [];
  for (const row of instruments) {
    const key = row.instrument_id.toUpperCase();
    const holding = byId.get(key);
    if (holding) {
      out.push({ ...row, holdingDisplayName: holding.displayName || holding.instrumentId });
    }
  }
  return out;
}
