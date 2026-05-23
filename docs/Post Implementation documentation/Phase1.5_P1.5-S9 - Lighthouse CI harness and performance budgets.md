# Post Implementation Detailed Document — P1.5-S9

**Version:** v1.0 | **Date:** 23-05-2026  
**Story ID:** P1.5-S9 (Phase 1.5, Story 9)  
**Reference plan:** `docs/plans/finnwise-phase1.5-implementation-tasks.md`

---

## Narrative style

**P1.5-S8** (accessibility quick wins) was **skipped** per product direction; **P1.5-S9** delivers the automated performance gate instead.

**P1.5-S9** adds a repo-root Lighthouse runner and CI job that audits **mobile** performance on production **Pulse** (`/pulse`) and **Thread** (`/thread/{cardId}`), then enforces Phase 1.5 budgets: **Performance ≥ 90**, **TBT < 200 ms**, **Speed Index < 3400 ms**. The runner reuses the same env conventions as **`bench_api_latency.mjs`** (`LIGHTHOUSE_THREAD_CARD_ID`, Vercel base URL). Budget logic lives in **`scripts/lighthouse-budget.mjs`** so smoke tests run without Chrome.

**Tests executed and passed:**

| Test | Result |
|------|--------|
| `node scripts/lighthouse-budget.test.mjs` | Pass — assertion helpers |
| `node scripts/lighthouse.mjs --assert-report="…pulse.json"` (baseline) | Exit **1** — performance 82, TBT 525 ms, SI 5790 ms (expected regression smoke) |
| Live prod **Thread** (`pnpm perf:lighthouse -- --thread-only --no-save`) | Pass — performance **96**, TBT **95 ms**, SI **2166 ms** |
| Live prod **Pulse** (same command, pulse-only) | **Fails SI only** — performance **98**, TBT **33 ms**, SI **3798 ms** (≥ 3400 ms budget) |

Optional axe/a11y test (**1.5.9.4**) deferred with skipped **P1.5-S8**.

**Follow-up (P1.5-S9b) — completed 23-05-2026:**

| Sub-task | Result |
|----------|--------|
| **1.5.9b.4** | Production desktop JSON captured under `Page Load Performance/New loads/` (Pulse + Thread); both pass `DESKTOP_BUDGETS` — no threshold changes needed for S10 |
| **1.5.9b.5** | Desktop CI step enforced (`continue-on-error` removed from `.github/workflows/ci.yml`) |

**Desktop baseline (production, DevTools export):**

| Surface | Performance | TBT | Speed Index |
|---------|-------------|-----|-------------|
| Pulse | 98 | 20 ms | 1600 ms |
| Thread | 100 | 0 ms | 980 ms |

Operator note: **`next dev` Lighthouse is not comparable to production** — use `pnpm build && pnpm start` locally; see `scripts/README.md`.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1.5-S9 |
| **Title** | Lighthouse CI harness and performance budgets |
| **Category** | **Full Stack** (Node runner + GitHub Actions; no app runtime changes) |

**What this story aimed to achieve**

Give the team an automated mobile Lighthouse gate on Pulse and Thread so performance regressions surface in CI before merge, using the same thresholds as the phase-wide Definition of Done.

**How it fits into the overall application**

**P1.5-S5/S6/S7** made SSR and bundle changes that improved TBT; **P1.5-S9** measures whether production still meets budgets. **P1.5-S10** (production sign-off) uses the same runner locally to capture JSON evidence. **P1.5-S8** was skipped; a11y axe tests tied to S8 were not added.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | Deliverable |
|----------|-------------|
| **1.5.9.1** | `scripts/lighthouse.mjs` — mobile throttling (4× CPU, slow 4G), audits Pulse + Thread |
| **1.5.9.2** | `pnpm perf:lighthouse` in `frontend/package.json` + root; env docs in `scripts/README.md` |
| **1.5.9.3** | `.github/workflows/ci.yml` job **Lighthouse budgets** |
| **1.5.9.4** | Optional axe — **deferred** (S8 skipped) |
| **1.5.9.5** | `scripts/lighthouse-budget.test.mjs` + baseline JSON assert exits 1 |

