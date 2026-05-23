import { CardDetailFetchError, fetchCardDetail, getServerApiBaseUrl } from "@/lib/api/server";

describe("fetchCardDetail", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.example.com";
    global.fetch = jest.fn();
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    jest.resetAllMocks();
  });

  it("uses direct API base URL on the server", () => {
    expect(getServerApiBaseUrl()).toBe("https://api.example.com");
  });

  it("returns parsed card detail for current view", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ card_id: "abc", view: "current", title: "Test card" }),
    });

    const data = await fetchCardDetail("abc", "current");

    expect(data.title).toBe("Test card");
    expect(global.fetch).toHaveBeenCalledWith(
      "https://api.example.com/api/cards/abc?view=current",
      { next: { revalidate: 60 } },
    );
  });

  it("throws CardDetailFetchError on 404", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 404,
      text: async () => "Card not found",
    });

    await expect(fetchCardDetail("missing")).rejects.toMatchObject({
      name: "CardDetailFetchError",
      status: 404,
      message: "Card not found",
    });
  });
});

describe("CardDetailFetchError", () => {
  it("preserves HTTP status", () => {
    const error = new CardDetailFetchError("fail", 503);
    expect(error).toBeInstanceOf(Error);
    expect(error.status).toBe(503);
  });
});
