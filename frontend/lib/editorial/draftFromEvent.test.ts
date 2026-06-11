import { parseDraftFromEventError } from "./draftFromEvent";

describe("parseDraftFromEventError", () => {
  it("maps critical_facts_held to editor-friendly copy", () => {
    const message = parseDraftFromEventError(
      423,
      JSON.stringify({
        detail: {
          code: "critical_facts_held",
          message: "INR/USD unavailable",
        },
      }),
    );

    expect(message).toMatch(/critical market facts are unavailable/i);
  });

  it("maps llm_daily_cap to editor-friendly copy", () => {
    const message = parseDraftFromEventError(
      429,
      JSON.stringify({
        detail: { code: "llm_daily_cap", message: "cap reached" },
      }),
    );

    expect(message).toMatch(/daily llm card limit/i);
  });

  it("maps llm_quota_exceeded to editor-friendly copy", () => {
    const message = parseDraftFromEventError(
      429,
      JSON.stringify({
        detail: { code: "llm_quota_exceeded", message: "quota" },
      }),
    );

    expect(message).toMatch(/nvidia api quota exceeded/i);
  });

  it("falls back to string detail bodies", () => {
    const message = parseDraftFromEventError(
      404,
      JSON.stringify({ detail: "Event missing" }),
    );

    expect(message).toBe("Event missing");
  });
});
