import {
  fetchSignalFiredCardId,
  resetNotificationAlertCacheForTests,
} from "./notificationAlert";

describe("fetchSignalFiredCardId", () => {
  beforeEach(() => {
    resetNotificationAlertCacheForTests();
  });

  it("dedupes concurrent requests", async () => {
    let fetchCount = 0;
    const fetchImpl = jest.fn(async () => {
      fetchCount += 1;
      await new Promise((resolve) => setTimeout(resolve, 10));
      return {
        ok: true,
        json: async () => ({
          items: [{ card_id: "card-1", kind: "signal_fired" }],
        }),
      } as Response;
    });

    const [a, b] = await Promise.all([
      fetchSignalFiredCardId(fetchImpl, "/api/notifications?limit=50", "token"),
      fetchSignalFiredCardId(fetchImpl, "/api/notifications?limit=50", "token"),
    ]);

    expect(a).toBe("card-1");
    expect(b).toBe("card-1");
    expect(fetchCount).toBe(1);
  });
});
