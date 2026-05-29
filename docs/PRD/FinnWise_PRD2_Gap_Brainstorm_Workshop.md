# FinnWise PRD 2 — Gap Brainstorm Workshop (Full)

> **Companion to:** `FinnWise_PRD2_Intelligence_Architecture.md`  
> **Goal:** Extreme brainstorming across all 15 gaps via structured multi-persona debate. Surface alternatives, stress-test PRD2 baselines, and produce PO decision blocks before SSA solution design.  
> **Status:** Complete workshop — awaiting PO decisions on flagged items.

---

## Personas

| Role | Name | Mandate |
|------|------|---------|
| **SPM** — Senior Product Manager | **Priya** | Customer-obsessed serial AI startup founder. Pushes simplest, trust-building, fully functional UX. Budget is zero within PRD2 constraints. Every decision must have a clear user-visible definition. |
| **INT** — Senior Interrogator | **Vikram** | Devil's advocate. Stress-tests SPM claims against solo-builder reality, Render free tier, no live data, SEBI exploratory posture. Keeps the build real. |
| **DEV** — Senior Developer | **Matt Padock** | 100+ AI projects delivered on this stack (FastAPI, Supabase/Postgres, Next.js, Gemini, GitHub Actions, Render). Knows every pitfall PMs hit when hypothesising customer problems. Einstein-level systems thinking. |
| **SSA** — Senior Solutions Architect | **Arjun** | Silent until PO decides. Network-aware, performance-first. Translates final decisions into implementable architecture. Output in separate file. |
| **PO** — Senior Product Owner | **You** | Final call on critical trade-offs where SPM ↔ INT ↔ Matt do not converge cleanly. |

---

## Workshop Rules

1. SPM, INT, and Matt debate **each gap for at least 4 rounds** before converging.
2. PRD2's proposed answer is treated as **Option A baseline** — not assumed correct.
3. Each gap closes with an **Options for PO** table (2–3 distinct paths).
4. PO answers decision questions. SSA (Arjun) writes solution design in `FinnWise_PRD2_SSA_Solution_Design.md`.
5. Non-negotiables from PRD2 Section 10 carry forward unchanged.

---

## Cross-Cutting Themes (Emergent Across All Gaps)

Before diving gap-by-gap, three themes surfaced repeatedly:

| Theme | SPM view | INT view | Matt view |
|-------|----------|----------|-----------|
| **Explainability over magic** | Users must see *why* a card exists | Explainability UI is worthless if upstream routing is wrong | Build explainability into API responses first; UI is a thin layer |
| **Synthetic-first, honest labels** | Seed data must never pollute user trust metrics | Synthetic rows must be invisible to users but visible to builder | `is_synthetic` filter must be enforced at DB RLS + service layer — not just query strings |
| **Solo-builder operational load** | Editor burnout is a product failure | Every "manual tick" is a future skip | Automate everything that can be regex-checked; manual ticks only where legally/ editorially required |

---

# Layer 1 — Confidence Scoring

---

## G-01 — Confidence Score Methodology Is a Black Box (P0)

**PRD2 baseline:** Rule-based weighted scorer — source_count (35%), source_quality (30%), factor_db_match (25%), recency (10%). Config in `confidence_config.py`.

**Current codebase reality:** `confidence_gate.py` routes on direct/partial source *counts*, not numeric 0–1 score. PRD2 replaces this entirely.

### Round 1

**Priya (SPM):** Customers don't trust algorithms — they trust evidence they can see. Keep a numeric score for internal routing, but expose a **5-dot "Sourcing Strength"** UI fed by source tier × count. Every card gets a tap-to-expand "Why this confidence?" panel showing the four input contributions and source list with timestamps. Score is a side effect of explainability, not the headline.

**Vikram (INT):** Hiding the number behind dots doesn't fix routing. "N reputable sources within M hours" is literally PRD2's formula. Without numeric cutoffs, editorial queue rules collapse. You've solved perception and left routing untouched.

**Matt (DEV):** Priya's UI is right for trust; Vikram's routing concern is right for correctness. The real blocker is that Phase 1's `confidence_gate.route()` uses a completely different model (3+ direct sources = HIGH). Migrating to PRD2's float scorer means rewriting the gate *and* backfilling `confidence_raw` on existing events. I'd ship the scorer as a pure function in `confidence_scorer.py`, unit-test it against 20 synthetic events, then swap the gate. Don't try to bridge the two models — pick one.

### Round 2

**Priya:** Keep PRD2's numeric scorer. Add explainability on top — every card exposes four input contributions inline. When a card is wrong, users must see whether it was thin sourcing, stale data, or Factor DB miss.

**Vikram:** That's a UI feature, not a methodology fix. G-01 asks for inputs, weights, output format — PRD2 answers all three. The real risk: weights (0.35/0.30/0.25/0.10) are vibes. Worse: three NewsAPI results parroting the same PTI wire story scores source_count = 3 but it's one story.

**Matt:** Wire inflation is the killer. Option (a): publisher-graph dedup — expensive, fragile. Option (b): count sources *post* G-03 dedup_key merge — free, already on the roadmap. I'd also add `unique_publisher_count` as a fifth input at 5% weight, carved from recency's 10% → 5%. Regex on `source_domain` from Evidence URLs — no graph needed. Existing `sources/base.py` already has URL normalisation for dedupe keys.

