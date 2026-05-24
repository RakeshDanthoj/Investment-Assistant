import {
  HOLDINGS_STORAGE_KEY,
  clearSessionHoldings,
  getPersonalisationToken,
  getSessionHoldings,
  intersectHoldingsWithInstruments,
  saveSessionHoldings,
} from "@/lib/personalisation/sessionHoldings";
import { setStoredSessionId } from "@/lib/sessionProfile";

describe("sessionHoldings", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    window.localStorage.clear();
    setStoredSessionId("test-session-abc");
  });

  it("persists holdings only in sessionStorage with HMAC seal", async () => {
    await saveSessionHoldings([
      { instrumentId: "HDFCBANK", displayName: "HDFC Bank Ltd" },
    ]);
    expect(window.sessionStorage.getItem(HOLDINGS_STORAGE_KEY)).toBeTruthy();
    expect(window.localStorage.getItem(HOLDINGS_STORAGE_KEY)).toBeNull();

    const loaded = await getSessionHoldings();
    expect(loaded).toEqual([{ instrumentId: "HDFCBANK", displayName: "HDFC Bank Ltd" }]);
  });

  it("rejects tampered sessionStorage payload", async () => {
    await saveSessionHoldings([{ instrumentId: "TCS", displayName: "Tata Consultancy" }]);
    const raw = window.sessionStorage.getItem(HOLDINGS_STORAGE_KEY)!;
    const tampered = raw.replace("TCS", "RELIANCE");
    window.sessionStorage.setItem(HOLDINGS_STORAGE_KEY, tampered);
    await expect(getSessionHoldings()).resolves.toEqual([]);
  });

  it("derives opaque personalisation token without embedding raw tickers", async () => {
    await saveSessionHoldings([
      { instrumentId: "HDFCBANK", displayName: "HDFC Bank Ltd" },
      { instrumentId: "icicibank", displayName: "ICICI Bank" },
    ]);
    const token = await getPersonalisationToken();
    expect(token).toMatch(/^v1:[a-f0-9]+(\.[a-f0-9]+)?$/);
    expect(token).not.toContain("HDFCBANK");
    expect(token).not.toContain("ICICIBANK");
  });

  it("clear removes session holdings", async () => {
    await saveSessionHoldings([{ instrumentId: "SBIN", displayName: "SBI" }]);
    await clearSessionHoldings();
    await expect(getSessionHoldings()).resolves.toEqual([]);
    await expect(getPersonalisationToken()).resolves.toBeNull();
  });

  it("intersectHoldingsWithInstruments matches case-insensitively", () => {
    const holdings = [{ instrumentId: "hdfcbank", displayName: "HDFC Bank Ltd" }];
    const instruments = [
      { instrument_id: "HDFCBANK", signal_label: "Headwind signal" },
      { instrument_id: "TCS", signal_label: "Watch" },
    ];
    const hits = intersectHoldingsWithInstruments(holdings, instruments);
    expect(hits).toHaveLength(1);
    expect(hits[0].holdingDisplayName).toBe("HDFC Bank Ltd");
  });
});
