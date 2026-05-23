#!/usr/bin/env node
/**
 * Lighthouse runner with Phase 1.5 performance budgets (P1.5-S9 / S9b).
 *
 * Mobile (default) and desktop (`--desktop`) profiles audit production
 * /pulse and /thread/{cardId}, then assert form-factor-specific budgets.
 */

import fs from "fs";
import path from "path";
import { createRequire } from "module";
import { fileURLToPath, pathToFileURL } from "url";

import {
  assertBudgets,
  budgetsForFormFactor,
  extractMetrics,
  resolveBudgets,
} from "./lighthouse-budget.mjs";

export { assertBudgets, extractMetrics } from "./lighthouse-budget.mjs";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.join(scriptDir, "..");

const DEFAULT_BASE_URL = "https://investment-assistant-frontend.vercel.app";
const DEFAULT_CARD_ID = "e708b82c-f7c7-45e7-a59b-6b66dac8927a";

/** Empty GitHub secret must not override the published default card id. */
export function resolveThreadCardId(env, defaultId = DEFAULT_CARD_ID) {
  const raw = String(env?.LIGHTHOUSE_THREAD_CARD_ID ?? "").trim();
  return raw || defaultId;
}

function lighthouseAttemptCount(env) {
  const configured = Number.parseInt(String(env.LIGHTHOUSE_CI_ATTEMPTS ?? ""), 10);
  if (Number.isFinite(configured) && configured > 0) return configured;
  return env.CI === "true" ? 2 : 1;
}

function loadEnvLocal() {
  const envPath = path.join(repoRoot, ".env.local");
  if (!fs.existsSync(envPath)) return {};
  const out = {};
  for (const line of fs.readFileSync(envPath, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let val = trimmed.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    out[key] = val;
  }
  return out;
}

function normalizeBaseUrl(raw) {
  return (raw ?? "").trim().replace(/\/$/, "");
}

function parseFormFactor(argv, env) {
  const fromEnv = (env.LIGHTHOUSE_FORM_FACTOR ?? "mobile").trim().toLowerCase();
  if (argv.includes("--desktop")) return "desktop";
  if (argv.includes("--mobile")) return "mobile";
  return fromEnv === "desktop" ? "desktop" : "mobile";
}

function parseArgs(argv) {
  const flags = {
    assertReport: null,
    saveReports: true,
    pages: ["pulse", "thread"],
    formFactor: "mobile",
  };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--no-save") {
      flags.saveReports = false;
    } else if (arg === "--pulse-only") {
      flags.pages = ["pulse"];
    } else if (arg === "--thread-only") {
      flags.pages = ["thread"];
    } else if (arg === "--desktop" || arg === "--mobile") {
      // handled by parseFormFactor
    } else if (arg.startsWith("--assert-report=")) {
      flags.assertReport = arg.slice("--assert-report=".length);
    } else if (arg === "--help" || arg === "-h") {
      flags.help = true;
    }
  }
  return flags;
}

function printHelp() {
  console.log(`Usage: node scripts/lighthouse.mjs [options]

Options:
  --mobile                Mobile emulation and budgets (default)
  --desktop               Desktop emulation and budgets
  --assert-report=<path>  Assert budgets against an existing Lighthouse JSON
  --no-save               Do not write JSON reports to disk
  --pulse-only            Audit /pulse only
  --thread-only           Audit /thread/{cardId} only
  -h, --help              Show this help

Environment:
  LIGHTHOUSE_FORM_FACTOR      mobile | desktop (default: mobile)
  LIGHTHOUSE_BASE_URL         Frontend origin
  LIGHTHOUSE_THREAD_CARD_ID   Published card id for Thread
  LIGHTHOUSE_OUTPUT_DIR       Report directory (default: Page Load Performance/)

  Mobile budgets (default env prefix LIGHTHOUSE_):
    MIN_PERFORMANCE=90  MAX_TBT_MS=200  MAX_SPEED_INDEX_MS=3400

  Desktop budgets (env prefix LIGHTHOUSE_DESKTOP_, falls back to LIGHTHOUSE_):
    MIN_PERFORMANCE=90  MAX_TBT_MS=150  MAX_SPEED_INDEX_MS=2400

  LIGHTHOUSE_SKIP=1           Exit 0 without running
`);
}

