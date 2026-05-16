export type InvestmentStatus = "starting_fresh" | "has_investments" | "curious";
export type Horizon = "under_1y" | "1_3y" | "3_7y" | "7_plus";
export type Cadence = "monthly" | "one_time";

export type OnboardingStep = 1 | 2 | 3 | 4;

export type SessionApiResult = {
  mode: string;
  starting_surface: string;
  rationale: string;
  session_id: string;
  amount_echo: number | null;
};

export type OnboardingState = {
  step: OnboardingStep;
  investmentStatus: InvestmentStatus | null;
  amountInput: string;
  cadence: Cadence;
  horizon: Horizon | null;
  sessionId: string;
  submitState: "idle" | "loading" | "success" | "error";
  apiError: string | null;
  apiResult: SessionApiResult | null;
};

export type OnboardingAction =
  | { type: "SELECT_STATUS"; status: InvestmentStatus }
  | { type: "SET_AMOUNT"; raw: string }
  | { type: "SET_CADENCE"; cadence: Cadence }
  | { type: "SELECT_HORIZON"; horizon: Horizon }
  | { type: "ADVANCE_FROM_STEP1" }
  | { type: "ADVANCE_FROM_STEP2" }
  | { type: "SUBMIT_SESSION_START" }
  | { type: "SUBMIT_SESSION_SUCCESS"; result: SessionApiResult }
  | { type: "SUBMIT_SESSION_ERROR"; message: string }
  | { type: "RESET_SUBMIT" };

function newSessionId(): string {
  const c = globalThis.crypto;
  if (c && "randomUUID" in c && typeof c.randomUUID === "function") {
    return c.randomUUID();
  }
  return `sess-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

/** Lazy init for `useReducer(…, null, initialOnboardingState)`. */
export function initialOnboardingState(_initArg?: null): OnboardingState {
  return {
    step: 1,
    investmentStatus: null,
    amountInput: "",
    cadence: "monthly",
    horizon: null,
    sessionId: newSessionId(),
    submitState: "idle",
    apiError: null,
    apiResult: null,
  };
}

/**
 * Strip non-digits for amount field (numeric mask).
 */
export function sanitizeAmountInput(raw: string): string {
  return raw.replace(/\D/g, "");
}

export function onboardingReducer(
  state: OnboardingState,
  action: OnboardingAction,
): OnboardingState {
  switch (action.type) {
    case "SELECT_STATUS":
      return { ...state, investmentStatus: action.status };
    case "SET_AMOUNT":
      return { ...state, amountInput: sanitizeAmountInput(action.raw) };
    case "SET_CADENCE":
      return { ...state, cadence: action.cadence };
    case "SELECT_HORIZON":
      return { ...state, horizon: action.horizon };
    case "ADVANCE_FROM_STEP1":
      if (!state.investmentStatus) return state;
      return { ...state, step: 2 };
    case "ADVANCE_FROM_STEP2": {
      if (state.amountInput.length === 0) return state;
      const n = Number(state.amountInput);
      if (!Number.isFinite(n) || n < 1000) return state;
      return { ...state, step: 3 };
    }
    case "SUBMIT_SESSION_START":
      if (!state.investmentStatus || !state.horizon) return state;
      return { ...state, submitState: "loading", apiError: null };
    case "SUBMIT_SESSION_SUCCESS":
      return {
        ...state,
        step: 4,
        submitState: "success",
        apiError: null,
        apiResult: action.result,
      };
    case "SUBMIT_SESSION_ERROR":
      return {
        ...state,
        submitState: "error",
        apiError: action.message,
      };
    case "RESET_SUBMIT":
      return { ...state, submitState: "idle", apiError: null };
    default:
      return state;
  }
}
