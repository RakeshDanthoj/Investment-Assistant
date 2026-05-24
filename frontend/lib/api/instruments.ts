import { describeFetchFailure, describeHttpFailure, getApiBaseUrl } from "@/lib/api";

export type InstrumentSearchResult = {
  instrument_id: string;
  display_name: string;
  exchange: string;
};

export async function searchInstruments(query: string): Promise<InstrumentSearchResult[]> {
  const q = query.trim();
  if (!q) return [];
  const base = getApiBaseUrl();
  const params = new URLSearchParams({ q });
  const url = `${base}/api/instruments/search?${params}`;
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(describeHttpFailure(res.status, text, "search instruments"));
    }
    const json = (await res.json()) as { results?: InstrumentSearchResult[] };
    return json.results ?? [];
  } catch (e) {
    throw new Error(describeFetchFailure(e, "search instruments"));
  }
}
