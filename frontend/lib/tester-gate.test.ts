import {
  pathRequiresTesterAcceptance,
  shouldRedirectToTesterBriefing,
} from "./tester-gate";

describe("tester gate", () => {
  it("requires acceptance on app surfaces but not onboarding or briefing", () => {
    expect(pathRequiresTesterAcceptance("/pulse")).toBe(true);
    expect(pathRequiresTesterAcceptance("/thread/card-1")).toBe(true);
    expect(pathRequiresTesterAcceptance("/admin/queue")).toBe(true);
    expect(pathRequiresTesterAcceptance("/onboarding")).toBe(false);
    expect(pathRequiresTesterAcceptance("/tester-briefing")).toBe(false);
    expect(pathRequiresTesterAcceptance("/")).toBe(false);
  });

  it("redirects signed-in users without acceptance on gated paths", () => {
    expect(shouldRedirectToTesterBriefing("/pulse", true, false)).toBe(true);
    expect(shouldRedirectToTesterBriefing("/onboarding", true, false)).toBe(false);
    expect(shouldRedirectToTesterBriefing("/pulse", false, false)).toBe(false);
    expect(shouldRedirectToTesterBriefing("/pulse", true, true)).toBe(false);
  });
});
