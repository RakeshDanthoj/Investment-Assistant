# Post Implementation Detailed Document — P3-S1f

**Version:** v1.0 | **Date:** 31-05-2026  
**Story ID:** P3-S1f (Phase 3, Story 1f)  
**PRD2 gap:** G-06  
**Reference plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (tasks **6.0**–**6.6**)  
**PRD2 architecture:** `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` §4.4, `docs/PRD/FinnWise_PRD2_SSA_Solution_Design.md` G-06

---

## Narrative style (read this first)

Market fact chips on Pulse and Thread now show **freshness** (green / amber / red) beside each macro number. Behind the UI, a **config-driven fallback chain** resolves five **critical facts** (INR/USD, repo rate, Nifty 50, India VIX, FII net) before card synthesis runs. If any critical fact is **unavailable**, the **card draft pipeline is held** — no LLM slot is consumed and telemetry records status `held`. If facts are only **stale**, drafting may proceed; chips and the editorial queue banner warn the editor.

This implements **PO decision G-06 Option B**: revised fallback chains **without investing.com scrape**, a freshness **tristate** (`fresh` | `stale` | `unavailable`), and a tiny **critical-facts gate** at `draft_card_from_event`. The P2-S14 signal-monitor fact stream (`MarketFact` text corroboration) is unchanged; P3-S1f adds a parallel **quoted fact** model (`MarketQuoteFact`) for displayable numbers and pipeline gating.

**Tests executed and passed (P3-S1f–specific, on implementation):**

| Suite | Command | Result |
|-------|---------|--------|
| Freshness + gate + pipeline hold | `python -m pytest backend/tests/test_market_facts_freshness.py -q` | **9 passed** |
| Card pipeline regression (gate mock) | `python -m pytest backend/tests/test_card_pipeline.py -q` | **2 passed** |
| P2-S14 merge regression | `python -m pytest backend/tests/test_market_facts_merge.py -q` | **5 passed** |
| NSE adapter contract regression | `python -m pytest backend/tests/test_nse_facts_adapter_contract.py -q` | **4 passed** |
| **Full backend CI** | `python -m ruff check backend` + `python -m pytest -q backend/tests` | **278 passed**, ruff clean |
| Frontend FreshnessDot | `pnpm test` (includes `FreshnessDot.test.tsx`) | **3 passed** (component) |
| **Full frontend CI** | `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` | **Pass** (124 Jest tests total) |

**Three anchors for handover:** (1) **No DB migration** — config lives in `critical_facts.yaml`; deploy backend + frontend together so `/api/market-facts` and chips align. (2) **Optional `OPEN_EXCHANGE_RATES_APP_ID`** improves INR/USD fallback — not required for local dev if Yahoo/RBI paths succeed. (3) **Do not bypass the critical-facts gate** in `card_pipeline.py` without PO sign-off — it is the G-06 trust mechanism for macro-dependent cards.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P3-S1f |
| **Title** | Market facts freshness + fallback chain |
| **Category** | **Full Stack** (config + adapter services + card pipeline gate + Pulse/Thread UI + editorial banner) |
| **Points / owner (plan)** | 3 · Sam |
| **Depends on** | P3-S1c (dedup pipeline ordering; shared data-pipeline milestone) |
| **Parallel with** | _None until dedup landed_ |
| **Blocks** | P3-T2 (data pipeline integration test gate includes critical-fact hold) |

**What this story aimed to achieve (plain language)**

Users and editors should never see a macro number without knowing how fresh it is. When Yahoo Finance, NSE, or other sources fail, the system should try named fallbacks (not investing.com scrape) and either show a stale value with a warning or block card generation when a **critical** fact has no value at all.

**How it fits into the overall application**

- **Upstream:** P2-S14 established merged market facts for the **signal monitor** (text overlap on event/NSE streams). P3-S1c ensured clean event rows before downstream scoring.
- **This story:** Adds **displayable quoted facts** with freshness dots on user surfaces and a **hard hold** on the LLM card pipeline when critical macro inputs are missing.
- **Downstream:** **P3-T2** will integration-test dedup + NewsAPI + watchlist + this hold gate together; **P3-S1g** confidence scoring consumes post-dedup events (orthogonal to facts gate).

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

