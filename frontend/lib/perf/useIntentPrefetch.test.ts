import {
  resetIntentPrefetchStateForTests,
  useIntentPrefetch,
} from "@/lib/perf/useIntentPrefetch";
import { act, renderHook } from "@testing-library/react";

describe("useIntentPrefetch", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    resetIntentPrefetchStateForTests();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    resetIntentPrefetchStateForTests();
  });

  it("does not fetch before dwell completes", () => {
    const fetchFn = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() => useIntentPrefetch());

    act(() => {
      result.current.onPointerEnter("banking", fetchFn);
    });

    act(() => {
      jest.advanceTimersByTime(249);
    });

    expect(fetchFn).not.toHaveBeenCalled();
  });

  it("starts fetch after 250ms dwell", async () => {
    const fetchFn = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() => useIntentPrefetch());

    act(() => {
      result.current.onPointerEnter("banking", fetchFn);
    });

    await act(async () => {
      jest.advanceTimersByTime(250);
      await Promise.resolve();
    });

    expect(fetchFn).toHaveBeenCalledTimes(1);
    expect(fetchFn.mock.calls[0][0]).toBeInstanceOf(AbortSignal);
  });

  it("aborts prior fetch when focus moves to another target", async () => {
    const bankingController = { current: null as AbortController | null };
    const bankingFetch = jest.fn((signal: AbortSignal) => {
      bankingController.current = { signal } as unknown as AbortController;
      return new Promise<void>(() => {});
    });
    const itFetch = jest.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() => useIntentPrefetch());

    act(() => {
      result.current.onPointerEnter("banking", bankingFetch);
    });

    await act(async () => {
      jest.advanceTimersByTime(250);
      await Promise.resolve();
    });

    expect(bankingFetch).toHaveBeenCalledTimes(1);

    act(() => {
      result.current.onPointerEnter("it", itFetch);
    });

    await act(async () => {
      jest.advanceTimersByTime(250);
      await Promise.resolve();
    });

    expect(bankingFetch.mock.calls[0][0].aborted).toBe(true);
    expect(itFetch).toHaveBeenCalledTimes(1);
  });

  it("clears dwell timer on pointer leave without fetching", () => {
    const fetchFn = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() => useIntentPrefetch());

    act(() => {
      result.current.onPointerEnter("banking", fetchFn);
      result.current.onPointerLeave();
    });

    act(() => {
      jest.advanceTimersByTime(250);
    });

    expect(fetchFn).not.toHaveBeenCalled();
  });

  it("skips fetch when target was recently prefetched", async () => {
    const fetchFn = jest.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() => useIntentPrefetch());

    act(() => {
      result.current.onPointerEnter("banking", fetchFn);
    });

    await act(async () => {
      jest.advanceTimersByTime(250);
      await Promise.resolve();
    });

    expect(fetchFn).toHaveBeenCalledTimes(1);

    act(() => {
      result.current.onPointerEnter("banking", fetchFn);
    });

    await act(async () => {
      jest.advanceTimersByTime(250);
      await Promise.resolve();
    });

    expect(fetchFn).toHaveBeenCalledTimes(1);
  });
});
