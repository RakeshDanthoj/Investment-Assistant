import type { Horizon } from "@/lib/onboarding/state";

import type { LensQueryItem } from "./types";

export type LensView = "idle" | "submitting" | "loading" | "result" | "error";

export type LensState = {
  view: LensView;
  queryText: string;
  sector: string | null;
  horizon: Horizon | null;
  activeQueryId: string | null;
  activeQuery: LensQueryItem | null;
  errorMessage: string | null;
};

export type LensAction =
  | { type: "SET_QUERY_TEXT"; text: string }
  | { type: "SET_SECTOR"; sector: string | null }
  | { type: "SET_HORIZON"; horizon: Horizon | null }
  | { type: "FILL_EXAMPLE"; text: string; sector?: string }
  | { type: "SUBMIT_START" }
  | { type: "SUBMIT_SUCCESS"; queryId: string }
  | { type: "SUBMIT_ERROR"; message: string }
  | { type: "OPEN_HISTORY"; item: LensQueryItem }
  | { type: "RESET_TO_IDLE" }
  | { type: "HYDRATE_FROM_HASH"; hash: string; history: LensQueryItem[] };

export const LENS_QUERY_MIN_CHARS = 11;

export function initialLensState(): LensState {
  return {
    view: "idle",
    queryText: "",
    sector: null,
    horizon: null,
    activeQueryId: null,
    activeQuery: null,
    errorMessage: null,
  };
}

export function lensHashForState(state: LensState): string {
  if (state.view === "loading" && state.activeQueryId) {
    return `#loading/${state.activeQueryId}`;
  }
  if (state.view === "result" && state.activeQueryId) {
    return `#result/${state.activeQueryId}`;
  }
  return "";
}

export function parseLensHash(hash: string): { view: LensView; queryId: string | null } {
  const trimmed = hash.replace(/^#/, "").trim();
  if (!trimmed) return { view: "idle", queryId: null };

  const [kind, id] = trimmed.split("/");
  if ((kind === "loading" || kind === "result") && id) {
    return { view: kind, queryId: id };
  }
  return { view: "idle", queryId: null };
}

function viewForHistoryItem(item: LensQueryItem): LensView {
  if (item.status === "done") return "result";
  if (item.status === "failed") return "error";
  return "loading";
}

export function lensReducer(state: LensState, action: LensAction): LensState {
  switch (action.type) {
    case "SET_QUERY_TEXT":
      return { ...state, queryText: action.text };
    case "SET_SECTOR":
      return { ...state, sector: action.sector };
    case "SET_HORIZON":
      return { ...state, horizon: action.horizon };
    case "FILL_EXAMPLE":
      return {
        ...state,
        queryText: action.text,
        sector: action.sector ?? state.sector,
        view: "idle",
        errorMessage: null,
      };
    case "SUBMIT_START":
      return { ...state, view: "submitting", errorMessage: null };
    case "SUBMIT_SUCCESS":
      return {
        ...state,
        view: "loading",
        activeQueryId: action.queryId,
        activeQuery: null,
        errorMessage: null,
      };
    case "SUBMIT_ERROR":
      return {
        ...state,
        view: "error",
        errorMessage: action.message,
      };
    case "OPEN_HISTORY": {
      const nextView = viewForHistoryItem(action.item);
      return {
        ...state,
        view: nextView,
        queryText: action.item.query,
        sector: action.item.sector,
        horizon: action.item.horizon,
        activeQueryId: action.item.id,
        activeQuery: action.item,
        errorMessage:
          nextView === "error"
            ? "This query did not complete. Edit and try again."
            : null,
      };
    }
    case "RESET_TO_IDLE":
      return {
        ...state,
        view: "idle",
        activeQueryId: null,
        activeQuery: null,
        errorMessage: null,
      };
    case "HYDRATE_FROM_HASH": {
      const parsed = parseLensHash(action.hash);
      if (!parsed.queryId) {
        return { ...state, view: "idle", activeQueryId: null, activeQuery: null };
      }
      const item = action.history.find((row) => row.id === parsed.queryId);
      if (!item) {
        return {
          ...state,
          view: parsed.view === "result" ? "result" : "loading",
          activeQueryId: parsed.queryId,
        };
      }
      return {
        ...state,
        view: parsed.view === "result" ? "result" : viewForHistoryItem(item),
        queryText: item.query,
        sector: item.sector,
        horizon: item.horizon,
        activeQueryId: item.id,
        activeQuery: item,
      };
    }
    default:
      return state;
  }
}

export function canSubmitLensQuery(text: string): boolean {
  return text.trim().length >= LENS_QUERY_MIN_CHARS;
}