| Sub-task | What it does |
|----------|----------------|
| **6.1** | `critical_facts.yaml` + per-fact fallback chains (no investing.com). |
| **6.2** | Tristate freshness on merged quoted stream; thresholds in YAML (`fresh_max_hours: 24`, `stale_max_hours: 72`). |
| **6.3** | `card_pipeline.py`: `assert_critical_facts_available()` before LLM; telemetry `status=held` on hold. |
| **6.4** | `FreshnessDot` + `MarketFactChips` on Pulse and Thread via `MarketFactsStrip`. |
| **6.5** | `MarketFactsBanner` on `/admin/queue` for degraded / hold messaging. |
| **6.6** | Tests: unavailable blocks draft; stale allows with flag. |

**Functional breakdown**

1. **Resolve facts:** `build_quoted_market_facts()` loads `critical_facts.yaml`, runs each fact’s `chain` in order until a `QuoteObservation` is returned.
2. **Classify freshness:** `classify_freshness()` maps observation age → `fresh` / `stale`; no value → `unavailable`.
3. **Gate:** `evaluate_critical_facts_gate()` collects fact IDs where `critical=true` and `freshness_status=unavailable`. Any hit → `blocked=true`.
4. **Card draft:** `draft_card_from_event()` calls gate first; on hold raises `CriticalFactsHoldError` (API → **423** `critical_facts_held`). On pass, macro lines are injected into evidence `macro_stub` via `quote_facts_to_macro_lines()`.
5. **UI:** Client polls `GET /api/market-facts` and renders chips with coloured dots; editorial queue shows banner when `unavailable_critical` or `has_stale_critical`.

**Fallback chains implemented (PO-08 / G-06 Option B)**

| Fact ID | Chain steps | Notes |
|---------|-------------|--------|
| `inr_usd` | yfinance → open_exchange_rates → rbi_ref | Yahoo chart API as yfinance primary; OXR needs env key |
| `repo_rate` | rbi_events → config_fallback | Parses recent `events` titles; fallback `6.50%` @ 720h ago |
| `nifty_50` | yfinance → nse_index | NSE index adapter parses “Nifty 50” level from snapshot |
| `india_vix` | yfinance → nse_index | Same NSE path for India VIX label |
| `fii_net` | nse_fii_csv → cdsl_portal | NSE `fiidiiTradeReact` API; **CDSL stub returns None** |

**Edge cases and validation**

| Case | Behaviour |
|------|-----------|
| All chain steps fail | `display_value="—"`, `freshness_status=unavailable`, fact ID in `unavailable_critical` |
| Value older than 72h | Still **stale** (red/amber dot), not unavailable — drafting allowed |
| Unknown chain step name in YAML | Logged warning; step skipped |
| Chain step raises exception | Logged warning; next step tried |
| `OPEN_EXCHANGE_RATES_APP_ID` unset | `open_exchange_rates` step skipped (returns None) |
| Critical hold during draft | No `consume_slot_or_raise()`; `insert_draft_card_bundle` not called |
| API draft request while held | HTTP **423** with `unavailable_critical_facts` list |

**Business rules enforced**

- **G-06:** No investing.com scrape in any chain.
- **Critical list ≤ 5 facts**, all marked `critical: true` in YAML.
- **Hold only on `unavailable`**, not on `stale` (workshop / PO convergence).
- **Signal monitor** (`build_market_facts` / P2-S14) unchanged — quoted facts are a separate path.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Yahoo chart HTTP API as “yfinance” primary** | Same data source yfinance uses; no new Python dependency; easy to mock in tests | Add `yfinance` package: heavier deps for Render |
| **Separate `MarketQuoteFact` vs extending `MarketFact`** | P2-S14 `MarketFact` is text + `observed_at` for Jaccard corroboration; chips need `fact_id`, `display_value`, tristate | Overload `MarketFact`: breaks signal_check contract |
| **Config in YAML (`critical_facts.yaml`)** | PO workshop: editable without deploy; matches `newsapi_keywords.yaml` pattern | Hardcode in Python: requires deploy for threshold tweaks |
| **Hold via exception + 423** | Clear API contract for editorial tools; distinct from 422 validation failures | Silent queue row: no schema added in S1f |
| **`pipeline_runs.status=held`** | Reuses P2-S13 telemetry table; observable in admin metrics | New `card_hold_queue` table: scope creep |
| **Public `GET /api/market-facts`** | Pulse/Thread need unauthenticated read (same as feed) | Embed facts in feed payload: couples caches |
| **CDSL portal as stub** | PRD2 names CDSL as fallback; no stable automated parser in Phase 3 | HTML scrape CDSL: brittle, deferred |

⚠️ **Do not remove the critical-facts check from `draft_card_from_event`** without PO approval — it is the G-06 “never silently drive cards on missing macro” rule.

⚠️ **Do not reintroduce investing.com** into fallback chains — explicit PO-08 rejection.

