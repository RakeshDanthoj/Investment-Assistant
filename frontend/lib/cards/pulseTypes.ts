export type ConfidenceTier = {
  tier: string;
  label: string;
};

export type PulseInstrument = {
  instrument_id: string;
  signal_type: string;
};

export type PulseCard = {
  id: string;
  headline: string;
  event_context: string;
  category: string;
  lifecycle_state: string;
  direction_confidence: ConfidenceTier;
  magnitude_confidence: ConfidenceTier;
  instruments: PulseInstrument[];
  insight_excerpt: string;
  last_reviewed_at: string | null;
  created_at: string | null;
  event_id: string;
};

export type PulseFeedResponse = {
  cards: PulseCard[];
  fog_of_war: boolean;
  profile: {
    horizon: string;
    mode: string;
    effective_horizon: string | null;
  } | null;
  last_updated: string;
  counts: number;
};