### Round 3

**Priya:** Option (b) — post-dedup source counting. Weights stay; input gets cleaner. Add `source_count > 5` guardrail → force editorial review regardless of score. Cheap insurance against dedup bugs.

**Vikram:** Accepted, but G-01 now depends on G-03 being live first. If dedup breaks, scorer silently inflates. Also: who recalibrates weights after launch? Manual eyeballing = unreproducible system.

**Matt:** Dependency is real — build order: G-03 migration → scorer → gate swap. For recalibration: tie to G-11 override log. If monthly false-positive rate exceeds 10%, auto-flag `confidence_config.py` for review. Don't auto-change weights — solo builder decides. I'll add `confidence_score_audit` table: event_id, raw inputs JSON, computed score, scorer_version. Makes every score reproducible.

### Round 4

**Priya:** Converged shape: (1) PRD2 rule-based scorer; (2) post-dedup source_count; (3) optional `unique_publisher_count` at 5%; (4) "Why this confidence?" breakdown in API + UI; (5) `source_count > 5` → editorial escalation; (6) `confidence_score_audit` for reproducibility; (7) recalibration trigger via G-11 override rate.

**Vikram:** Live with it. Two PO nits: initial weights need defensible starting point before Week 2 calibration; re-calibration trigger must be defined now, not "whenever builder feels like it."

**Matt:** Implementation note: replace `confidence_gate.route()` entirely. New flow: `compute_confidence(event) → float → tier_from_threshold(float)`. Existing tests in `test_fog_of_war_detector.py` need updating since FoW will read `is_major` not card counts. Estimate: 2 days scorer + 1 day gate swap + 1 day audit table.

### Options for PO — G-01

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 baseline as-is. Fixed weights. Week 2 calibration only. | Fastest. Wire inflation unaddressed. |
| **B** ★ | PRD2 + post-dedup counting + audit table + `source_count > 5` guardrail + explainability API/UI + G-11-linked recalibration trigger. | +3–4 days build. Significantly more auditable. |
| **C** | LLM-as-judge (Gemini Pro one-shot rubric rating). | Abandons debuggability. Adds per-event LLM cost. |

#### 🔴 PO Decision — G-01

1. **Option A, B, or C?** (Consensus: **B**)
2. **Add `unique_publisher_count` (5% weight)?** Yes / No
3. **"Why this confidence?" UI — Phase 3 must-have or Phase 4 polish?**
4. **Re-calibration trigger:** time-based (monthly) / event-count / override-rate drift (consensus: override-rate ≥ 10% monthly)

---

## G-02 — HIGH/MEDIUM/LOW Threshold Values Are Arbitrary (P0)

**PRD2 baseline:** HIGH ≥ 0.75, MEDIUM ≥ 0.45, LOW < 0.45. Calibrate Week 2 against 10 historical events.

### Round 1

**Priya:** Thresholds should reflect editor operational load. If solo editor can handle 8 HIGH cards/day, set HIGH threshold so ~8/day cross it. Workload-driven, not math-driven.

**Vikram:** That's load-shedding. You'd downgrade a genuinely high-confidence event because the editor is tired. Inverts the user contract.

**Matt:** Workload framing is wrong abstraction. Thresholds should map to *signal quality tiers* that the editor can validate quickly. HIGH = "auto-draft, 2-hour override" means the system is confident enough to act without waiting. I'd instrument the editorial queue first: log time-to-review per tier. Then calibrate thresholds against editor SLA, not card count.

### Round 2

**Priya:** Reframed: keep 0.75/0.45 defaults but make them living numbers anchored to override rate. Monthly: how many HIGH cards got overridden as wrong? Tune to keep override ≤ 10% (G-11 target).

**Vikram:** G-02 now depends on G-11 being live 30+ days. First 30–60 days run on arbitrary numbers — the gap we're closing stays open for 60 days.

**Matt:** Honest framing is fine. Bootstrap with synthetic seed: run scorer against 20 events, hand-grade expected tier, tune thresholds until ≥ 80% match. Label as "author-classified provisional." After Day 60, override rate drives tuning. I'd store thresholds in `confidence_config.py` with a `calibration_status: provisional | validated` enum.

### Round 3

**Priya:** Accepted. Initial 0.75/0.45 labelled "provisional — not yet data-driven." Re-calibrate Day 30 and Day 60 from G-11 log. Target override ≤ 10%.

**Vikram:** MEDIUM band is 0.45–0.75 — 30 points of ambiguous middle. Every event there hits editorial queue. Narrow MEDIUM (0.55–0.75) sends more to LOW silent-log, saves editor cycles, risks missing borderline events.

**Matt:** The MEDIUM band width is the biggest operational lever. With solo builder, I'd start narrow: HIGH ≥ 0.75, MEDIUM 0.55–0.74, LOW < 0.55. Widen only if override log shows missed real events in LOW. Also: FoW dampener (0.6×) will push HIGH events to MEDIUM during storms — factor that into threshold design or editors get flooded exactly when markets are chaotic.

### Round 4

**Priya:** FoW interaction is critical UX. During Fog of War, show banner explaining *why* tiers shifted — "3 major events active; confidence dampened." Don't silently downgrade.

