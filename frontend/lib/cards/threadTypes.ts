/** GET /api/cards/{id}?view=current|original — Thread surface (P1-S10). */

export type ConfidenceTier = {
  tier: string;
  label: string;
};

export type ContextStep = {
  title: string;
  body: string;
  mmj: string | null;
};

export type EvidenceRow = {
  claim: string;
  source_name: string;
  date_label: string;
  retrieved_at: string | null;
  freshness: "green" | "amber" | "red";
  mmj: string;
};

export type InstrumentDetail = {
  instrument_id: string;
  signal_label: string;
  reasoning: string | null;
  entry_conditions: string[];
  exit_conditions: string[];
};

export type SignalRow = {
  signal_text: string;
  state: string;
};

export type LifecycleStep = {
  slug: string;
  label: string;
  status: "done" | "current" | "future";
};

export type BiasEntry = {
  id: string;
  label: string;
  status: string;
  detail: string;
};

export type CardDetailResponse = {
  view: "current" | "original";
  card_id: string;
  event_id: string;
  title: string;
  event_title: string;
  category: string;
  lifecycle_state: string;
  lifecycle_tracker: LifecycleStep[];
  week_number: number | null;
  direction_confidence: ConfidenceTier;
  magnitude_confidence: ConfidenceTier;
  event_confidence_score: number | null;
  insight_layer: string;
  context_layer: string;
  context_steps: ContextStep[];
  evidence_layer: Record<string, unknown>;
  evidence_rows: EvidenceRow[];
  evidence_markdown: string;
  evidence_macro_stub: string;
  dissenting_view: string;
  framework_behind_this: string;
  instruments: InstrumentDetail[];
  signals: SignalRow[];
  confidence_composition: {
    measured: number;
    modelled: number;
    judged: number;
    counts: { measured: number; modelled: number; judged: number };
  };
  bias_audit: {
    flags: BiasEntry[];
    monitored: BiasEntry[];
    note?: string;
  };
  published_at: string | null;
};