function lighthouseConfig(formFactor) {
  if (formFactor === "desktop") {
    return {
      extends: "lighthouse:default",
      settings: {
        onlyCategories: ["performance"],
        formFactor: "desktop",
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          requestLatencyMs: 0,
          downloadThroughputKbps: 0,
          uploadThroughputKbps: 0,
          cpuSlowdownMultiplier: 1,
        },
        screenEmulation: {
          mobile: false,
          width: 1350,
          height: 940,
          deviceScaleFactor: 1,
          disabled: false,
        },
        emulatedUserAgent:
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      },
    };
  }

  return {
    extends: "lighthouse:default",
    settings: {
      onlyCategories: ["performance"],
      formFactor: "mobile",
      throttling: {
        rttMs: 150,
        throughputKbps: 1638.4,
        requestLatencyMs: 562.5,
        downloadThroughputKbps: 1474.56,
        uploadThroughputKbps: 675,
        cpuSlowdownMultiplier: 4,
      },
      screenEmulation: {
        mobile: true,
        width: 412,
        height: 823,
        deviceScaleFactor: 1.75,
        disabled: false,
      },
      emulatedUserAgent:
        "Mozilla/5.0 (Linux; Android 11; moto g power (2022)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    },
  };
}

async function loadLighthouseModules() {
  const searchRoots = [repoRoot, path.join(repoRoot, "frontend")];
  let lastError;
  for (const root of searchRoots) {
    try {
      const pkgJson = path.join(root, "package.json");
      if (!fs.existsSync(pkgJson)) continue;
      const require = createRequire(pkgJson);
      const chromePath = require.resolve("chrome-launcher");
      const lighthousePath = require.resolve("lighthouse");
      const [chromeModule, lighthouseModule] = await Promise.all([
        import(pathToFileURL(chromePath).href),
        import(pathToFileURL(lighthousePath).href),
      ]);
      const launchChrome = chromeModule.launch;
      const lighthouse = lighthouseModule.default ?? lighthouseModule;
      if (typeof launchChrome !== "function" || typeof lighthouse !== "function") {
        throw new Error("chrome-launcher.launch or lighthouse default export missing");
      }
      return { launchChrome, lighthouse };
    } catch (err) {
      lastError = err;
    }
  }
  throw new Error(
    `Could not load lighthouse or chrome-launcher. Run pnpm install at repo root. ${lastError?.message ?? lastError}`,
  );
}

async function runLighthouse(url, chrome, lighthouse, formFactor) {
  const result = await lighthouse(
    url,
    {
      port: chrome.port,
      output: "json",
      logLevel: "error",
    },
    lighthouseConfig(formFactor),
  );
  return result.lhr;
}

function printResult(label, url, metrics) {
  console.log(`\n=== ${label} ===`);
  console.log(url);
  console.log(
    `performance=${metrics.performanceScore}  TBT=${Math.round(metrics.tbtMs)}ms  speed-index=${Math.round(metrics.speedIndexMs)}ms`,
  );
}

async function auditPageOnce({
  label,
  url,
  chrome,
  lighthouse,
  formFactor,
  budgets,
  saveReports,
  outputDir,
  attempt,
  attemptCount,
}) {
  if (attemptCount > 1) {
    console.log(`\nAuditing ${label} (attempt ${attempt}/${attemptCount})…`);
  } else {
    console.log(`\nAuditing ${label}…`);
  }
  const lhr = await runLighthouse(url, chrome, lighthouse, formFactor);
  const metrics = extractMetrics(lhr);

  if (saveReports) {
    const stamp = new Date().toISOString().replace(/[:.]/g, "").slice(0, 15);
    const host = new URL(url).hostname.replace(/\./g, "-");
    const slug = label.toLowerCase().replace(/\s+/g, "-");
    const outPath = path.join(
      outputDir,
      `lighthouse-ci-${formFactor}-${host}-${stamp}-${slug}${attemptCount > 1 ? `-a${attempt}` : ""}.json`,
    );
    fs.mkdirSync(outputDir, { recursive: true });
    fs.writeFileSync(outPath, JSON.stringify(lhr, null, 2));
    console.log(`Saved report: ${outPath}`);
  }

  printResult(label, url, metrics);
  return { violation: assertBudgets(label, metrics, budgets), metrics };
}

