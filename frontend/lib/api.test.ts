import { describeFetchFailure, getApiBaseUrl } from "./api";

describe("getApiBaseUrl", () => {
  const prev = process.env.NEXT_PUBLIC_API_BASE_URL;

  afterEach(() => {
    if (prev === undefined) delete process.env.NEXT_PUBLIC_API_BASE_URL;
    else process.env.NEXT_PUBLIC_API_BASE_URL = prev;
  });

  it("defaults to loopback when unset (server)", () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    expect(getApiBaseUrl()).toBe("http://127.0.0.1:8000");
  });
});

describe("describeFetchFailure", () => {
  it("maps Failed to fetch to actionable guidance", () => {
    const msg = describeFetchFailure(new Error("Failed to fetch"), "save your profile");
    expect(msg).toContain("save your profile");
    expect(msg).toContain("NEXT_PUBLIC_API_BASE_URL");
  });
});