⚠️ **`unavailable` vs `stale` semantics:** missing data blocks drafting; old data does not. Reversing this breaks acceptance criteria 6.6 and user trust copy on chips.

**Assumptions**

- Editors interpret amber/red dots as “proceed with caution,” not “block publish” (publish gate remains G-07 number validator in later stories).
- Repo rate `config_fallback_value` (6.50%) is acceptable as last-resort stale input until RBI events feed mentions a newer rate.
- NSE/Yahoo may block datacenter IPs; degraded chips are an expected production state, not a bug by themselves.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Upstream** | **P3-S1c** dedup (milestone ordering); **P2-S14** `market_facts_adapters.py` merge helpers and NSE index fetchers reused |
| **Parallel** | Completed after S1c; independent of S1d/S1e feature code |
| **Downstream** | **P3-T2** integration gate (critical fact unavailable → card held); **P3-S1g** confidence scorer (separate concern) |

**Shared components touched**

- `market_facts_adapters.py` — extended (quoted facts + gate); P2 merge functions retained
- `card_pipeline.py` — gate at start of draft path
- `pipeline_runs` — append-only telemetry with `status=held`
- Pulse / Thread shells — new market facts strip
- `/admin/queue` — degradation banner

---

### A5. DESIGN CHOICES

**Architecture patterns**

- **Config loader** (`critical_facts_config.py`) mirrors `newsapi_config.py` (`@lru_cache`, YAML parse validation).
- **Chain registry** — `@_register_chain` decorator maps `_chain_{step}` functions to YAML step names.
- **Injectable `chain_fetchers` dict** in gate/build functions for unit tests without network.
- **Thin API router** (`market_facts.py`) over service functions.

**Database schema**

| Object | Change |
|--------|--------|
| _None_ | No migration in P3-S1f |

**API contracts**

| Method | Route | Auth | Purpose |
|--------|-------|------|---------|
| GET | `/api/market-facts` | None (public read) | Quoted facts + gate summary for UI |
| POST | `/api/cards/draft-from-event` | Existing | **Modified:** 423 when critical facts unavailable |

**UI/UX**

- **FreshnessDot:** green (`fresh`), amber (`stale`), red (`unavailable`).
- **MarketFactChips:** label + value + dot; dashed border when unavailable.
- **Pulse:** strip below Topbar.
- **Thread:** compact strip in sticky header.
- **Admin queue:** amber/red `Alert` when facts degraded or hold active.

**Libraries / tools**

| Library | Purpose |
|---------|---------|
| `httpx` | Yahoo chart, OXR, RBI ref, NSE FII API |
| `pyyaml` | `critical_facts.yaml` |
| Existing NSE index adapter | Secondary index/VIX levels |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `critical_facts.yaml` | `backend/app/config/critical_facts.yaml` | Five critical facts, staleness thresholds, fallback chains |
| `critical_facts_config.py` | `backend/app/services/critical_facts_config.py` | YAML loader + typed config |
| `market_facts.py` (API) | `backend/app/api/market_facts.py` | `GET /api/market-facts` |
| `test_market_facts_freshness.py` | `backend/tests/test_market_facts_freshness.py` | Tristate, chain, gate, pipeline hold tests |
| `types.ts` | `frontend/lib/marketFacts/types.ts` | TS types for API response |
| `useMarketFacts.ts` | `frontend/lib/marketFacts/useMarketFacts.ts` | Client fetch hook |
| `FreshnessDot.tsx` | `frontend/components/market-facts/FreshnessDot.tsx` | Green/amber/red dot |
| `FreshnessDot.test.tsx` | `frontend/components/market-facts/FreshnessDot.test.tsx` | A11y label tests |
| `MarketFactChips.tsx` | `frontend/components/market-facts/MarketFactChips.tsx` | Chip row component |
| `MarketFactsBanner.tsx` | `frontend/components/market-facts/MarketFactsBanner.tsx` | Editorial queue alerts |
| `MarketFactsStrip.tsx` | `frontend/components/market-facts/MarketFactsStrip.tsx` | Hook + chips wrapper for Pulse/Thread |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `market_facts_adapters.py` | `backend/app/services/market_facts_adapters.py` | `MarketQuoteFact`, chain fetchers, gate, macro line formatter; P2 merge helpers preserved |
| `card_pipeline.py` | `backend/app/services/card_pipeline.py` | Critical-facts gate before LLM; macro lines in evidence; `held` telemetry |
| `cards.py` | `backend/app/api/cards.py` | Map `CriticalFactsHoldError` → HTTP 423 |
| `settings.py` | `backend/app/core/settings.py` | `OPEN_EXCHANGE_RATES_APP_ID` setting |
| `main.py` | `backend/app/main.py` | Register `market_facts_router` |
| `test_card_pipeline.py` | `backend/tests/test_card_pipeline.py` | Mock `assert_critical_facts_available` in happy-path test |
| `test_newsapi_scheduler.py` | `backend/tests/test_newsapi_scheduler.py` | Dynamic `publishedAt` in fixtures (date drift fix; unrelated regression) |
| `PulseClient.tsx` | `frontend/app/(app)/pulse/_components/PulseClient.tsx` | `MarketFactsStrip` below Topbar |
| `ThreadExperience.tsx` | `frontend/app/(app)/thread/_components/ThreadExperience.tsx` | Compact `MarketFactsStrip` in header |
| `page.tsx` | `frontend/app/admin/queue/page.tsx` | `MarketFactsBanner` + `useMarketFacts` |
| `finnwise-phase3-implementation-tasks.md` | `docs/plans/finnwise-phase3-implementation-tasks.md` | P3-S1f AC + tasks **6.0**–**6.6** marked complete |

