#!/usr/bin/env node
/**
 * Warm-request latency bench for Pulse feed and Thread card detail (P1.5-S1).
 *
 * Compares direct Render backend vs Vercel `/backend/...` proxy.
 * Reads repo-root `.env.local` when present.
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.join(scriptDir, "..");

const DEFAULT_VERCEL_URL = "https://investment-assistant-frontend.vercel.app";
const DEFAULT_CARD_ID = "e708b82c-f7c7-45e7-a59b-6b66dac8927a";
const WARM_ITERATIONS = 5;

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

function percentile(sorted, p) {
  if (sorted.length === 0) return 0;
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, idx)];
}

function summarize(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return {
    min: sorted[0] ?? 0,
    p50: percentile(sorted, 50),
    p95: percentile(sorted, 95),
    max: sorted[sorted.length - 1] ?? 0,
  };
}

function parseServerTiming(raw) {
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

async function benchEndpoint(label, url) {
  const wallSamples = [];
  const connectSamples = [];
  const querySamples = [];
  const totalSamples = [];
  const connectionCounts = [];

  for (let i = 0; i < WARM_ITERATIONS + 1; i += 1) {
    const started = performance.now();
    const response = await fetch(url, { cache: "no-store" });
    const wallMs = performance.now() - started;
    const serverTiming = parseServerTiming(response.headers.get("x-finnwise-timing"));

    if (i === 0) {
      if (!response.ok) {
        throw new Error(`${label} warmup failed: HTTP ${response.status} ${url}`);
      }
      continue;
    }

    if (!response.ok) {
      throw new Error(`${label} request failed: HTTP ${response.status} ${url}`);
    }

    wallSamples.push(wallMs);
    if (serverTiming) {
      connectSamples.push(Number(serverTiming.db_connect_ms ?? 0));
      querySamples.push(Number(serverTiming.db_query_ms ?? 0));
      totalSamples.push(Number(serverTiming.total_ms ?? 0));
      if (serverTiming.connection_count != null) {
        connectionCounts.push(Number(serverTiming.connection_count));
      }
    }
  }

  return {
    label,
    url,
    wall_ms: summarize(wallSamples),
    server: {
      db_connect_ms: summarize(connectSamples),
      db_query_ms: summarize(querySamples),
      total_ms: summarize(totalSamples),
    },
    connection_count: connectionCounts.length
      ? {
          min: Math.min(...connectionCounts),
          max: Math.max(...connectionCounts),
        }
      : null,
  };
}

function printSummary(result) {
  console.log(`\n=== ${result.label} ===`);
  console.log(result.url);
  console.log(
    `wall_ms   p50=${result.wall_ms.p50.toFixed(1)} p95=${result.wall_ms.p95.toFixed(1)}`,
  );
  if (result.server.db_connect_ms.p50 > 0 || result.server.db_query_ms.p50 > 0) {
    console.log(
      `server db_connect_ms p50=${result.server.db_connect_ms.p50.toFixed(1)} p95=${result.server.db_connect_ms.p95.toFixed(1)}`,
    );
    console.log(
      `server db_query_ms  p50=${result.server.db_query_ms.p50.toFixed(1)} p95=${result.server.db_query_ms.p95.toFixed(1)}`,
    );
    console.log(
      `server total_ms     p50=${result.server.total_ms.p50.toFixed(1)} p95=${result.server.total_ms.p95.toFixed(1)}`,
    );
  } else {
    console.log("server timing headers: (missing — deploy backend with P1.5-S1 first)");
  }
  if (result.connection_count) {
    console.log(
      `connections/request min=${result.connection_count.min} max=${result.connection_count.max}`,
    );
  }
}

async function main() {
  const env = { ...loadEnvLocal(), ...process.env };
  const directBase = normalizeBaseUrl(
    env.BENCH_API_DIRECT_URL ?? env.RENDER_API_BASE_URL ?? env.NEXT_PUBLIC_API_BASE_URL,
  );
  const vercelBase = normalizeBaseUrl(env.BENCH_VERCEL_URL ?? DEFAULT_VERCEL_URL);
  const cardId = (env.BENCH_CARD_ID ?? env.LIGHTHOUSE_THREAD_CARD_ID ?? DEFAULT_CARD_ID).trim();
  const allowLoopback = Boolean(env.BENCH_ALLOW_LOOPBACK === "1" || env.BENCH_API_DIRECT_URL);

  if (!directBase) {
    console.error(
      "Set BENCH_API_DIRECT_URL (or NEXT_PUBLIC_API_BASE_URL) to your Render backend origin.",
    );
    console.error("Example: BENCH_API_DIRECT_URL=https://your-service.onrender.com");
    process.exit(1);
  }

  if (!allowLoopback && /\/\/(localhost|127\.0\.0\.1)(:|\/|$)/i.test(directBase)) {
    console.error(
      "Direct URL points at loopback. Set BENCH_API_DIRECT_URL explicitly or BENCH_ALLOW_LOOPBACK=1 for local runs.",
    );
    process.exit(1);
  }

  const targets = [
    { label: "feed direct", url: `${directBase}/api/feed` },
    {
      label: "feed proxy",
      url: `${vercelBase}/backend/api/feed`,
    },
    {
      label: "card direct",
      url: `${directBase}/api/cards/${cardId}?view=current`,
    },
    {
      label: "card proxy",
      url: `${vercelBase}/backend/api/cards/${cardId}?view=current`,
    },
  ];

  console.log("FinnWise API latency bench (P1.5-S1)");
  console.log(`Direct base: ${directBase}`);
  console.log(`Proxy base:  ${vercelBase}`);
  console.log(`Card id:     ${cardId}`);
  console.log(`Warm iterations: ${WARM_ITERATIONS} (plus 1 discarded warmup)`);

  const results = [];
  for (const target of targets) {
    const result = await benchEndpoint(target.label, target.url);
    printSummary(result);
    results.push(result);
  }

  console.log("\nDone. Compare direct vs proxy wall_ms p95 to isolate proxy overhead.");
  console.log("Compare db_connect_ms vs db_query_ms to validate connection churn vs query cost.");
}

main().catch((err) => {
  console.error(err.message ?? err);
  process.exit(1);
});
