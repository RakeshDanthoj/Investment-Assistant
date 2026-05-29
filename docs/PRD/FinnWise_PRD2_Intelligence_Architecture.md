# FinnWise — Product Requirements Document — Volume 2

## Intelligence Architecture Redesign

| Attribute | Value |
|-----------|-------|
| **Status** | Final — supersedes all event-detection and confidence-scoring decisions in PRD v3 |
| **Scope** | Phase 3 intelligence layer: confidence scoring, de-duplication, LLM validation, Fog of War, NLP pipeline, hosting architecture |
| **Solo builder** | Three roles (Jordan / Sam / Riley) played by one person with role-switching |
| **LLM in prod** | Google Gemini (Phase 1/2). Phase 3 NLP: Gemini Flash. |
| **Hosting** | Render free tier (API server) + GitHub Actions (batch jobs). No tier upgrade required. |
| **SEBI posture** | Exploratory research. P3-S6 (marketing) and P3-S7 (billing) formally deferred. |
| **Phase 2 status** | Complete and clean. All Phase 2 stories ticked. |
| **Live tester data** | None yet. Synthetic seed strategy defined in Section 7. |
| **Date** | 24 May 2026 |

> **SEBI DISCLAIMER:** This document describes analytical infrastructure for an educational research application. It does not constitute investment advice under SEBI (Investment Advisers) Regulations 2013. No fee is charged. No personalised investment advice is provided.

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Gap Register — All Layers](#2-gap-register--all-layers)
3. [Block A — Confidence Scoring Decisions](#3-block-a--confidence-scoring-decisions)
4. [Block B — Data Pipeline Decisions](#4-block-b--data-pipeline-decisions)
5. [Block C — LLM Pipeline Decisions](#5-block-c--llm-pipeline-decisions)
6. [Block D — Fog of War and Signal Model Decisions](#6-block-d--fog-of-war-and-signal-model-decisions)
7. [Block E — Hosting, Infrastructure, and Data Decisions](#7-block-e--hosting-infrastructure-and-data-decisions)
8. [Phase 3 Scope Decisions](#8-phase-3-scope-decisions)
9. [Decision Summary — All 15 Blocks](#9-decision-summary--all-15-blocks)
10. [Non-Negotiable Constraints (Inherited from PRD v3)](#10-non-negotiable-constraints-inherited-from-prd-v3)

---

## 1. Purpose and Scope

This document resolves fifteen gaps in the FinnWise intelligence architecture that were identified across the PRD v3 event detection journey, the Phase 1/2 task audit, and the Phase 3 prerequisite review. These gaps were unspecified at the time Phase 1 and Phase 2 were built, meaning the implementations that exist in production may be producing outputs against undefined specifications.

PRD 2 does two things:

- Closes every open architectural decision with a definitive, implementable answer so Phase 3 build starts on solid ground.
- Replaces the Phase 3 task list with a scope-corrected, solo-sequenced build plan that reflects the actual constraints: one builder, Render free tier, no live tester data, SEBI exploratory posture.

This document supersedes all confidence scoring, de-duplication, LLM validation, Fog of War trigger, and hosting architecture decisions from PRD v3. Where PRD v3 and PRD 2 conflict, PRD 2 governs for Phase 3 build.

---

## 2. Gap Register — All Layers

Fifteen gaps identified across five architectural layers, rated by criticality. **P0** = build blocker. **P1** = high risk. **P2** = medium, manageable during build. All P0 and P1 gaps are resolved in Sections 3–7.

### 2.1 Layer 1 — Confidence Scoring (blocks everything downstream)

| ID | Title | Layer | Priority | Description |
|----|-------|-------|----------|-------------|
| **G-01** | Confidence score methodology is a black box | Event detection → confidence gate → signal monitoring | **P0 – CRITICAL** | PRD v3 says score is AI-generated but defines no inputs, model, thresholds, or output format. Every routing decision downstream (High/Medium/Low) depends on this. The Phase 1 scorer was built against an undefined spec and may produce arbitrary outputs. |
| **G-02** | High/Medium/Low threshold values are arbitrary | Confidence gate routing | **P0 – CRITICAL** | Even if the scorer exists, the numeric thresholds that determine routing tier were never defined. Phase 3 interaction model (P3-S2) builds on top of these — compounding undefined on undefined. |

### 2.2 Layer 2 — Data Pipeline Integrity

| ID | Title | Layer | Priority | Description |
|----|-------|-------|----------|-------------|
| **G-03** | De-duplication logic undefined — same event hits multiple sources | Raw event queue → deduplication → persistence | **P0 – CRITICAL** | RBI rate announcements appear in NewsAPI, RBI RSS, and NSE feed simultaneously. Phase 1 task 6.6 was ticked done but the deduplication key was never specified. Wrong key = missed events or duplicate editorial reviews. |
| **G-04** | NewsAPI keyword filters never defined | Source monitoring — NewsAPI adapter | **P1 – HIGH** | 100 calls/day cap. Without defined keyword filters the adapter returns noise or misses events. No keyword list was ever documented against the 8 Factor DB macro factors. |
| **G-05** | Slow-burn watchlist completely unspecified | Source monitoring — manual watchlist | **P1 – HIGH** | PRD v3 mentions it as a source but gives no format, owner process, escalation trigger, or DB table. As a solo builder, this is the highest-risk item to be skipped. Slow-burn events (monsoon deficit, regulatory reviews, budget cycle) require the most lead time. |
| **G-06** | yfinance and NSE scraper fragility — no tested fallback | Macro data sources → Factor DB refresh | **P1 – HIGH** | PRD v3 flags this risk. Phase 1 built source abstraction but fallback sources were never named or integrated. Phase 3 NLP pipeline adds a nightly filings job that will exacerbate scraper exposure. |

### 2.3 Layer 3 — LLM Pipeline Integrity

| ID | Title | Layer | Priority | Description |
|----|-------|-------|----------|-------------|
| **G-07** | Post-generation validation — no defined automated checks that block publication | Draft generation → editorial queue | **P0 – CRITICAL** | The LLM must never generate numbers — all numbers must trace to the Evidence layer. Whether the Phase 1 number_validator enforces this as a hard publish gate or a soft warning is unknown. As solo builder reviewing your own AI output, a soft warning is not sufficient. |
| **G-08** | Gemini vs smaller model for Phase 3 NLP extraction | LLM architecture — Phase 3 P3-S1a | **P1 – HIGH** | Phase 3 NLP filings extraction uses an LLM but which model was never specified. Gemini Pro is overkill for JSON-strict extraction from a bounded source excerpt. Gemini Flash is 10x cheaper and sufficient. |
| **G-09** | Editorial rejection loop — full re-run vs targeted section regen | Editorial review → draft revision | **P2 – MEDIUM** | When a draft card fails review, no return path is defined. Full 3-call re-run wastes cost and ignores specific editor feedback. Targeted section regen preserves the editor's annotation. |

### 2.4 Layer 4 — Fog of War and Signal Model

| ID | Title | Layer | Priority | Description |
|----|-------|-------|----------|-------------|
| **G-10** | Fog of War major event trigger has no implementable definition | Fog of War banner → confidence suppression → Phase 3 interaction model | **P0 – CRITICAL** | PRD v3 says fires at 3+ major events simultaneously active. Neither the definition of major nor the transition between Phase 1 heuristic and Phase 3 model is defined. The 6-month backtest has no real data to run against. |
| **G-11** | Signal false-positive rate — measurement mechanism never implemented | Confidence-gated signal detection → override log | **P1 – HIGH** | PRD v3 sets a V1 target of less than 10% false positive rate. The override log was mentioned but never specified as a DB table. Without measurement the target is unmeasurable. |

### 2.5 Layer 5 — Phase 3 Specific Gaps

| ID | Title | Layer | Priority | Description |
|----|-------|-------|----------|-------------|
| **G-12** | Render free tier cold-start kills nightly NLP job | P3-S1a NLP pipeline — hosting constraint | **P0 – CRITICAL** | Render free tier spins down after 15 minutes of inactivity. A nightly PDF-processing job will cold-start from zero every night. spaCy model load alone takes 10–30 seconds. The job will appear to run but silently fail or timeout. |
| **G-13** | No live Mirror/Lens data — Phase 3 ML prerequisites unmet | Phase 3 prerequisite — tester data | **P0 – CRITICAL** | Phase 3 requires Mirror + Lens live data for 3+ months. Fog of War backtest, reasoning gap detector, and NLP Factor DB comparison all need historical ground truth. Starting Phase 3 ML work without this means building blind. |
| **G-14** | P3-S6/S7 marketing and billing are dead weight until SEBI gate | Phase 3 scope — SEBI posture | **P2 – MEDIUM** | SEBI stays exploratory. P3-S8 gate will not go green without RA registration decision. Building marketing and billing infrastructure before the gate wastes solo effort and creates decision fatigue. |
| **G-15** | Editorial checklist never formalised as a hard pass/fail gate | Editorial review — ongoing quality control | **P2 – MEDIUM** | Phase 1 built a ChecklistPanel but acceptance criteria were never defined per item. As solo builder reviewing own AI output, unchecked items must block publish — not be soft reminders. |

---

## 3. Block A — Confidence Scoring Decisions

> **P0 blocker.** Every routing decision in the pipeline depends on this. Resolve before any Phase 3 build begins.

### 3.1 Decision: Rule-based scorer replaces AI-generated score

The PRD v3 description of an AI-generated confidence score is replaced. Rationale: a rule-based weighted scorer is debuggable, reproducible, requires no LLM call, and produces an auditable numeric basis for every routing decision. Reserve Gemini for the three card synthesis roles where it genuinely adds value.

#### Scorer specification

```
confidence_score(event) -> float (0.0 to 1.0):

  source_count_score   = min(event.source_count / 3, 1.0)  x 0.35
  source_quality_score = QUALITY_MAP[event.primary_source]  x 0.30
  factor_db_match      = factor_db.match_strength(event)    x 0.25
  recency_score        = decay_fn(event.first_seen_at)      x 0.10

  raw = sum(above)   # 0.0 - 1.0

  if fog_of_war_active:
    raw = raw * FOG_DAMPENER   # default 0.6, see Section 6

  store raw on events.confidence_raw
  return raw
```

#### Source quality map — Indian financial sources

| Source tier | Examples | Quality weight |
|-------------|----------|----------------|
| Official government / exchange feed | RBI website, NSE official, BSE official, Ministry of Finance | 1.0 |
| Major news wire | PTI, Reuters India, Bloomberg India, IANS | 0.8 |
| Financial press | Economic Times, Mint, Business Standard, Hindu Business Line | 0.65 |
| General news | Times of India financial desk, NDTV Business, Moneycontrol | 0.50 |
| Aggregator / blog / social | Twitter/X, Substack, Reddit IndiaInvestments | 0.30 |

#### Factor DB match strength

`factor_db.match_strength(event)` returns 0.0 to 1.0 based on how many of the 8 macro factors the event touches, weighted by event category:

- Direct match to 2+ factors: **1.0** (e.g. RBI rate decision touches domestic interest rates + bank NIM directly)
- Direct match to 1 factor: **0.7**
- Indirect / sector match only: **0.4**
- No Factor DB match: **0.0**

#### Recency decay function

```
decay_fn(first_seen_at):
  age_hours = (now - first_seen_at).total_seconds() / 3600
  if age_hours <= 4:   return 1.0   # within one detection cycle
  if age_hours <= 12:  return 0.7
  if age_hours <= 24:  return 0.4
  return 0.1                         # stale event
```

### 3.2 Decision: Routing thresholds

Calibrated against 10 historical Indian financial events (manual calibration exercise required in Week 2 of the Phase 3 build, see Section 9):

| Tier | Raw score threshold | System action |
|------|---------------------|---------------|
| **HIGH** | >= 0.75 | Auto-generate draft card. Notify editor. 2-hour override window. |
| **MEDIUM** | >= 0.45 and < 0.75 | Generate draft. Hold in editorial queue. Editor reviews within 10 minutes. |
| **LOW** | < 0.45 | Log to events table. Surface in daily editorial digest. No card generated. |

These thresholds are stored in a config file (`backend/app/core/confidence_config.py`), not hardcoded. They are tunable without a code change after calibration.

---

## 4. Block B — Data Pipeline Decisions

### 4.1 Decision: De-duplication key

A composite SHA-256 key prevents the same real-world event from generating multiple queue entries when it appears in multiple sources simultaneously.

```
dedup_key = sha256(
  event_category       +   # 'RBI_POLICY' / 'CRUDE' / 'GEOPOLITICAL' / etc.
  normalise(entity)    +   # see entity normalisation dict below
  date_floor_4h(detected_at)  # floor to nearest 4-hour window
)

INSERT INTO events (..., dedup_key, source_count, sources)
ON CONFLICT (dedup_key)
DO UPDATE SET
  source_count = events.source_count + 1,
  sources      = array_append(events.sources, EXCLUDED.sources[1]),
  confidence_raw = recompute_score(events.id)   # score improves as sources accumulate
```

Entity normalisation dictionary — top 30 Indian financial entities (extend as needed):

```
ENTITY_MAP = {
  'Reserve Bank of India': 'rbi', 'RBI': 'rbi',
  'National Stock Exchange': 'nse', 'NSE': 'nse',
  'Bombay Stock Exchange': 'bse', 'BSE': 'bse',
  'SEBI': 'sebi', 'Securities and Exchange Board': 'sebi',
  'ONGC': 'ongc', 'Oil and Natural Gas': 'ongc',
  'State Bank of India': 'sbi', 'SBI': 'sbi',
  'HDFC Bank': 'hdfc_bank', 'ICICI Bank': 'icici_bank',
  'Infosys': 'infosys', 'TCS': 'tcs', 'Tata Consultancy': 'tcs',
  'Reliance Industries': 'ril', 'Reliance': 'ril',
  'OPEC': 'opec', 'Federal Reserve': 'fed', 'US Fed': 'fed',
  # ... extend to 50+ entities over Phase 3
}
```

### 4.2 Decision: NewsAPI keyword filters per Factor DB macro factor

Each of the 8 Factor DB macro factors maps to a keyword set. The NewsAPI adapter cycles through these sets across its 100 daily calls, allocating calls proportionally to factor volatility:

| Factor | Daily calls | Keyword set |
|--------|-------------|-------------|
| Crude oil price | 15 | crude oil, brent, WTI, OPEC, oil price India, petroleum, ATF price, ONGC, oil ministry |
| Dollar-Rupee rate | 15 | rupee dollar, INR USD, RBI forex, currency India, dollar rate, foreign exchange India |
| Domestic interest rates | 20 | RBI rate, repo rate, monetary policy, MPC meeting, inflation India, CPI India, RBI circular |
| Global risk sentiment | 10 | FII outflow, FII inflow, foreign institutional, risk off, global selloff, emerging markets |
| Monsoon index | 10 | monsoon India, IMD forecast, rainfall deficit, kharif, rabi, food inflation India |
| Government capex | 10 | union budget, capex India, infrastructure spending, PLI scheme, government spending |
| GST collections | 10 | GST collection, goods services tax, ministry of finance monthly, consumption India |
| Regulatory environment | 10 | SEBI circular, NSE regulation, RBI regulation, sector policy India, new regulation |

Total: 100 calls/day exactly. Adjust allocation based on Phase 3 event frequency data.

### 4.3 Decision: Slow-burn watchlist format and process

A DB table replaces the undefined manual watchlist. The solo builder reviews it every Sunday morning as a calendar-blocked 30-minute session.

```sql
CREATE TABLE watchlist_items (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_description text NOT NULL,
  category          text NOT NULL,  -- same enum as events.category
  added_at          timestamptz DEFAULT now(),
  review_frequency  text DEFAULT 'weekly',  -- 'daily'/'weekly'/'monthly'
  last_reviewed_at  timestamptz,
  escalation_trigger text,  -- condition that moves this to active event
  status            text DEFAULT 'watching'  -- 'watching'/'escalated'/'closed'
);
```

Qualifying slow-burn categories for Phase 3 seed:

- Electoral calendar — state elections with market-sensitive outcomes (e.g. UP, Maharashtra)
- Regulatory reviews in progress — pending SEBI circulars, RBI consultation papers
- Monsoon outlook — IMD seasonal forecast updates (April, June, August windows)
- Union Budget cycle — pre-budget expectations, interim budget, full budget
- Geopolitical slow burns — India-Pakistan tensions, India-China trade disputes, sanctions affecting Indian imports

### 4.4 Decision: Data source fallback chain

| Data type | Primary source | Fallback chain |
|-----------|----------------|----------------|
| Stock EOD prices | yfinance (Yahoo Finance) | 1. investing.com scrape  2. Manual entry + staleness flag  3. Freshness dot turns red |
| Currency rates | yfinance INR/USD | 1. Open Exchange Rates free API  2. RBI reference rate page scrape |
| NSE FII/DII data | NSE public CSV | 1. CDSL data portal  2. NSE website table scrape with retry  3. Stale + flag |
| RBI policy data | RBI RSS feed | 1. RBI website direct scrape  2. Manual entry (events rarely missed) |
| Market news | NewsAPI free tier | 1. GNews API free tier (100/day)  2. RSS feeds: ET Markets, Mint |
| Fundamental data | Screener.in / Tickertape | Manual weekly review only. No automated fallback. Grey area. |

---

## 5. Block C — LLM Pipeline Decisions

### 5.1 Decision: Number validator is a hard publish gate, not a warning

This is the most important integrity mechanism in the product. The Publish button in the editorial interface is disabled until `number_validator.check(card)` returns PASS. There is no override. There is no per-card exception.

```
number_validator.check(card) -> PASS | FAIL(reasons):

  # Step 1: Extract all numeric tokens from Insight + Context text
  numbers = extract_numerics(card.insight_text + card.context_text)
  # regex: [0-9]+([.,][0-9]+)?\s*(%|bps|Cr|L|K|bn|mn|$/Rs/INR)?

  # Step 2: Every number must appear in at least one Evidence row
  ungrounded = []
  for num in numbers:
    if not any(num_appears_in(num, row.source_excerpt) for row in card.evidence):
      ungrounded.append(num)

  # Step 3: Every Evidence row must have required fields
  missing_provenance = [
    row for row in card.evidence
    if not (row.source_url and row.retrieved_at and row.mmj_tag)
  ]

  if ungrounded or missing_provenance:
    return FAIL(ungrounded=ungrounded, missing=missing_provenance)
  return PASS
```

The editorial interface shows a structured diff when FAIL is returned: which numbers in the narrative have no Evidence backing, listed by sentence. The editor either adds an Evidence row with the source or rewrites the narrative sentence to remove the unsupported number.

### 5.2 Decision: LLM model for Phase 3 NLP filings extraction

**Gemini Flash** (`gemini-1.5-flash` or `gemini-2.0-flash-lite`, whichever is active in Gemini API at Phase 3 build time) for the P3-S1a NLP filings extraction job. Rationale:

- The task is JSON-strict extraction from a bounded source excerpt — Gemini Pro is overkill.
- Gemini Flash is approximately 10x cheaper per token at comparable JSON-extraction quality.
- The source_guard hallucination check (G-01a in Phase 3) catches any model errors programmatically.
- Same provider as production card synthesis (Gemini Pro) — no new API keys, no new billing account.

The three-call card synthesis pipeline (Role 1/2/3) continues to use Gemini Pro. Only the NLP extraction job uses Flash.

### 5.3 Decision: Editorial rejection loop — targeted section regen

When a draft card fails editorial review, the editor annotates which ICE section failed and why. A targeted regen call re-runs only the failing section's LLM call with the editor's annotation appended to the prompt. Full re-runs are not permitted in the standard flow.

```
POST /api/cards/{id}/regenerate-section
Body: {
  section: 'insight' | 'context' | 'evidence' | 'dissent' | 'framework',
  editor_note: string  // editor's specific objection, max 500 chars
}

# The regeneration prompt appends:
# 'EDITOR FEEDBACK: {editor_note}. Revise this section only.
#  All other sections are approved. Do not alter them.'
```

The full 3-call re-run is available as a separate button (`POST /api/cards/{id}/regenerate-full`) for cases where the card is fundamentally wrong, but it requires a separate confirmation and logs a `full_regen_count` on the card row. A card with `full_regen_count > 2` gets flagged in the editorial queue for Product Owner review before publish.

---

## 6. Block D — Fog of War and Signal Model Decisions

### 6.1 Decision: Formalise the is_major attribute on the events table

The word *major* is given a concrete, storable definition. This attribute is the shared foundation that both the Phase 1 heuristic and the Phase 3 interaction model reference.

```sql
ALTER TABLE events ADD COLUMN is_major BOOLEAN DEFAULT FALSE;

-- is_major = TRUE when ALL three conditions are met:
--   1. confidence_raw >= 0.75 (HIGH tier)
--   2. factor_db_match_count >= 2  (touches 2+ of the 8 macro factors)
--   3. category IN ('RBI_POLICY','GEOPOLITICAL','BUDGET','GLOBAL_MACRO','CRUDE_SHOCK')

-- Set automatically by the confidence scorer after each event upsert.
-- Can be manually overridden by Product Owner via editorial interface.

-- Fog of War heuristic (Phase 1 fallback):
--   SELECT COUNT(*) FROM events
--   WHERE is_major = TRUE AND lifecycle_state = 'active'
--   >= 3  -->  fog_of_war_active = TRUE
```

### 6.2 Decision: Fog of War confidence dampener

When Fog of War is active, the confidence scorer applies a **0.6** multiplier to all raw scores. This means:

- An event that would score 0.80 (HIGH) during normal conditions scores 0.48 (MEDIUM) during Fog of War.
- An event that would score 0.70 (HIGH) scores 0.42 (LOW) during Fog of War.
- The dampener is stored as a config constant `FOG_DAMPENER = 0.6` — tunable after Phase 3 backtest.

The Fog of War banner in the Pulse shows the reason string: which `is_major` events are currently active and their factor overlaps. This replaces the generic banner from Phase 1.

### 6.3 Decision: Phase 3 interaction model deferred until synthetic data is in place

The P3-S2 interaction model (factor-overlap detection replacing the `is_major` count heuristic) requires 6 months of historical confidence data to backtest against. With no live tester data, that data does not exist. The model is deferred until the synthetic seed strategy (Section 7) is in place and has been live for at least 30 days.

**Build order for P3-S2:** synthetic seed first (Week 3) → let heuristic run against synthetic data for 30 days → build interaction model against the resulting `card_confidence_history` → backtest → feature-flag deployment.

### 6.4 Decision: Signal override log — schema for false positive measurement

```sql
CREATE TABLE signal_override_log (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id       uuid REFERENCES signals(id),
  card_id         uuid REFERENCES events(id),
  auto_triggered_at  timestamptz NOT NULL,
  overridden_at      timestamptz,
  override_reason    text,
  override_by        uuid REFERENCES auth.users(id),
  final_outcome      text  -- 'confirmed'/'incorrect'/'ambiguous'
);

-- False positive rate = COUNT(override_reason IS NOT NULL AND final_outcome='incorrect')
--                      / COUNT(*) WHERE auto_triggered_at IS NOT NULL
-- Target: < 10% (PRD v3 Section 13)
-- Measured monthly. Logged in notes/signal-override-log-monthly.md
```

---

## 7. Block E — Hosting, Infrastructure, and Data Decisions

### 7.1 Decision: GitHub Actions as Phase 3 NLP job runner

The nightly filings extraction job (P3-S1a) runs as a GitHub Actions scheduled workflow, not on Render. This resolves the cold-start problem (G-12) at zero additional cost.

```yaml
# .github/workflows/nlp_filings_extract.yml
on:
  schedule:
    - cron: '0 1 * * *'   # 1am IST = 7:30pm UTC, after NSE close
  workflow_dispatch:       # manual trigger for testing

jobs:
  extract:
    runs-on: ubuntu-latest
    timeout-minutes: 50    # well within GH Actions 6hr limit
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r backend/requirements-nlp.txt
      - run: python backend/app/jobs/nlp_filings_extract.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

The existing 4-hour event detection cron stays on Render. A GH Actions ping workflow keeps the Render container warm:

```yaml
# .github/workflows/render_keepalive.yml
on:
  schedule:
    - cron: '*/10 4-14 * * 1-5'  # every 10min, 9:30am-8pm IST, weekdays
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: curl -f ${{ secrets.BACKEND_URL }}/health || exit 0
```

Total additional infrastructure cost: **zero**. GH Actions free tier provides 2,000 minutes/month. The nightly NLP job runs approximately 30 minutes per night = 900 minutes/month, well within the free allowance.

### 7.2 Decision: Synthetic data seeding strategy

Phase 3 ML work starts immediately using synthetic historical data seeded into the production DB tables, marked with `is_synthetic = TRUE`. Synthetic rows are excluded from all user-facing track record displays and from the real accuracy statistics in The Mirror.

#### Seed scope

- 20 historical Indian financial events from January to June 2025.
- Each event seeded with: confidence scores, lifecycle transitions, signals fired, system predictions, and simulated user predictions with accuracy grades.
- 7 events designated `is_major = TRUE` to generate Fog of War trigger history for the backtest.

#### Seed event list (20 events)

Events to seed — all publicly verifiable from news archives:

- RBI MPC rate hold (February 2025)
- Union Budget 2025-26 (February 1)
- RBI rate cut 25bps (April 2025)
- Pahalgam attack market reaction (April 2025)
- India-Pakistan tensions escalation (May 2025)
- RBI MPC (June 2025)
- Monsoon onset Kerala (June 2025)
- FII outflow spike (March 2025)
- Crude oil price spike on OPEC cut (March 2025)
- INR/USD move to 87+ (January 2025)
- IT sector TCS / Infosys quarterly results (January 2025)
- HDFC Bank quarterly results (January 2025)
- SBI quarterly results (February 2025)
- Nifty Bank index circuit event (April 2025)
- US tariff announcement India impact (April 2025)
- Gold price ATH India (April 2025)
- Pharma sector USFDA action (February 2025)
- PLI scheme auto sector announcement (March 2025)
- NSE F&O expiry anomaly (March 2025)
- RBI liquidity injection announcement (January 2025)

#### is_synthetic flag migration

```sql
-- Add to: events, signals, track_record, user_predictions, card_confidence_history
ALTER TABLE events ADD COLUMN is_synthetic BOOLEAN DEFAULT FALSE;
ALTER TABLE track_record ADD COLUMN is_synthetic BOOLEAN DEFAULT FALSE;
ALTER TABLE user_predictions ADD COLUMN is_synthetic BOOLEAN DEFAULT FALSE;

-- RLS: synthetic rows never appear in user-facing queries
-- All existing queries append: AND is_synthetic = FALSE
-- Synthetic rows accessible only via service role key (admin/job use)
```

#### Synthetic isolation verification (P3-T1)

Triple-layer isolation is enforced in production as follows: **(1)** Postgres RLS hides `is_synthetic = TRUE` rows from the `authenticated` role on `events`, `signals`, `track_record`, `user_predictions`, and `card_confidence_history`; **(2)** the FastAPI service layer applies `SyntheticFilterMixin` (`is_synthetic IS NOT TRUE`) on all Pulse feed, Thread card-detail, Mirror prediction, and market-facts read paths, because the API connects via `SUPABASE_DB_URL` as `postgres` and bypasses RLS; **(3)** CI runs `test_query_synthetic_filter.py` (static guard on known read modules) and `test_synthetic_isolation.py` (integration: Pulse, Thread, Mirror return zero synthetic rows when seed data exists; service-role SQL smoke confirms synthetic rows remain visible for admin/calibration jobs). See migration `0021_synthetic_isolation.sql` and Phase 3 task **P3-T1**.

---

## 8. Phase 3 Scope Decisions

### 8.1 Formal deferral of P3-S6 and P3-S7

> **P3-S6** (public marketing site + waitlist) and **P3-S7** (pricing + paywall infrastructure) are formally deferred from active Phase 3 scope. They remain as a gated appendix. No build work begins on either story until P3-S8 go/no-go returns green **and** a SEBI Research Analyst registration path is confirmed.

Rationale: SEBI posture is exploratory. The P3-S8 gate requires RA registration decision as a precondition. Building marketing and billing infrastructure before the gate is wasted solo effort. Removing these two stories from active scope frees approximately 11 story points and eliminates billing provider selection as a current decision.

**Active Phase 3 scope after deferral:** P3-S1a, P3-S1b, P3-S2, P3-S3, P3-S4, P3-S5, P3-S8, P3-S9. **Total: 43 story points.**

### 8.2 Editorial checklist — hard gate specification

The Phase 1 ChecklistPanel is upgraded to a hard gate. Each checklist item must be explicitly marked PASS before the Publish button activates. The five items and their pass criteria:

| Checklist item | Hard pass criterion |
|----------------|---------------------|
| All numbers source-tagged | `number_validator.check()` returns PASS (automated — auto-checked on card load) |
| Dissenting view present | `card.dissent_text` is not null and len > 100 chars (automated check) |
| Confidence consistent with data freshness | Manual tick. Editor confirms no MEASURED claim has a source older than 18 months. |
| Language accessible to non-expert | Manual tick. Editor has read the Insight layer for jargon and confirmed plain English. |
| SEBI language compliance | Manual tick. No buy/sell/hold. No price targets. No return expectations. All instrument chips use approved signal vocabulary. |

Items 1 and 2 are automated checks run on card load. Items 3, 4, and 5 require manual ticks. All five must show PASS state before Publish activates.

---

## 9. Decision Summary — All 15 Blocks

Consolidated reference. Each decision is traceable to its gap ID and section.

### Block A — Confidence scoring

| # | Decision | Agreed answer |
|---|----------|---------------|
| 1 | AI-generated vs rule-based scorer? | Rule-based weighted scorer. 4 inputs: source_count (35%), source_quality (30%), factor_db_match (25%), recency (10%). Stored in `confidence_config.py`. |
| 2 | Source quality map? | 5 tiers: Official feed 1.0 / Major wire 0.8 / Financial press 0.65 / General news 0.50 / Blog-social 0.30. |
| 3 | Routing thresholds? | HIGH >= 0.75 / MEDIUM >= 0.45 / LOW < 0.45. Calibrate against 10 historical events in Week 2. |
| 4 | Fog of War score dampener? | 0.6x multiplier on raw score when `fog_of_war_active = TRUE`. |

### Block B — Data pipeline

| # | Decision | Agreed answer |
|---|----------|---------------|
| 1 | De-duplication key? | SHA-256 of `event_category` + normalised entity name + 4-hour time window floor. Source count accumulates on conflict. |
| 2 | NewsAPI keyword filters? | 8 factor sets, 100 calls/day allocated proportionally. Full keyword list in Section 4.2. |
| 3 | Slow-burn watchlist format? | `watchlist_items` DB table. 5 categories. Weekly Sunday 30-min review session. |
| 4 | Fallback source chain? | Defined per data type in Section 4.4. Source abstraction layer tries fallbacks in order before setting staleness flag. |

### Block C — LLM pipeline

| # | Decision | Agreed answer |
|---|----------|---------------|
| 1 | NLP extraction model? | Gemini Flash. Same provider as prod. 10x cheaper than Pro for JSON-strict extraction. source_guard catches hallucinations. |
| 2 | Number validator gate type? | Hard gate. Publish button disabled until PASS. No per-card override. Editorial interface shows structured diff of ungrounded numbers. |
| 3 | Rejection loop design? | Targeted section regen by default. Editor annotates failing section + reason. Full re-run available but logged; card flagged if `full_regen_count > 2`. |

### Block D — Fog of War and signals

| # | Decision | Agreed answer |
|---|----------|---------------|
| 1 | Define major event? | `is_major = TRUE` when: `confidence_raw >= 0.75` AND `factor_db_match_count >= 2` AND category IN qualifying set. Stored as boolean column on events table. |
| 2 | Synthetic data before ML work? | Seed 20 historical events (Jan–Jun 2025) as `is_synthetic` rows. Unblocks Fog of War backtest and gap detector. Week 3 of Phase 3. |
| 3 | Defer P3-S6 and P3-S7? | Yes. Formally deferred. Not in active Phase 3 scope. Gated appendix only. Revisit when SEBI posture changes. |

### Block E — Hosting and infrastructure

| # | Decision | Agreed answer |
|---|----------|---------------|
| 1 | NLP job runner? | GitHub Actions scheduled workflow (1am IST). Render API server stays on free tier with GH Actions keep-alive ping every 10 minutes on market day hours. |
| 2 | Override log schema? | `signal_override_log` table defined in Section 6.4. False positive rate = overrides with `final_outcome=incorrect` / total auto-triggers. Measured monthly. |

---

## 10. Non-Negotiable Constraints (Inherited from PRD v3)

These constraints carry forward unchanged into Phase 3. No build decision in PRD 2 relaxes them.

- No buy, sell, or hold language anywhere in the application. Instruments use only: opportunity signal / headwind signal / watch.
- SEBI disclaimer hardcoded on every screen that shows instrument-specific analysis — persistent footer, never a popup.
- MMJ badges on every quantitative claim. MEASURED / MODELLED / JUDGED. Never omitted. Never optional.
- Direction and magnitude confidence are always two separate dots with separate labels. Never combined.
- Original View is always accessible. Track record is append-only at DB level — no deletes, no updates.
- LLM never generates numbers. Every number in Insight and Context must trace to a specific Evidence layer data point.
- Compound Fog of War confidence dampener must never mutate original confidence values in place. Writes to `card_confidence_history`, not to the events row.
- No user financial data stored beyond session — investment amount, period, risk preference are session-only.

---

_FinnWise PRD 2 — Intelligence Architecture Redesign — 24 May 2026_

_Document status: Final — supersedes all confidence scoring, de-duplication, LLM validation, Fog of War, and hosting architecture decisions from PRD v3._

_Source: converted from `finnwise-gaps-enhanced.js` (docx generator script)._
