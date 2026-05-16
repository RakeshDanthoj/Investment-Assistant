import {
  initialOnboardingState,
  onboardingReducer,
  sanitizeAmountInput,
} from "./state";

describe("onboardingReducer", () => {
  it("selects status and advances from step 1", () => {
    let s = initialOnboardingState();
    s = onboardingReducer(s, { type: "SELECT_STATUS", status: "curious" });
    expect(s.investmentStatus).toBe("curious");
    s = onboardingReducer(s, { type: "ADVANCE_FROM_STEP1" });
    expect(s.step).toBe(2);
  });

  it("does not advance from step 1 without status", () => {
    const s = initialOnboardingState();
    const next = onboardingReducer(s, { type: "ADVANCE_FROM_STEP1" });
    expect(next.step).toBe(1);
  });

  it("sanitizes amount and advances from step 2 when valid", () => {
    let s = initialOnboardingState();
    s = onboardingReducer(s, { type: "SELECT_STATUS", status: "starting_fresh" });
    s = onboardingReducer(s, { type: "ADVANCE_FROM_STEP1" });
    s = onboardingReducer(s, { type: "SET_AMOUNT", raw: "15,000x" });
    expect(s.amountInput).toBe("15000");
    s = onboardingReducer(s, { type: "ADVANCE_FROM_STEP2" });
    expect(s.step).toBe(3);
  });

  it("rejects advance from step 2 when amount below minimum", () => {
    let s = initialOnboardingState();
    s = onboardingReducer(s, { type: "SELECT_STATUS", status: "starting_fresh" });
    s = onboardingReducer(s, { type: "ADVANCE_FROM_STEP1" });
    s = onboardingReducer(s, { type: "SET_AMOUNT", raw: "500" });
    s = onboardingReducer(s, { type: "ADVANCE_FROM_STEP2" });
    expect(s.step).toBe(2);
  });

  it("completes submit success path to step 4", () => {
    let s = initialOnboardingState();
    s = onboardingReducer(s, { type: "SELECT_STATUS", status: "has_investments" });
    s = onboardingReducer(s, { type: "ADVANCE_FROM_STEP1" });
    s = onboardingReducer(s, { type: "SET_AMOUNT", raw: "50000" });
    s = onboardingReducer(s, { type: "ADVANCE_FROM_STEP2" });
    s = onboardingReducer(s, { type: "SELECT_HORIZON", horizon: "3_7y" });
    s = onboardingReducer(s, { type: "SUBMIT_SESSION_START" });
    expect(s.submitState).toBe("loading");
    s = onboardingReducer(s, {
      type: "SUBMIT_SESSION_SUCCESS",
      result: {
        mode: "portfolio_protector",
        starting_surface: "pulse",
        rationale: "test",
        session_id: s.sessionId,
        amount_echo: 50000,
      },
    });
    expect(s.step).toBe(4);
    expect(s.apiResult?.mode).toBe("portfolio_protector");
  });

  it("records submit error without changing step", () => {
    let s = initialOnboardingState();
    s = onboardingReducer(s, { type: "SELECT_STATUS", status: "curious" });
    s = onboardingReducer(s, { type: "ADVANCE_FROM_STEP1" });
    s = onboardingReducer(s, { type: "SET_AMOUNT", raw: "2000" });
    s = onboardingReducer(s, { type: "ADVANCE_FROM_STEP2" });
    s = onboardingReducer(s, { type: "SELECT_HORIZON", horizon: "under_1y" });
    s = onboardingReducer(s, { type: "SUBMIT_SESSION_START" });
    s = onboardingReducer(s, { type: "SUBMIT_SESSION_ERROR", message: "network" });
    expect(s.step).toBe(3);
    expect(s.apiError).toBe("network");
  });
});

describe("sanitizeAmountInput", () => {
  it("strips non-digits", () => {
    expect(sanitizeAmountInput("₹12ab34")).toBe("1234");
  });
});