**Vikram:** Agreed on banner. PO must pick MEDIUM band width and whether FoW dampener applies before or after tier assignment (PRD2 says before — raw score multiplied, then tiered).

**Matt:** PRD2 order is correct: dampen raw, then tier. Implementation: `effective_score = raw * (FOG_DAMPENER if fog_active else 1.0)`. Store both `confidence_raw` and `confidence_effective` on events row. FoW must never mutate raw in place (PRD2 Section 10 non-negotiable). `card_confidence_history` gets effective score snapshots.

### Options for PO — G-02

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 baseline: 0.75/0.45, Week 2 calibration, then locked. | Simplest. Frozen on Day 0 opinion. |
| **B** ★ | Provisional 0.75/0.45; re-calibrate Day 30/60 from override rate; dual storage raw + effective. | Honest uncertainty. Real data after 60 days. |
| **C** | Same as B but narrow MEDIUM: 0.55–0.74. | Less editor load. Risk missing borderline events. |

#### 🔴 PO Decision — G-02

1. **Option A, B, or C?** (Consensus: **B** or **C**)
2. **Override-rate target:** confirm ≤ 10% or different?
3. **MEDIUM band:** wide (0.45–0.75) or narrow (0.55–0.74)?
4. **Same recalibration trigger as G-01 weights?** Yes (unified) / No (separate)

---

# Layer 2 — Data Pipeline Integrity

---

## G-03 — De-duplication Logic Undefined (P0)

**PRD2 baseline:** SHA-256 of `event_category + normalise(entity) + date_floor_4h(detected_at)`. UPSERT on conflict, increment source_count.

### Round 1

**Priya:** Dedup must be invisible to users — they see one card per real-world event, with a "Reported by 4 sources" badge. That's the trust signal.

**Vikram:** Invisible is fine until dedup *merges two different events* because entity normalisation is too aggressive. "RBI rate hold" and "RBI liquidity injection" both normalise to `rbi` — merged wrongly.

**Matt:** Category is in the key — `RBI_POLICY` vs `LIQUIDITY` are different categories. Risk is within-category: two distinct RBI announcements same day. 4-hour window helps but MPC + separate circular same afternoon could collide. Mitigation: include `headline_hash` (first 100 chars normalised) as optional fourth key component when category is `RBI_POLICY` or `REGULATORY`.

### Round 2

**Priya:** Add source accumulation UX: when dedup merges, show all sources with individual retrieved-at timestamps in Evidence layer.

**Vikram:** Evidence layer is card-level, not event-level. Dedup happens pre-card. Don't conflate event dedup with card evidence.

**Matt:** Correct separation. Event dedup → one `events` row with `sources[]` array. Card generation pulls from that row. Migration `0006_events_dedupe_newsapi_quota.sql` exists — I'll extend it with `dedup_key` column + unique index. Entity map starts at 30 entries, grows via config file not code deploy. `ON CONFLICT` recomputes score — already in PRD2 spec.

### Round 3

**Priya:** What about same event, different categories? Crude spike tagged `CRUDE_SHOCK` by NewsAPI and `GLOBAL_MACRO` by RSS?

**Vikram:** That's a classification problem, not dedup. If categories differ, they're different keys — duplicate cards. Editor merges manually.

**Matt:** Add post-dedup **similarity flag**: if two events same entity + same 4h window but different category, log to `dedup_review_queue` for Sunday review. Don't auto-merge across categories. Cheap heuristic: Levenshtein on headline > 0.85 → flag.

### Round 4

**Priya:** Sunday review slot already exists for G-05 watchlist. Bundle dedup_review_queue into same 30-min session.

**Vikram:** Don't expand Sunday session scope every gap — it'll become 3 hours. Cap review queue at 10 items/week; overflow → auto-close oldest.

**Matt:** Converged: PRD2 composite key + entity map in config + `dedup_review_queue` for cross-category collisions + recompute score on merge. Build before G-01 scorer goes live.

### Options for PO — G-03

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 baseline key only. | Fast. Cross-category dupes possible. |
| **B** ★ | PRD2 + `dedup_review_queue` for cross-category same-window collisions. | +0.5 day. Catches edge cases. |
| **C** | Add headline_hash to key for all events. | Fewer dupes. More false merges. |

#### 🔴 PO Decision — G-03

1. **Option A, B, or C?** (Consensus: **B**)
2. **Include headline_hash for RBI_POLICY/REGULATORY only?** Yes / No / All categories

---

## G-04 — NewsAPI Keyword Filters Never Defined (P1)

**PRD2 baseline:** 8 factor keyword sets, 100 calls/day allocated proportionally.

### Round 1

**Priya:** Keywords must map 1:1 to user-visible Factor DB labels. When a card fires, user sees "Touches: Domestic interest rates, Global risk sentiment" — same language as keyword sets.

**Vikram:** 100 calls/day is a hard ceiling. 8 factors × rotation = each factor polled ~every 2.4 hours. Slow-burn monsoon deficit won't hit keywords until next cycle — acceptable?

