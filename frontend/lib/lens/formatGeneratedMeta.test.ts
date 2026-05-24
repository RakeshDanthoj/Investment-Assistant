import { formatGeneratedMeta } from "./formatGeneratedMeta";

describe("formatGeneratedMeta", () => {
  it("includes generation seconds and formatted date", () => {
    const label = formatGeneratedMeta(42, "2026-05-24T10:00:00.000Z");
    expect(label).toContain("Generated in 42s");
    expect(label).toContain("2026");
  });

  it("omits seconds when unknown", () => {
    const label = formatGeneratedMeta(null, "2026-05-24T10:00:00.000Z");
    expect(label).not.toContain("Generated in");
  });
});
