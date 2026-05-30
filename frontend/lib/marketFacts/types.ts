export type FreshnessStatus = "fresh" | "stale" | "unavailable";

export type MarketFactChip = {
  fact_id: string;
  label: string;
  display_value: string;
  observed_at: string;
  source: string;
  freshness_status: FreshnessStatus;
};

export type MarketFactsResponse = {
  facts: MarketFactChip[];
  degraded: boolean;
  unavailable_critical: string[];
  has_stale_critical: boolean;
  reference_time: string;
};