**Matt:** NewsAPI free tier also limits to 1 month history and 100 req/day. I'd implement a **round-robin scheduler** in the adapter: each cron tick fires one factor's keyword set, not all 8. 4-hour detection cron × 6 ticks/day × ~16 calls/tick = 96 calls. Buffer 4 for manual dispatch. Keyword list in `backend/app/config/newsapi_keywords.yaml` — editable without deploy.

### Round 2

**Priya:** Volatile factors (crude, INR/USD, RBI) should get more calls. PRD2 allocation (crude 15, rates 20) is right. Show "last checked" timestamp per factor in admin/editor view.

**Vikram:** Admin UI for factor freshness is scope creep for solo builder. Log it; don't UI it yet.

**Matt:** Agree — log `last_factor_poll_at` in DB, surface in editorial digest email only. Adapter returns `{ factor, articles[], polled_at }`. Existing NewsAPI adapter gets refactored, not replaced.

### Round 3

**Priya:** Fallback when NewsAPI returns zero results for a factor — is that "no news" or "adapter broken"?

**Vikram:** Critical distinction. Zero results + 200 OK = no news. 429/401 = broken, trigger G-06 fallback chain.

**Matt:** Status code handling in adapter base class. Zero-result gets logged as `poll_status: empty` not `error`. After 3 consecutive empties for same factor, escalate to watchlist (G-05) as "monitoring gap." RSS fallback from G-06 kicks in on 429 only.

### Round 4

**Converged:** PRD2 keyword sets in YAML config. Round-robin scheduler respecting 100/day cap. Volatile factor weighting per PRD2 table. Log freshness, no admin UI. Empty-vs-error distinction. RSS fallback on rate limit.

### Options for PO — G-04

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 baseline keywords in Python dict. | Fast. Requires deploy to tune. |
| **B** ★ | YAML config + round-robin + empty/error distinction + digest surfacing. | +1 day. Operable without deploy. |

#### 🔴 PO Decision — G-04

1. **Option A or B?** (Consensus: **B**)
2. **Adjust PRD2 call allocation or keep as-is?**

---

## G-05 — Slow-Burn Watchlist Completely Unspecified (P1)

**PRD2 baseline:** `watchlist_items` DB table. 5 seed categories. Sunday 30-min review.

### Round 1

**Priya:** Slow-burn is the highest-value source for a thoughtful investor app. Monsoon, budget cycle, regulatory reviews — these need weeks of lead time. UI: dedicated "Watchlist" tab in Pulse with status chips (watching / escalated / closed).

**Vikram:** Dedicated tab is Phase 4 polish. Solo builder will skip watchlist maintenance without frictionless process. Sunday 30-min is already committed for G-03 review queue — don't add another ritual.

**Matt:** No new tab. Surface watchlist items in **daily editorial digest email** + inline in editorial queue as "slow-burn candidates." Table per PRD2 schema. Seed 5–10 items via migration. Escalation trigger is the hard part — make it a simple SQL boolean eval, not LLM.

### Round 2

**Priya:** Escalation examples: "IMD monsoon forecast revised downward > 5%" → auto-create event. "SEBI consultation paper published" → auto-create event.

**Vikram:** Auto-create from watchlist requires monitoring adapters for IMD, SEBI — that's new scrapers. Scope explosion.

**Matt:** Phase 3 scope: **manual escalation only.** Editor clicks "Escalate to event" in Sunday review. Phase 4: add RSS monitors for IMD/SEBI that match `escalation_trigger` regex against watchlist items. Don't build auto-escalation now.

### Round 3

**Priya:** Manual escalation is fine if the UI is one click from digest email deep link.

**Vikram:** Deep link to editorial watchlist view — not a new app section. Single page at `/editor/watchlist`.

**Matt:** Minimal `/editor/watchlist` page: table of items, status dropdown, "Escalate" button → creates `events` row with `source='watchlist'` and pre-filled category. 4 hours frontend + backend.

### Round 4

**Converged:** PRD2 table + 5 seed items + Sunday review bundled with dedup queue + `/editor/watchlist` page + manual escalation only + digest email surfacing.

### Options for PO — G-05

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 table + manual Sunday review only. No UI. | Cheapest. High skip risk. |
| **B** ★ | Table + `/editor/watchlist` + digest + manual escalate. | +0.5 day. Sustainable process. |
| **C** | Auto-escalation via IMD/SEBI monitors. | Best UX. +1 week. Out of Phase 3 scope. |

#### 🔴 PO Decision — G-05

1. **Option A, B, or C?** (Consensus: **B**)

---

## G-06 — yfinance and NSE Scraper Fragility (P1)

**PRD2 baseline:** Per-data-type fallback chains. Staleness flags. Red freshness dot.

### Round 1

**Priya:** Users see a freshness dot on every market fact chip. Red dot = "data may be stale, treat accordingly." Never show a number without a dot.

**Vikram:** investing.com scrape as fallback is legally grey and breaks monthly. Don't build on sand.

**Matt:** Agree — drop investing.com scrape from fallback chain. Revised chain: yfinance → Open Exchange Rates (currency) → manual entry + staleness flag. For NSE FII/DII: NSE CSV → CDSL portal → stale flag. No HTML scraping in Phase 3 except RBI reference rate (stable page structure). Screener.in stays manual-only per PRD2.

### Round 2

**Priya:** When primary fails, should card generation pause or proceed with stale data?

