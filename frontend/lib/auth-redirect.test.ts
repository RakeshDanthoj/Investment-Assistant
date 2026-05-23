import { buildAuthCallbackUrl, resolveSiteOrigin } from "@/lib/auth-redirect";

describe("resolveSiteOrigin", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
    delete process.env.NEXT_PUBLIC_SITE_URL;
    delete process.env.VERCEL_URL;
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it("prefers NEXT_PUBLIC_SITE_URL", () => {
    process.env.NEXT_PUBLIC_SITE_URL = "https://app.example.com/";
    expect(resolveSiteOrigin({ windowOrigin: "http://localhost:3000" })).toBe(
      "https://app.example.com",
    );
  });

  it("uses forwarded host on the server", () => {
    expect(
      resolveSiteOrigin({
        forwardedHost: "investment-assistant-frontend.vercel.app",
        forwardedProto: "https",
      }),
    ).toBe("https://investment-assistant-frontend.vercel.app");
  });

  it("falls back to window origin in the browser", () => {
    expect(resolveSiteOrigin({ windowOrigin: "https://preview.vercel.app" })).toBe(
      "https://preview.vercel.app",
    );
  });
});

describe("buildAuthCallbackUrl", () => {
  it("builds callback url with encoded next path", () => {
    process.env.NEXT_PUBLIC_SITE_URL = "https://app.example.com";
    expect(buildAuthCallbackUrl("/pulse")).toBe(
      "https://app.example.com/callback?next=%2Fpulse",
    );
  });
});
