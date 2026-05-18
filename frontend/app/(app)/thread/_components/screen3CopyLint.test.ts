import { PREDICTION_OPTIONS } from "./PredictionLogger";

const forbidden = /\b(buy|sell|hold)\b|₹\s*\d+/i;

describe("PRD Screen 3 copy lint", () => {
  it("keeps discrete prediction options free of forbidden advisory wording", () => {
    for (const opt of PREDICTION_OPTIONS) {
      expect(opt.toLowerCase()).not.toMatch(forbidden);
    }
  });
});