**Not modified (intentionally)**

| File | Note |
|------|------|
| `signal_monitor_runner.py` | P2-S14 corroboration path unchanged |
| `market_facts.py` (service) | Event/NSE merge for signal monitor unchanged |
| DB migrations | No schema change required |

---

### A8. TESTS EXECUTED

| Test file | Test function | Status | What it verifies |
|-----------|---------------|--------|------------------|
| `test_market_facts_freshness.py` | `test_classify_freshness_tristate` | **Pass** | fresh / stale / unavailable age boundaries |
| `test_market_facts_freshness.py` | `test_resolve_quote_fact_uses_fallback_chain` | **Pass** | Primary fail → secondary succeeds; stale classification |
| `test_market_facts_freshness.py` | `test_unavailable_critical_fact_blocks_gate` | **Pass** | All critical facts missing → `blocked` |
| `test_market_facts_freshness.py` | `test_stale_critical_fact_allows_gate_with_flag` | **Pass** | Stale critical → not blocked; `has_stale_critical` |
| `test_market_facts_freshness.py` | `test_assert_critical_facts_available_raises` | **Pass** | Exception carries fact IDs |
| `test_market_facts_freshness.py` | `test_critical_facts_config_loads_five_facts` | **Pass** | Production YAML has 5 critical facts |
| `test_market_facts_freshness.py` | `test_draft_card_held_when_critical_facts_unavailable` | **Pass** | No LLM slot / no insert on hold |
| `test_market_facts_freshness.py` | `test_draft_card_proceeds_when_only_stale_critical_facts` | **Pass** | `consume_slot_or_raise` called when only stale |
| `test_market_facts_freshness.py` | `test_build_quoted_market_facts_returns_all_configured_rows` | **Pass** | One row per configured fact |
| `test_card_pipeline.py` | `test_draft_card_pipeline_mocked_llm` | **Pass** | Gate mocked fresh; full pipeline smoke |
| `test_card_pipeline.py` | `test_cards_migration_has_budget_function` | **Pass** | Unrelated migration contract regression |
| `FreshnessDot.test.tsx` | three label tests | **Pass** | Accessible freshness labels |
| `test_market_facts_merge.py` | (5 tests) | **Pass** | P2-S14 merge regression |
| `test_nse_facts_adapter_contract.py` | (4 tests) | **Pass** | NSE adapter regression |

**Commands used**

```bash
python -m ruff check backend
python -m pytest -q backend/tests
cd frontend && pnpm lint && pnpm typecheck && pnpm test && pnpm build
```

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**None.** Freshness and hold state are computed at request time from external APIs + config. Pipeline hold events are logged in existing `pipeline_runs.context` JSON (`unavailable_critical_facts` array) with `status='held'`.

---

### B2. API / INTEGRATION CONTRACTS

**Market facts (public)**

```http
GET /api/market-facts
```

Example response shape:

```json
{
  "facts": [
    {
      "fact_id": "inr_usd",
      "label": "INR/USD",
      "display_value": "84.12",
      "observed_at": "2026-05-31T10:00:00Z",
      "source": "yfinance",
      "freshness_status": "fresh"
    }
  ],
  "degraded": false,
  "unavailable_critical": [],
  "has_stale_critical": false,
  "reference_time": "2026-05-31T12:00:00Z"
}
```

**Draft card hold**

```http
POST /api/cards/draft-from-event
Content-Type: application/json

{ "event_id": "<uuid>" }
```

When critical facts unavailable:

