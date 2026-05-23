import {
  canSubmitLensQuery,
  initialLensState,
  lensHashForState,
  lensReducer,
  parseLensHash,
} from "./useLensState";

import type { LensQueryItem } from "./types";

const historyItem: LensQueryItem = {
  id: "q-1",
  query: "What would a US recession mean for Indian IT exporters?",
  sector: "macro",
  horizon: "3_7y",
  status: "done",
  card_id: "card-1",
  created_at: "2026-05-20T10:00:00.000Z",
};

describe("lensReducer", () => {
  it("fills example text and keeps idle view", () => {
    const next = lensReducer(initialLensState(), {
      type: "FILL_EXAMPLE",
      text: historyItem.query,
      sector: "macro",
    });
    expect(next.queryText).toBe(historyItem.query);
    expect(next.sector).toBe("macro");
    expect(next.view).toBe("idle");
  });

  it("transitions submit → loading → result via history", () => {
    let state = initialLensState();
    state = lensReducer(state, { type: "SUBMIT_START" });
    expect(state.view).toBe("submitting");

    state = lensReducer(state, { type: "SUBMIT_SUCCESS", queryId: "q-new" });
    expect(state.view).toBe("loading");
    expect(state.activeQueryId).toBe("q-new");

    state = lensReducer(state, { type: "OPEN_HISTORY", item: historyItem });
    expect(state.view).toBe("result");
    expect(state.queryText).toBe(historyItem.query);
  });

  it("opens queued history in loading view", () => {
    const queued: LensQueryItem = { ...historyItem, id: "q-2", status: "queued" };
    const next = lensReducer(initialLensState(), { type: "OPEN_HISTORY", item: queued });
    expect(next.view).toBe("loading");
  });

  it("resets to idle from result", () => {
    let state = lensReducer(initialLensState(), { type: "OPEN_HISTORY", item: historyItem });
    state = lensReducer(state, { type: "RESET_TO_IDLE" });
    expect(state.view).toBe("idle");
    expect(state.activeQueryId).toBeNull();
  });
});

describe("canSubmitLensQuery", () => {
  it("requires more than 10 characters", () => {
    expect(canSubmitLensQuery("1234567890")).toBe(false);
    expect(canSubmitLensQuery("12345678901")).toBe(true);
  });
});

describe("lens hash helpers", () => {
  it("round-trips loading and result hashes", () => {
    const loading = lensReducer(initialLensState(), {
      type: "SUBMIT_SUCCESS",
      queryId: "abc",
    });
    expect(lensHashForState(loading)).toBe("#loading/abc");
    expect(parseLensHash("#loading/abc")).toEqual({ view: "loading", queryId: "abc" });

    const result = lensReducer(initialLensState(), { type: "OPEN_HISTORY", item: historyItem });
    expect(lensHashForState(result)).toBe("#result/q-1");
    expect(parseLensHash("#result/q-1")).toEqual({ view: "result", queryId: "q-1" });
  });
});