**Vikram:** Proceed with stale + red dot. Pausing stops the editorial pipeline for scraper blips.

**Matt:** `market_facts_adapters.py` already merges streams with dedup. I'll add `freshness_status: fresh | stale | unavailable` per fact. Card pipeline checks: if critical fact (INR/USD, Nifty) is `unavailable`, hold card in queue. If `stale`, proceed with MEASURED badge + red dot.

### Round 3

**Priya:** "Critical fact" list should be tiny — INR/USD, repo rate, Nifty 50. Everything else can be stale.

**Vikram:** Who defines critical? Hardcode in config or Factor DB metadata?

**Matt:** `critical_facts.yaml` — 5 entries max. Checked at card generation. Nightly NLP job (P3-S1a) adds scraper exposure — run it on GitHub Actions (G-12), not Render. Filings PDF source uses NSE API where possible, not scrape.

### Round 4

**Converged:** Revised fallback chains (no investing.com). Freshness tristate. Critical fact gate pauses card gen. Config-driven critical list. NSE via CSV/API not HTML scrape where possible.

### Options for PO — G-06

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 fallback chains as-written. | Includes investing.com scrape risk. |
| **B** ★ | Revised chains + freshness tristate + critical fact gate. | Safer. -1 fallback for EOD prices. |

#### 🔴 PO Decision — G-06

1. **Option A or B?** (Consensus: **B**)
2. **Critical facts list:** PRD2 implicit / explicit 5-item config?

---

# Layer 3 — LLM Pipeline Integrity

---

## G-07 — Post-Generation Validation — No Hard Publish Gate (P0)

**PRD2 baseline:** `number_validator.check()` returns PASS/FAIL. Publish disabled until PASS. No override.

**Current codebase:** `number_validator.py` exists. `card_pipeline.py` imports it. Unknown if it's a hard gate in UI.

### Round 1

**Priya:** This is the #1 trust mechanism. Publish button literally does not exist until every number traces to Evidence. Show structured diff: "Sentence 3: '87.2' has no Evidence row."

**Vikram:** Solo builder reviewing own AI output will click through. Hard gate only works if the UI makes fixing faster than bypassing — and there's no bypass.

**Matt:** Read the code: `validate_numbers_in_evidence` exists but Publish button likely doesn't enforce it yet. I'll wire: backend `POST /cards/{id}/publish` returns 422 if validator fails; frontend disables button on card load when status != PASS. No override endpoint. Period.

### Round 2

**Priya:** What about non-numeric claims? "Significantly higher inflation" — no number but still a quantitative claim.

**Vikram:** Scope creep. PRD2 says numbers. Qualitative inflation claims are editor's manual checklist item (G-15).

**Matt:** Regex extractor per PRD2 spec. Add one enhancement: detect comparative quantifiers ("doubled", "tripled", "record high") and flag for manual review — soft warning, not hard gate. Hard gate stays numbers-only.

### Round 3

**Priya:** Structured diff must show which Evidence row to add, with a one-click "Add Evidence" prefilled with the flagged number.

**Vikram:** Nice UX, not Phase 3 blocker. Editor can add Evidence row manually.

**Matt:** Phase 3: structured diff list. Phase 4: one-click Evidence prefilled. Backend returns `{ fail_reasons: [{ sentence, number, suggested_action }] }`. Frontend renders list. 1 day backend, 0.5 day frontend.

### Round 4

**Converged:** Hard gate, no override, backend 422 + frontend disabled Publish. Numbers-only regex validation. Structured diff response. Comparative quantifier soft flag (log only).

### Options for PO — G-07

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 hard gate, minimal error message. | Fast. |
| **B** ★ | Hard gate + structured diff + comparative quantifier soft flag. | +1.5 days. Better editor UX. |

#### 🔴 PO Decision — G-07

1. **Option A or B?** (Consensus: **B**)

---

## G-08 — Gemini vs Smaller Model for Phase 3 NLP (P1)

**PRD2 baseline:** Gemini Flash for P3-S1a filings extraction. Gemini Pro for 3-call card synthesis.

### Round 1

**Priya:** Users don't care which model — they care that extracted filing data is accurate. Flash is fine if validated.

**Vikram:** Flash hallucinates on edge-case financial tables. One wrong extracted JSON poisons Factor DB.

**Matt:** Flash + `source_guard` (PRD2 G-01a) is the right stack. Extraction prompt includes source excerpt; post-extraction validation checks every extracted number exists in source text via substring match. If fail → reject row, log, don't write to DB. Pro is 10× cost for marginal quality gain on JSON extraction. I've shipped this pattern 40+ times.

### Round 2

**Priya:** Model version drift — `gemini-1.5-flash` vs `gemini-2.0-flash-lite`?

**Vikram:** Pinning old models that get deprecated breaks nightly job silently.

