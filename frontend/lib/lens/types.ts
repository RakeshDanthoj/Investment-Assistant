import type { Horizon } from "@/lib/onboarding/state";

export type LensQueryStatus = "queued" | "running" | "done" | "failed";

export type LensQueryItem = {
  id: string;
  query: string;
  sector: string | null;
  horizon: Horizon | null;
  status: LensQueryStatus;
  card_id: string | null;
  created_at: string;
};

export type LensQueriesResponse = {
  items: LensQueryItem[];
};

export type LensQueryCreateResponse = {
  id: string;
  status: LensQueryStatus;
};
