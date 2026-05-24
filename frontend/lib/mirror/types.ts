export type MirrorStatus = "resolved" | "active" | "pending";

export type AccuracyLevel = "mechanism" | "business" | "market";

export type AccuracyGrade = "correct" | "partial" | "incorrect" | "monitoring" | null;

export type MirrorPrediction = {
  id: string;
  card_id: string;
  prediction_text: string;
  logged_at: string;
  mechanism_accuracy: AccuracyGrade;
  business_accuracy: AccuracyGrade;
  market_accuracy: AccuracyGrade;
  gap_insight: string | null;
  card_title: string;
  event_title: string;
  event_category: string;
  lifecycle_state: string;
  mirror_status: MirrorStatus;
  linked_map_module_id: string | null;
  linked_map_module_name: string | null;
};

export type MirrorPredictionsResponse = {
  items: MirrorPrediction[];
  limit: number;
  offset: number;
};

export type MirrorUnreadNotification = {
  id: string;
  card_id: string;
  prediction_id: string;
  event_title: string;
  card_title: string;
  resolved_at: string | null;
  created_at: string;
};

export type MirrorUnreadNotificationsResponse = {
  count: number;
  items: MirrorUnreadNotification[];
};

export type MirrorStatsResponse = {
  total_predictions: number;
  mechanism_accuracy_pct: number | null;
  market_accuracy_pct: number | null;
  reasoning_gaps_found: number;
  mechanism_tone: "strong" | "developing" | "neutral";
  market_tone: "strong" | "developing" | "neutral";
};

export type StreakGrade = "correct" | "partial" | "incorrect" | "monitoring" | "empty";

export type StreakLetter = "M" | "P" | "✗" | "·" | "–";

export type StreakCell = {
  letter: StreakLetter;
  grade: StreakGrade;
};

export type MirrorStreakResponse = {
  cells: StreakCell[];
  mechanism_accuracy_pct: number | null;
  market_accuracy_pct: number | null;
  summary: string;
};

export type MirrorReasoningGap = {
  gap_type: string;
  gap_name: string;
  pattern_explanation: string;
  linked_map_module_id: string;
  linked_map_module_name: string;
};

export type MirrorReasoningGapsResponse = {
  items: MirrorReasoningGap[];
  insufficient_history: boolean;
};

export const MIRROR_FILTER_OPTIONS = [
  { id: "resolved", label: "Resolved" },
  { id: "active", label: "Active" },
  { id: "pending", label: "Pending" },
] as const;