**Budget enforcement**

```
For each URL (Pulse, Thread):
  performance score (0–100) ≥ 90
  total-blocking-time.numericValue < 200
  speed-index.numericValue < 3400
```

**Environment**

| Variable | Default / notes |
|----------|-----------------|
| `LIGHTHOUSE_BASE_URL` | `https://investment-assistant-frontend.vercel.app` |
| `LIGHTHOUSE_THREAD_CARD_ID` | `e708b82c-f7c7-45e7-a59b-6b66dac8927a` (same as bench script) |
| `LIGHTHOUSE_SKIP=1` | Skip run (exit 0) |
| `LIGHTHOUSE_*` overrides | Min score, max TBT, max SI |

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale |
|----------|-----------|
| **Split `lighthouse-budget.mjs`** | Pure assertions testable without Chrome in CI smoke step |
| **Dynamic resolve via `createRequire`** | Runner lives in `scripts/` but deps install via pnpm workspace (`frontend/` or root) |
| **CI audits production, not PR preview** | Matches plan (“production or staging”); measures what users hit today |
| **Strict exit code 1 on budget miss** | Required for regression detection (**1.5.9.5**) |
| **Skip optional axe** | **P1.5-S8** deferred; axe test was optional and a11y-coupled |

**Current production snapshot (23-05-2026, mobile Lighthouse via runner)**

| Surface | Performance | TBT | Speed Index | Budget |
|---------|-------------|-----|-------------|--------|
| Pulse | 98 | 33 ms | 3798 ms | **SI fails** |
| Thread | 96 | 95 ms | 2166 ms | Pass |

CI **Lighthouse budgets** job will fail until Pulse Speed Index is under 3400 ms (or budgets adjusted at sign-off).

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Stories |
|-----------|---------|
| **Upstream** | **P1.5-S5**, **P1.5-S6** (pages to benchmark), **P1.5-S7** (TBT improvements) |
| **Downstream** | **P1.5-S10** (sign-off re-runs + JSON archive) |
| **Skipped** | **P1.5-S8** — no axe test added |

---

### A5. DESIGN CHOICES

**Files added/updated**

| Path | Role |
|------|------|
| `scripts/lighthouse.mjs` | Chrome + Lighthouse runner |
| `scripts/lighthouse-budget.mjs` | Shared budget helpers |
| `scripts/lighthouse-budget.test.mjs` | Smoke test |
| `frontend/package.json` | `perf:lighthouse` scripts + devDeps |
| `package.json` (root) | Workspace devDeps + script aliases |
| `.github/workflows/ci.yml` | **Lighthouse budgets** job |
| `scripts/README.md` | Operator docs |

**Run locally**

```bash
pnpm install          # repo root (pnpm workspace)
pnpm perf:lighthouse
pnpm perf:lighthouse:budget-test
```

---

## PART B — EXTENDED REFERENCE (optional)

### B1. CI job sequence

1. `pnpm perf:lighthouse:budget-test`
2. `pnpm perf:lighthouse -- --no-save` against `LIGHTHOUSE_BASE_URL` (mobile, enforced)
3. `pnpm perf:lighthouse:desktop -- --no-save` (desktop, enforced since **1.5.9b.5**)

### B2. Operator troubleshooting

| Symptom | Action |
|---------|--------|
| `Could not load lighthouse` | Run `pnpm install` at repo root |
| Chrome not found (Linux CI) | Ubuntu runner includes Chrome-compatible headless via `chrome-launcher` |
| Thread 404 | Set `LIGHTHOUSE_THREAD_CARD_ID` to a published card UUID |
| CI red on Pulse SI only | Expected until Pulse visual-complete improves; track under **P1.5-S10** |
