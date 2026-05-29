import { formatRelativeDate } from "./relativeDate";

describe("formatRelativeDate", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2026-05-30T12:00:00.000Z"));
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("uses a fixed locale for stable labels", () => {
    const iso = "2026-05-27T12:00:00.000Z";
    expect(formatRelativeDate(iso)).toBe(formatRelativeDate(iso));
    expect(formatRelativeDate(iso)).toMatch(/ago|day/i);
  });

  it("returns empty string for invalid input", () => {
    expect(formatRelativeDate("not-a-date")).toBe("");
  });
});