```json
HTTP/1.1 423 Locked

{
  "detail": {
    "code": "critical_facts_held",
    "message": "critical facts unavailable: inr_usd, fii_net",
    "unavailable_critical_facts": ["inr_usd", "fii_net"]
  }
}
```

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Freshness classification**

```
has_value?
  no  → unavailable
  yes → age ≤ fresh_max_hours (24) → fresh
        age ≤ stale_max_hours (72) → stale
        else → stale (still has a number; UI shows warning)
```

**Gate decision**

```
for each fact in critical_facts.yaml where critical=true:
  if freshness_status == unavailable → add to unavailable_critical

blocked = len(unavailable_critical) > 0
```

**Card pipeline sequence (simplified)**

```
fetch_event_row
→ assert_critical_facts_available()  # may raise CriticalFactsHoldError
→ build_evidence_layer(..., macro_fact_lines)
→ check_monthly_budget / consume_slot / LLM calls / persist
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Detail |
|------|--------|
| **CDSL portal stub** | `_fetch_cdsl_portal_stub()` always returns `None` — FII often unavailable if NSE CSV fails |
| **RBI ref scrape** | HTML regex on reference rate archive — brittle; last resort in INR/USD chain |
| **Repo rate fallback** | Static 6.50% in YAML may be stale vs live RBI policy |
| **No caching on `/api/market-facts`** | Every Pulse/Thread load hits adapters; acceptable for Phase 3 volume |
| **Yahoo/NSE IP blocking** | Production Render IP may see empty chains → hold gate fires frequently until fallbacks configured |
| **Dual fact models** | `MarketFact` (signal monitor) vs `MarketQuoteFact` (UI/gate) — consolidate only with PO review |

---

### B5. TESTING NOTES

- **Automated:** All gate logic tested with injected `chain_fetchers` — no live Yahoo/NSE in unit tests.
- **Not automated:** End-to-end browser verification of chips against live APIs; P3-T2 will add cross-service integration fixture.
- **Manual smoke (recommended post-deploy):**
  1. Open `/pulse` — chips render with dots.
  2. Open `/admin/queue` — banner absent when all facts fresh; visible when degraded.
  3. Trigger `draft-from-event` when facts unavailable — expect 423.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPEN_EXCHANGE_RATES_APP_ID` | Optional | INR/USD fallback step `open_exchange_rates` |
| Existing `SUPABASE_DB_URL` | Yes (draft path) | Unchanged; gate runs before DB-heavy LLM work |

**Deployment:** Deploy backend before or with frontend — chips call `/api/market-facts` on the FastAPI service (or `/backend` proxy on Vercel).

**Tuning without code deploy:** Edit `backend/app/config/critical_facts.yaml` (thresholds, fallback order, repo fallback value). Restart backend to clear `@lru_cache` on config loader if hot-reload is not used.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before touching this code**

1. Read G-06 in `FinnWise_PRD2_SSA_Solution_Design.md` — hold vs stale is a PO decision.
2. Distinguish **signal monitor facts** (`market_facts.py` / `MarketFact`) from **quoted chips** (`build_quoted_market_facts` / `MarketQuoteFact`).
3. Adding a new critical fact: update YAML (keep ≤5), implement chain step as `_chain_{name}` in `market_facts_adapters.py`, add test coverage in `test_market_facts_freshness.py`.

**Common mistakes**

- Treating **stale** as blocking — only **unavailable** blocks drafting.
- Calling external APIs in tests without mocking `chain_fetchers`.
- Removing macro lines from evidence when gate passes — LLM should see chip snapshot in `macro_stub`.

**Key file paths**

| Concern | Path |
|---------|------|
| Config | `backend/app/config/critical_facts.yaml` |
| Loader | `backend/app/services/critical_facts_config.py` |
| Chain + gate | `backend/app/services/market_facts_adapters.py` |
| Pipeline hold | `backend/app/services/card_pipeline.py` |
| Public API | `backend/app/api/market_facts.py` |
| UI components | `frontend/components/market-facts/*` |
| Client hook | `frontend/lib/marketFacts/useMarketFacts.ts` |

**Contact for product context:** Product Owner — critical fact list membership and hold-vs-stale policy (G-06).

---

## Quick operator checklist

| Step | Action |
|------|--------|
| 1 | Deploy backend + frontend |
| 2 | (Optional) Set `OPEN_EXCHANGE_RATES_APP_ID` on Render |
| 3 | Verify `GET /api/market-facts` returns five facts |
| 4 | Confirm Pulse/Thread chips and admin queue banner |
| 5 | Proceed to **P3-T2** data pipeline integration test gate |
