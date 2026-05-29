#!/usr/bin/env node
/**
 * P2.5-S1 — Map production deploy smoke checks.
 *
 * Usage:
 *   node scripts/map_production_smoke.mjs
 *   MAP_SMOKE_BEARER_TOKEN=<jwt> node scripts/map_production_smoke.mjs
 *
 * Env:
 *   MAP_SMOKE_FRONTEND_URL  (default: Vercel production)
 *   MAP_SMOKE_API_URL       (default: Render production)
 *   MAP_SMOKE_MAP_SLUG      (default: it)
 *   MAP_SMOKE_BEARER_TOKEN  optional — enables authenticated API checks
 */

const frontendBase = (
  process.env.MAP_SMOKE_FRONTEND_URL ?? "https://investment-assistant-frontend.vercel.app"
).replace(/\/$/, "");
const apiBase = (
  process.env.MAP_SMOKE_API_URL ?? "https://investment-assistant-3eqc.onrender.com"
).replace(/\/$/, "");
const slug = (process.env.MAP_SMOKE_MAP_SLUG ?? "it").trim();
const token = (process.env.MAP_SMOKE_BEARER_TOKEN ?? "").trim();

const checks = [
  { label: "GET /map (index)", url: `${frontendBase}/map`, expect: [200] },
  { label: `GET /map/${slug} (sector)`, url: `${frontendBase}/map/${encodeURIComponent(slug)}`, expect: [200] },
  {
    label: "GET /api/map/sectors (no auth)",
    url: `${apiBase}/api/map/sectors`,
    expect: [401],
    note: "404 means Map router not deployed on Render",
  },
];

if (token) {
  checks.push(
    {
      label: "GET /api/map/sectors (auth)",
      url: `${apiBase}/api/map/sectors`,
      headers: { Authorization: `Bearer ${token}` },
      expect: [200],
    },
    {
      label: `GET /api/map/sectors/${slug} (auth)`,
      url: `${apiBase}/api/map/sectors/${encodeURIComponent(slug)}`,
      headers: { Authorization: `Bearer ${token}` },
      expect: [200],
    },
  );
}

let failed = 0;

for (const check of checks) {
  try {
    const res = await fetch(check.url, {
      method: "GET",
      redirect: "follow",
      headers: check.headers ?? {},
    });
    const ok = check.expect.includes(res.status);
    const status = ok ? "PASS" : "FAIL";
    if (!ok) failed += 1;
    const note = check.note && !ok ? ` — ${check.note}` : "";
    console.log(`${status} ${check.label}: HTTP ${res.status} (expected ${check.expect.join("|")})${note}`);
  } catch (err) {
    failed += 1;
    console.log(`FAIL ${check.label}: ${err.message ?? err}`);
  }
}

if (!token) {
  console.log("\n(Set MAP_SMOKE_BEARER_TOKEN to run authenticated API checks.)");
}

process.exit(failed > 0 ? 1 : 0);
