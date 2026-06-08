import { isLocalDevHost, tryLocalDevLogin } from "./local-dev-login";

describe("isLocalDevHost", () => {
  it("returns true on localhost hostnames", () => {
    expect(isLocalDevHost()).toBe(true);
  });
});

describe("tryLocalDevLogin", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it("returns session tokens when the backend accepts credentials", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        access_token: "access",
        refresh_token: "refresh",
      }),
    }) as typeof fetch;

    const session = await tryLocalDevLogin("owner@example.com", "localdev123");
    expect(session).toEqual({
      access_token: "access",
      refresh_token: "refresh",
    });
  });

  it("returns null when the backend rejects credentials", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "Invalid email or password" }),
    }) as typeof fetch;

    const session = await tryLocalDevLogin("owner@example.com", "wrong");
    expect(session).toBeNull();
  });
});