**Matt:** Config-driven model ID in env var `NLP_EXTRACTION_MODEL`. Default to latest Flash at deploy time. Health check in workflow validates model responds before batch run. Fallback: if Flash fails 3×, abort job (don't silently switch to Pro — cost spike).

### Round 3

**Priya:** Extraction output must use same MMJ tagging as card pipeline.

**Vikram:** Obviously. Don't invent new taxonomy.

**Matt:** Extraction schema: `{ field, value, mmj_tag, source_excerpt, source_url }`. Same enum as cards. Written to `factor_db_extractions` table, not directly to Factor DB master — editor approves bulk.

### Round 4

**Converged:** Gemini Flash + source_guard + config-driven model ID + workflow health check + extraction approval queue.

### Options for PO — G-08

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 Flash baseline. | Good enough. |
| **B** ★ | Flash + source_guard + approval queue + model config. | +1 day. Safer DB writes. |
| **C** | Gemini Pro for extraction. | Higher cost. Marginal quality gain. |

#### 🔴 PO Decision — G-08

1. **Option A, B, or C?** (Consensus: **B**)

---

## G-09 — Editorial Rejection Loop (P2)

**PRD2 baseline:** Targeted section regen by default. Full regen logged and capped at 2.

### Round 1

**Priya:** Editor rejects "Insight" section — only Insight regenerates. Other approved sections untouched. Editor sees diff of what changed.

**Vikram:** Partial regen can create internal contradictions between Insight and Context.

**Matt:** Regen prompt includes other sections as read-only context. Post-regen: run number_validator + consistency check (simple: extract entity names from approved sections, verify no conflicts in regen section). 1 LLM call per regen, not 3.

### Round 2

**Priya:** Full regen should require confirmation dialog: "This will regenerate all sections and cost ~3× tokens."

**Vikram:** Solo builder knows the cost. Dialog is annoying on call 3.

**Matt:** Dialog only when `full_regen_count >= 1`. First full regen is silent. Second requires confirm. Third blocks until PO review flag cleared.

### Round 3

**Priya:** Editor annotation max 500 chars — enough?

**Vikram:** More than enough. If editor needs more, the card is fundamentally wrong → full regen.

**Matt:** `POST /api/cards/{id}/regenerate-section` per PRD2 spec. Store `regen_history[]` JSONB on card row: `{ section, editor_note, timestamp, model, tokens_used }`.

### Round 4

**Converged:** PRD2 targeted regen default + consistency check post-regen + tiered full regen confirmation + regen_history audit.

### Options for PO — G-09

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 baseline. | Minimal. |
| **B** ★ | + consistency check + tiered full regen confirm + regen_history. | +1 day. Safer partial regen. |

#### 🔴 PO Decision — G-09

1. **Option A or B?** (Consensus: **B**)

---

# Layer 4 — Fog of War and Signal Model

---

## G-10 — Fog of War Major Event Trigger Undefined (P0)

**PRD2 baseline:** `is_major` boolean on events. TRUE when confidence ≥ 0.75 AND factor_match ≥ 2 AND category in qualifying set. FoW when 3+ active is_major events.

**Current codebase:** `detect_fog_of_war()` counts major active *cards*, not events with `is_major`.

### Round 1

**Priya:** FoW banner must explain *why*: "3 major events active: RBI rate decision, Crude shock, Geopolitical escalation." Named events, not generic fog.

**Vikram:** `is_major` definition uses confidence ≥ 0.75 — but FoW dampener lowers effective score below 0.75. Can an event be `is_major` and simultaneously drop to MEDIUM tier?

**Matt:** Yes — by design. `is_major` is set on raw score before dampener. FoW trigger reads `is_major` on events, not effective tier. Banner lists events where `is_major = TRUE AND lifecycle = active`. Dampener affects new event routing, not major classification.

### Round 2

**Priya:** Manual override: PO can mark event as major/non-major from editorial interface.

**Vikram:** Override without audit trail = chaos.

**Matt:** `is_major_override` nullable boolean + `is_major_override_by` + `is_major_override_at`. Computed default from scorer; override wins if set. Feed endpoint returns `{ fog_of_war, active_major_events: [...] }` for banner.

### Round 3

**Priya:** Phase 1 heuristic vs Phase 3 interaction model — when do we switch?

**Vikram:** PRD2 defers P3-S2 until 30 days synthetic data. Heuristic stays until then. Don't half-build interaction model.

**Matt:** Feature flag `FOG_MODEL=heuristic|interaction`. Default heuristic. P3-S2 builds interaction model against `card_confidence_history`, backtests, then flips flag. No dual-run — one active model at a time.

### Round 4

**Converged:** PRD2 `is_major` definition + override with audit + named banner + heuristic until P3-S2 ready + feature flag switch.

### Options for PO — G-10

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 baseline. | Clean. |
| **B** ★ | + override audit + named banner payload + feature flag for model switch. | +1 day. Operational clarity. |

#### 🔴 PO Decision — G-10

1. **Option A or B?** (Consensus: **B**)
2. **FoW threshold:** 3+ major events fixed, or configurable?

---

## G-11 — Signal False-Positive Rate Measurement (P1)

**PRD2 baseline:** `signal_override_log` table. FP rate = incorrect overrides / total auto-triggers. Target < 10%. Monthly measurement.

### Round 1

**Priya:** Users never see FP rate directly. Builder sees monthly dashboard note. Trust is earned by not firing bad signals.

**Vikram:** Without UI, builder forgets to log overrides. Measurement dies.

**Matt:** Override must be **structured in editorial flow**, not optional notes. When editor dismisses auto-triggered signal: mandatory dropdown (confirmed / incorrect / ambiguous) + optional reason. Can't dismiss without selecting. Stored in `signal_override_log`.

### Round 2

**Priya:** Monthly report auto-generated to `notes/signal-override-log-monthly.md`?

**Vikram:** Markdown file in repo is fine for solo builder. Don't build a dashboard.

**Matt:** GitHub Action on 1st of month: query FP rate, append to notes file, open issue if > 10%. Zero UI cost.

### Round 3

**Priya:** FP rate feeds back to G-01/G-02 calibration. Close the loop visibly in the monthly note.

**Vikram:** Circular dependency if FP rate is bad because thresholds are bad. Acknowledge bootstrap period.

**Matt:** Monthly note includes: FP rate, top 3 incorrect signal types, recommended threshold adjustment (computed suggestion, not auto-applied). Links to `confidence_config.py` current values.

### Round 4

**Converged:** PRD2 schema + mandatory override dropdown in editorial + monthly GH Action report + calibration feedback loop.

### Options for PO — G-11

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 table only. | Measurement exists but unused. |
| **B** ★ | Mandatory override UX + monthly auto-report + calibration suggestions. | +1 day. Closes measurement loop. |

#### 🔴 PO Decision — G-11

1. **Option A or B?** (Consensus: **B**)
2. **FP target:** 10% or stricter (5%)?

---

# Layer 5 — Phase 3 Specific Gaps

---

## G-12 — Render Free Tier Cold-Start Kills Nightly NLP Job (P0)

**PRD2 baseline:** GitHub Actions for NLP job. Render keep-alive ping workflow.

### Round 1

**Priya:** Users don't notice where jobs run. Reliability is the product feature.

**Vikram:** GH Actions free tier = 2000 min/month. NLP job 30 min/night × 30 = 900 min. Tight with CI already running.

**Matt:** 900 min is fine — CI runs on push, not nightly. NLP workflow gets 50-min timeout. spaCy model cached via pip + Actions cache. Keep-alive ping for Render: `*/10 4-14 * * 1-5` per PRD2. Verify with workflow dispatch before enabling cron.

### Round 2

**Priya:** What if GH Actions secrets leak or job fails silently?

**Vikram:** Job must fail loudly — Slack/email notification on failure.

**Matt:** Solo builder won't have Slack. Workflow posts failure as GitHub Issue with label `nlp-job-failure`. Success logged to `job_runs` table in Supabase. Editor digest shows "Last NLP run: success 6h ago" or red warning.

### Round 3

**Priya:** Keep-alive ping hitting `/health` — does that count as Render usage?

**Vikram:** Free tier allows it. 66 pings/day × weekdays = fine. Stops outside market hours per PRD2 cron.

**Matt:** Keep-alive uses `curl -f ... || exit 0` — don't fail workflow on Render blip. Log response time. If p95 > 5s for a week, flag cold-start regression.

### Round 4

**Converged:** PRD2 GH Actions NLP + Render keep-alive + job_runs table + failure → GitHub Issue + digest surfacing.

### Options for PO — G-12

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 baseline workflows. | Minimal. |
| **B** ★ | + job_runs table + failure issues + digest surfacing. | +0.5 day. Observable jobs. |

#### 🔴 PO Decision — G-12

1. **Option A or B?** (Consensus: **B**)

---

## G-13 — No Live Mirror/Lens Data (P0)

**PRD2 baseline:** 20 synthetic historical events seeded with `is_synthetic = TRUE`. RLS excludes from user-facing queries.

### Round 1

**Priya:** Synthetic data must never appear in Mirror track record or user-facing accuracy stats. Users trust Mirror — one synthetic leak destroys credibility.

**Vikram:** RLS-only protection is fragile. One query missing `AND is_synthetic = FALSE` leaks data.

**Matt:** Three-layer defense: (1) RLS policy on all affected tables, (2) service-layer filter in every read path, (3) CI test that greps for queries missing synthetic filter. Synthetic seed via idempotent migration script, not manual SQL.

### Round 2

**Priya:** 20 events enough for FoW backtest and gap detector?

**Vikram:** 7 marked `is_major` per PRD2 — exactly enough to test 3+ trigger once. Not enough for ML. Honest scope: heuristic validation only.

**Matt:** Seed script generates: events + confidence history + signals + simulated user predictions + card outcomes. 20 events × ~3 signals each = 60 signal rows. Sufficient for FP rate formula smoke test. P3-S2 interaction model needs 30 days *live* synthetic running, not just seed insert.

### Round 3

**Priya:** Simulated user predictions — label clearly as synthetic in admin view?

**Vikram:** Admin-only. Never in Lens UI.

**Matt:** `user_predictions.is_synthetic = TRUE`. Lens queries join with filter. Seed predictions use realistic but fake user IDs (UUID v4, not auth.users FK). Service role only.

### Round 4

**Converged:** PRD2 20-event seed + triple-layer synthetic isolation + idempotent seed script + 30-day live run before P3-S2 + admin-only visibility.

### Options for PO — G-13

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 seed + RLS only. | Fast. Leak risk. |
| **B** ★ | Triple-layer isolation + CI grep test + idempotent script. | +1 day. Defensive. |

#### 🔴 PO Decision — G-13

1. **Option A or B?** (Consensus: **B**)
2. **Seed timing:** Week 1 (before other P3 work) or Week 3 (per PRD2)?

---

## G-14 — P3-S6/S7 Marketing and Billing Deferred (P2)

**PRD2 baseline:** Formal deferral. Not in active Phase 3 scope. Revisit after P3-S8 go/no-go.

### Round 1

**Priya:** Agree — building waitlist and Stripe before SEBI clarity is wasted effort. But landing page stub with disclaimer should exist for credibility.

**Vikram:** Even a stub is scope creep. Phase 3 is intelligence layer, not marketing.

**Matt:** Zero build. README + docs are the public face until SEBI gate. Remove P3-S6/S7 from task tracker entirely — not "deferred", **removed from active board**. Appendix file references them.

### Round 2

**Priya:** Users finding the app need *something* — even a single static page?

**Vikram:** Vercel frontend already deploys. Pulse/Thread require auth. No public discovery path — intentional for exploratory phase.

**Matt:** Correct. If PO wants a stub later, it's 2 hours. Not Phase 3. Formal deferral = no tasks, no placeholders in codebase.

### Round 3–4

**Unanimous:** Full deferral per PRD2. Remove from active scope. Document in appendix. Revisit only on P3-S8 green + RA registration path.

### Options for PO — G-14

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** ★ | PRD2 formal deferral. Remove from board. | -11 story points. Focus. |
| **B** | Static landing stub. | +2 hours. Premature marketing. |

#### 🔴 PO Decision — G-14

1. **Option A or B?** (Consensus: **A**)

---

## G-15 — Editorial Checklist Not Formalised (P2)

**PRD2 baseline:** 5 checklist items. Items 1–2 automated. Items 3–5 manual ticks. All must PASS before Publish.

### Round 1

**Priya:** Checklist is the editor's safety net. Show progress: "3/5 complete." Publish button greyed until 5/5.

**Vikram:** Manual ticks 3–5 will be rubber-stamped. Solo builder fatigue.

**Matt:** Items 1–2 already automated (G-07 number_validator + dissent length check). Item 3 (freshness): automate — check max Evidence `retrieved_at` age > 18 months → block. Item 4 (plain English): keep manual. Item 5 (SEBI compliance): automate keyword scan for buy/sell/hold/price target → block.

### Round 2

**Priya:** Automating SEBI scan is essential — that's the one legal risk.

**Vikram:** Keyword scan false positives on "hold rate" (RBI context). Need allowlist.

**Matt:** Regex with word boundaries + context allowlist: `hold` blocked only when adjacent to instrument name. `repo rate hold` allowed. Pattern list in `sebi_compliance_patterns.yaml`. Item 4 (plain English) stays manual — can't automate readability.

### Round 3

**Priya:** 3 automated + 1 manual = 4 items. Drop old item 3 manual tick since automated?

**Vikram:** Reframe: 4 items, 3 automated, 1 manual. Simpler UI.

**Matt:** Final checklist: (1) numbers validated [auto], (2) dissent present [auto], (3) evidence freshness [auto], (4) SEBI language [auto], (5) plain English [manual]. Five items, four automated.

### Round 4

**Converged:** PRD2 5 items with 4 automated + 1 manual. SEBI pattern scanner with allowlist. Freshness auto-check. Publish blocked until all PASS.

### Options for PO — G-15

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 baseline (3 manual ticks). | Rubber-stamp risk. |
| **B** ★ | 4 automated + 1 manual (freshness + SEBI automated). | +1 day. Less fatigue. |

#### 🔴 PO Decision — G-15

1. **Option A or B?** (Consensus: **B**)

---

# PO Decision Summary (All Gaps)

| Gap | Consensus option | Open PO choice |
|-----|------------------|----------------|
| G-01 | B | unique_publisher_count? UI phase? |
| G-02 | B or C | MEDIUM band width |
| G-03 | B | headline_hash scope |
| G-04 | B | call allocation tweak? |
| G-05 | B | — |
| G-06 | B | critical facts list |
| G-07 | B | — |
| G-08 | B | — |
| G-09 | B | — |
| G-10 | B | FoW threshold configurable? |
| G-11 | B | FP target 5% or 10% |
| G-12 | B | — |
| G-13 | B | seed Week 1 vs Week 3 |
| G-14 | A | — |
| G-15 | B | — |

---

# Recommended PO Defaults (If No Response — SSA Will Use These)

| Decision | Recommended default |
|----------|---------------------|
| G-01 Option | **B** + unique_publisher_count **Yes** + explainability UI **Phase 3 must-have** |
| G-01 Recalibration | Override-rate drift ≥ 10% monthly |
| G-02 Option | **C** (narrow MEDIUM 0.55–0.74) |
| G-02 Override target | ≤ 10% |
| G-02 Recalibration | Unified with G-01 |
| G-03 | **B** + headline_hash for RBI_POLICY/REGULATORY only |
| G-04 | **B**, keep PRD2 allocation |
| G-05–G-15 | Consensus **B** (or **A** for G-14) |
| G-10 FoW threshold | Configurable, default 3 |
| G-11 FP target | 10% |
| G-13 Seed timing | **Week 1** (unblocks all downstream) |

---

_Workshop complete. Next: PO confirms decisions → SSA solution design in `FinnWise_PRD2_SSA_Solution_Design.md`._
