import {
  formatFinnwiseDate,
  formatFinnwiseDateTime,
  formatFinnwiseTime,
} from "./dateTime";

describe("formatFinnwiseDateTime", () => {
  it("formats with stable locale and UTC timezone", () => {
    const iso = "2026-05-01T14:30:00.000Z";
    expect(formatFinnwiseTime(iso)).toBe(formatFinnwiseTime(iso));
    expect(formatFinnwiseDateTime(iso)).toBe(formatFinnwiseDateTime(iso));
    expect(formatFinnwiseDate(iso)).toMatch(/2026/);
  });

  it("returns em dash for null", () => {
    expect(formatFinnwiseTime(null)).toBe("—");
    expect(formatFinnwiseDateTime(null)).toBe("—");
  });
});
