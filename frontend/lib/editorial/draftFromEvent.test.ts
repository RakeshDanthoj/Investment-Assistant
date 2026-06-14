import { draftFromEventTimeoutMs, parseDraftFromEventError } from "./draftFromEvent";

describe("draftFromEventTimeoutMs", () => {
  const prevPerCall = process.env.NEXT_PUBLIC_LLM_REQUEST_TIMEOUT_SECONDS;
  const prevRetries = process.env.NEXT_PUBLIC_LLM_MAX_RETRIES;
  const prevOverride = process.env.NEXT_PUBLIC_DRAFT_FROM_EVENT_TIMEOUT_MS;

  afterEach(() => {
    if (prevPerCall === undefined) delete process.env.NEXT_PUBLIC_LLM_REQUEST_TIMEOUT_SECONDS;
    else process.env.NEXT_PUBLIC_LLM_REQUEST_TIMEOUT_SECONDS = prevPerCall;
    if (prevRetries === undefined) delete process.env.NEXT_PUBLIC_LLM_MAX_RETRIES;
    else process.env.NEXT_PUBLIC_LLM_MAX_RETRIES = prevRetries;
    if (prevOverride === undefined) delete process.env.NEXT_PUBLIC_DRAFT_FROM_EVENT_TIMEOUT_MS;
    else process.env.NEXT_PUBLIC_DRAFT_FROM_EVENT_TIMEOUT_MS = prevOverride;
  });

  it("defaults to per-call timeout × retries × 5 calls + 45s buffer", () => {
    delete process.env.NEXT_PUBLIC_DRAFT_FROM_EVENT_TIMEOUT_MS;
    delete process.env.NEXT_PUBLIC_LLM_REQUEST_TIMEOUT_SECONDS;
    delete process.env.NEXT_PUBLIC_LLM_MAX_RETRIES;
    expect(draftFromEventTimeoutMs()).toBe(90 * 2 * 5 * 1000 + 45_000);
  });

  it("honours NEXT_PUBLIC_DRAFT_FROM_EVENT_TIMEOUT_MS override", () => {
    process.env.NEXT_PUBLIC_DRAFT_FROM_EVENT_TIMEOUT_MS = "600000";
    expect(draftFromEventTimeoutMs()).toBe(600_000);
  });
});

describe("parseDraftFromEventError", () => {
  it("maps critical_facts_held to editor-friendly copy", () => {
    const message = parseDraftFromEventError(
      423,
      JSON.stringify({
        detail: {
          code: "critical_facts_held",
          message: "critical facts unavailable: fii_net",
          unavailable_critical_facts: ["fii_net"],
        },
      }),
    );

    expect(message).toMatch(/critical market facts are unavailable/i);
    expect(message).toMatch(/fii_net/);
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

  it("maps llm_timeout to editor-friendly copy", () => {
    const message = parseDraftFromEventError(
      504,
      JSON.stringify({
        detail: {
          code: "llm_timeout",
          message: "LLM request timed out after 120s (prompt synthesis.v1).",
        },
      }),
    );

    expect(message).toMatch(/timed out/i);
    expect(message).toMatch(/super-120b/i);
  });

  it("maps FUNCTION_INVOCATION_TIMEOUT to editor-friendly copy", () => {
    const message = parseDraftFromEventError(
      504,
      "An error occurred with your deployment FUNCTION_INVOCATION_TIMEOUT",
    );

    expect(message).toMatch(/timed out in the hosting proxy/i);
    expect(message).toMatch(/30–90 seconds/i);
  });

  it("maps draft_pipeline_failed MMJ errors to editor-friendly copy", () => {
    const message = parseDraftFromEventError(
      422,
      JSON.stringify({
        detail: {
          code: "draft_pipeline_failed",
          message:
            "quantitative sentence missing [MEASURED]/[MODELLED]/[JUDGED] tag: Repo rate reduction of 25 basis points or more",
        },
      }),
    );

    expect(message).toMatch(/missing an editorial/i);
    expect(message).toMatch(/\[MEASURED\]/);
  });

  it("falls back to string detail bodies", () => {
    const message = parseDraftFromEventError(
      404,
      JSON.stringify({ detail: "Event missing" }),
    );

    expect(message).toBe("Event missing");
  });
});
