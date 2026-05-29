import { deferAfterPaint } from "./deferAfterPaint";

describe("deferAfterPaint", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("runs deferred work on the next macrotask when idle callback is unavailable", async () => {
    const original = global.requestIdleCallback;
    // @ts-expect-error test shim
    delete global.requestIdleCallback;

    const fn = jest.fn().mockResolvedValue("done");
    const pending = deferAfterPaint(fn);

    expect(fn).not.toHaveBeenCalled();
    jest.runOnlyPendingTimers();
    await expect(pending).resolves.toBe("done");
    expect(fn).toHaveBeenCalledTimes(1);

    global.requestIdleCallback = original;
  });
});
