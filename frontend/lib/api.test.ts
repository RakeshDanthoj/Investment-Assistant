import { describeFetchFailure, describeHttpFailure, getApiBaseUrl, getLongRunningApiBaseUrl } from "./api";

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

describe("getLongRunningApiBaseUrl", () => {
  const prev = process.env.NEXT_PUBLIC_API_BASE_URL;

  afterEach(() => {
    if (prev === undefined) delete process.env.NEXT_PUBLIC_API_BASE_URL;
    else process.env.NEXT_PUBLIC_API_BASE_URL = prev;
  });

  it("returns configured API origin for direct long-running calls", () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.example.com/";
    expect(getLongRunningApiBaseUrl()).toBe("https://api.example.com");
  });

  it("defaults to loopback when unset", () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    expect(getLongRunningApiBaseUrl()).toBe("http://127.0.0.1:8000");
  });
});

describe("describeFetchFailure", () => {
  it("maps Failed to fetch to actionable guidance", () => {
    const msg = describeFetchFailure(new Error("Failed to fetch"), "save your profile");
    expect(msg).toContain("save your profile");
    expect(msg).toContain("NEXT_PUBLIC_API_BASE_URL");
  });
});

describe("describeHttpFailure", () => {
  it("maps Next.js HTML 404 pages to proxy guidance", () => {
    const html = "<!DOCTYPE html><html><title>404: This page could not be found.</title></html>";
    const msg = describeHttpFailure(404, html, "load the feed");
    expect(msg).toContain("load the feed");
    expect(msg).toContain("NEXT_PUBLIC_API_BASE_URL");
    expect(msg).not.toContain("<!DOCTYPE");
  });

  it("returns JSON detail when present", () => {
    const msg = describeHttpFailure(503, '{"detail":"Database unavailable"}', "load the feed");
    expect(msg).toBe("Database unavailable");
  });
});
