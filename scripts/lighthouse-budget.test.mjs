#!/usr/bin/env node
/**
 * Smoke tests for Lighthouse budget assertions (P1.5-S9.5).
 */

import assert from "node:assert/strict";
import { assertBudgets, detectAuditFailure, extractMetrics } from "./lighthouse-budget.mjs";

const passing = {
  categories: { performance: { score: 0.92 } },
  audits: {
    "total-blocking-time": { numericValue: 150 },
    "speed-index": { numericValue: 3000 },
  },
};

const failingTbt = {
  categories: { performance: { score: 0.95 } },
  audits: {
    "total-blocking-time": { numericValue: 250 },
    "speed-index": { numericValue: 3000 },
  },
};

const metricsPass = extractMetrics(passing);
assert.equal(metricsPass.performanceScore, 92);
assert.equal(assertBudgets("pass", metricsPass), null);

const metricsFail = extractMetrics(failingTbt);
const violation = assertBudgets("fail", metricsFail);
assert.ok(violation);
assert.ok(violation.failures.some((f) => f.includes("TBT")));

const auditFailed = {
  runtimeError: {
    message: "Lighthouse was unable to reliably load the page you requested. (Status code: 404)",
  },
  categories: { performance: { score: null } },
  audits: {},
};
const metricsAuditFail = extractMetrics(auditFailed);
assert.equal(metricsAuditFail.performanceScore, null);
assert.equal(
  detectAuditFailure(auditFailed),
  "Lighthouse was unable to reliably load the page you requested. (Status code: 404)",
);
const auditViolation = assertBudgets("404", metricsAuditFail);
assert.ok(auditViolation?.failures.some((f) => f.includes("audit failed")));

console.log("lighthouse-budget.test.mjs: all assertions passed");
