export type MapSectorSummary = {
  slug: string;
  name: string;
  instrument_count: number;
  cover_accent: string;
};

export type MapSectorListResponse = {
  sectors: MapSectorSummary[];
};

export type MapFactor = {
  slug: string;
  display_name: string;
  sort_order: number;
  description: string;
};

export type MapInstrument = {
  id: string;
  ticker: string;
  display_name: string;
};

export type MapSensitivityCell = {
  sensitivity: number;
  mmj_tag: string;
  source_url: string;
  retrieved_at: string;
  freshness: "green" | "amber" | "red";
};

export type MapModule = {
  id: string;
  sector_slug: string | null;
  title: string;
  body: string;
  linked_gap_types: string[];
  sort_order: number;
};

export type MapSectorSummaryDetail = {
  sector: { slug: string; name: string };
  instrument_count: number;
  modules: MapModule[];
  cover_accent: string;
};

export type MapSectorMatrixResponse = {
  sector: { slug: string; name: string };
  factors: MapFactor[];
  instruments: MapInstrument[];
  instrument_count: number;
  sensitivities: Record<string, Record<string, MapSensitivityCell>>;
};

/** @deprecated Use MapSectorSummaryDetail + MapSectorMatrixResponse */
export type MapSectorDetailResponse = MapSectorSummaryDetail & MapSectorMatrixResponse;
