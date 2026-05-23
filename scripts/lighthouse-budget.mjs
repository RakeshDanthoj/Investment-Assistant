/**
 * Pure budget helpers for Lighthouse CI (imported by lighthouse.mjs and tests).
 */

/** Phase 1.5 Definition of Done — mobile (baseline traces May 2026). */
export const MOBILE_BUDGETS = {
  minPerformanceScore: 90,
  maxTotalBlockingTimeMs: 200,
  maxSpeedIndexMs: 3400,
};

/**
 * Desktop budgets — Lighthouse desktop "good" band (p10) for TBT/SI.
 * Baselines captured 2026-05-23 (see scripts/README.md); enforced in CI since P1.5-S9b.5.
 */
export const DESKTOP_BUDGETS = {
  minPerformanceScore: 90,
  maxTotalBlockingTimeMs: 150,
  maxSpeedIndexMs: 2400,
};

/** @deprecated Use MOBILE_BUDGETS */
export const BUDGETS = MOBILE_BUDGETS;

export function budgetsForFormFactor(formFactor) {
  return formFactor === "desktop" ? DESKTOP_BUDGETS : MOBILE_BUDGETS;
}

export function extractMetrics(lhr) {
  const audits = lhr.audits ?? {};
  const performanceScore = Math.round((lhr.categories?.performance?.score ?? 0) * 100);
  const tbtMs = audits["total-blocking-time"]?.numericValue ?? NaN;
  const speedIndexMs = audits["speed-index"]?.numericValue ?? NaN;
  return { performanceScore, tbtMs, speedIndexMs };
}

export function assertBudgets(label, metrics, budgets = MOBILE_BUDGETS) {
  const failures = [];
  if (metrics.performanceScore < budgets.minPerformanceScore) {
    failures.push(
      `performance ${metrics.performanceScore} < ${budgets.minPerformanceScore}`,
    );
  }
  if (Number.isFinite(metrics.tbtMs) && metrics.tbtMs >= budgets.maxTotalBlockingTimeMs) {
    failures.push(`TBT ${Math.round(metrics.tbtMs)}ms >= ${budgets.maxTotalBlockingTimeMs}ms`);
  }
  if (
    Number.isFinite(metrics.speedIndexMs) &&
    metrics.speedIndexMs >= budgets.maxSpeedIndexMs
  ) {
    failures.push(
      `Speed Index ${Math.round(metrics.speedIndexMs)}ms >= ${budgets.maxSpeedIndexMs}ms`,
    );
  }
  return failures.length ? { label, failures } : null;
}

export function resolveBudgets(env = process.env, formFactor = "mobile") {
  const defaults = budgetsForFormFactor(formFactor);
  const prefix = formFactor === "desktop" ? "LIGHTHOUSE_DESKTOP_" : "LIGHTHOUSE_";
  return {
    minPerformanceScore: Number(
      env[`${prefix}MIN_PERFORMANCE`] ?? env.LIGHTHOUSE_MIN_PERFORMANCE ?? defaults.minPerformanceScore,
    ),
    maxTotalBlockingTimeMs: Number(
      env[`${prefix}MAX_TBT_MS`] ?? env.LIGHTHOUSE_MAX_TBT_MS ?? defaults.maxTotalBlockingTimeMs,
    ),
    maxSpeedIndexMs: Number(
      env[`${prefix}MAX_SPEED_INDEX_MS`] ??
        env.LIGHTHOUSE_MAX_SPEED_INDEX_MS ??
        defaults.maxSpeedIndexMs,
    ),
  };
}
