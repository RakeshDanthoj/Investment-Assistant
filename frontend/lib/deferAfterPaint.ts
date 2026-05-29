/**
 * Defer work until after first paint (PC-1.2 / P2.5-S4).
 * Uses requestIdleCallback when available, otherwise setTimeout(0).
 */
export function deferAfterPaint<T = void>(fn: () => T | Promise<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    const run = () => {
      void Promise.resolve(fn()).then(resolve, reject);
    };
    if (typeof requestIdleCallback === "function") {
      requestIdleCallback(() => run(), { timeout: 2000 });
    } else {
      setTimeout(run, 0);
    }
  });
}