async function auditPage(opts) {
  const attemptCount = lighthouseAttemptCount(opts.env ?? {});
  let best = null;

  for (let attempt = 1; attempt <= attemptCount; attempt += 1) {
    const result = await auditPageOnce({ ...opts, attempt, attemptCount });
    if (!result.violation) {
      if (attempt > 1) {
        console.log(`${opts.label}: passed on attempt ${attempt}/${attemptCount}`);
      }
      return null;
    }
    if (
      !best ||
      result.metrics.performanceScore > best.metrics.performanceScore ||
      (result.metrics.performanceScore === best.metrics.performanceScore &&
        result.metrics.tbtMs < best.metrics.tbtMs)
    ) {
      best = result;
    }
  }

  if (attemptCount > 1) {
    console.log(`${opts.label}: failed after ${attemptCount} attempts (Lighthouse variance on CI)`);
  }
  return best?.violation ?? null;
}

async function main() {
  const flags = parseArgs(process.argv);
  if (flags.help) {
    printHelp();
    return;
  }

  const env = { ...loadEnvLocal(), ...process.env };
  if (env.LIGHTHOUSE_SKIP === "1") {
    console.log("LIGHTHOUSE_SKIP=1 — skipping Lighthouse run.");
    return;
  }

  const formFactor = parseFormFactor(process.argv, env);
  const budgets = resolveBudgets(env, formFactor);
  const defaultBudgets = budgetsForFormFactor(formFactor);

  if (flags.assertReport) {
    const reportPath = path.resolve(flags.assertReport);
    const lhr = JSON.parse(fs.readFileSync(reportPath, "utf8"));
    const metrics = extractMetrics(lhr);
    const violation = assertBudgets(path.basename(reportPath), metrics, budgets);
    if (violation) {
      console.error("Budget assertion failed (expected for smoke test):");
      for (const msg of violation.failures) console.error(`  - ${msg}`);
      process.exit(1);
    }
    console.log(`Budget assertions passed for ${reportPath}`);
    return;
  }

  const baseUrl = normalizeBaseUrl(env.LIGHTHOUSE_BASE_URL ?? DEFAULT_BASE_URL);
  const cardId = resolveThreadCardId(env);
  if (String(env.LIGHTHOUSE_THREAD_CARD_ID ?? "").trim() === "") {
    console.log(
      "Note: LIGHTHOUSE_THREAD_CARD_ID unset or empty — using default published card id.",
    );
  }
  const outputDir = path.resolve(
    env.LIGHTHOUSE_OUTPUT_DIR ?? path.join(repoRoot, "Page Load Performance"),
  );

  const targets = [];
  if (flags.pages.includes("pulse")) {
    targets.push({ label: "Pulse", url: `${baseUrl}/pulse` });
  }
  if (flags.pages.includes("thread")) {
    targets.push({ label: "Thread", url: `${baseUrl}/thread/${cardId}` });
  }

  console.log(`FinnWise Lighthouse CI (P1.5-S9) — ${formFactor}`);
  console.log(`Base URL: ${baseUrl}`);
  console.log(`Thread card: ${cardId}`);
  console.log(
    `Budgets: performance≥${budgets.minPerformanceScore}, TBT<${budgets.maxTotalBlockingTimeMs}ms, speed-index<${budgets.maxSpeedIndexMs}ms`,
  );
  if (
    budgets.minPerformanceScore !== defaultBudgets.minPerformanceScore ||
    budgets.maxTotalBlockingTimeMs !== defaultBudgets.maxTotalBlockingTimeMs ||
    budgets.maxSpeedIndexMs !== defaultBudgets.maxSpeedIndexMs
  ) {
    console.log("(budget overrides active via env)");
  }

  const { launchChrome, lighthouse } = await loadLighthouseModules();
  const chromeFlags = ["--headless", "--no-sandbox", "--disable-gpu"];
  if (env.CI === "true") {
    chromeFlags.push("--disable-dev-shm-usage");
  }
  const chrome = await launchChrome({ chromeFlags });

  const violations = [];
  try {
    for (const target of targets) {
      const violation = await auditPage({
        ...target,
        env,
        chrome,
        lighthouse,
        formFactor,
        budgets,
        saveReports: flags.saveReports,
        outputDir,
      });
      if (violation) violations.push(violation);
    }
  } finally {
    if (typeof chrome.kill === "function") {
      await chrome.kill();
    }
  }

  if (violations.length) {
    console.error("\n❌ Lighthouse budget failures:");
    for (const { label, failures } of violations) {
      console.error(`  ${label}:`);
      for (const msg of failures) console.error(`    - ${msg}`);
    }
    process.exit(1);
  }

  console.log("\n✅ All Lighthouse budgets passed.");
}

const isMain =
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (isMain) {
  main().catch((err) => {
    console.error(err.message ?? err);
    process.exit(1);
  });
}
