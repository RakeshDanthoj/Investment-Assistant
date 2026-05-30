# Intelligence Pipeline Overview — Q&A Reference

**Version:** v1.0  
**Date:** 30-05-2026  
**Purpose:** Standalone reference for how FinnWise ingests events, scores confidence, links stocks, handles editorial workflow, deduplication, and the path toward editorial automation.

---

## How to read this document

There are two distinct layers in the system:

1. **Event ingestion** — automated, mostly non-LLM (cron → adapters → `events` table).
2. **Card synthesis** — LLM-driven, triggered manually after editorial triage (`draft-from-event` → review → publish).

Keep those separate when reasoning about “scoring” or “extraction.”

---

## 1. What format is used to extract information — prompt or defined schema?

**Events are not LLM-extracted.** Ingestion uses a fixed adapter schema, not a prompt.

Every source normalizes into a `RawEvent`:

| Field | Description |
|-------|-------------|
| `title` | Headline text |
| `canonical_url` | Normalised URL (UTM params stripped) |
| `published_at` | Provider timestamp (optional) |
| `excerpt` | Description / summary (optional, capped at ingest) |

**Source:** `backend/app/sources/base.py`

### What runs automatically

The 4-hour cron (`python -m app.jobs.event_detection`, scheduled in `render.yaml`) runs three adapters:

| Source | What it pulls |
|--------|----------------|
| **RBI RSS** | Official press releases via feedparser |
| **NewsAPI** | Headlines via factor-keyword rotation (`backend/app/config/newsapi_keywords.yaml`, 100 calls/day cap) |
| **NSE/BSE** | Corporate announcements (best-effort JSON scrape) |

Each raw item then gets:

- **Category** — rule-based keyword mapping (`backend/app/services/event_classification.py`), e.g. RBI feed → `rbi_policy`, NewsAPI text → `budget`, `regulatory`, etc.
- **Confidence (0–100)** — heuristic, not LLM: source-tier prior + keyword bumps (`backend/app/services/event_confidence.py`)

### Where LLM prompts apply

LLM prompts apply **only at card generation**, after you pick an event. Three versioned prompt files in `backend/prompts/`:

| Prompt | Role |
|--------|------|
| `synthesis.v1.md` | Insight, Context, `instrument_assessments`, signals |
| `dissent.v1.md` | Dissenting view |
| `framework.v1.md` | Transferable mental model |

Synthesis receives structured **Evidence** (Factor DB matrix markdown + event metadata + optional editor notes), and must return a single JSON object — no markdown fences, numbers only from Evidence, MMJ tags required.

---

## 2. How do we avoid missing important events that affect scoring?

There is **no guarantee of full market coverage**. The design uses multiple ingestion paths plus human backstops.

### Automated coverage

- 4-hour cron across RBI, NSE, and NewsAPI
- NewsAPI rotates across **8 macro factor keyword sets** (crude, INR/USD, rates, FII flows, monsoon, capex, GST, regulatory) to target financial signal rather than generic news
- RSS fallback when NewsAPI hits rate limits (429)
- Dedup merges same story from multiple outlets → higher `source_count` → higher confidence (interim blend today; full rule-based scorer planned in **P3-S1g**)

### Human / editorial backstops

- **Slow-burn watchlist** (`/editor/watchlist`) — monsoon, budget cycle, regulatory reviews tracked manually; one-click **Escalate** creates a draft event
- **Sunday editorial digest email** — pending watchlist items + dedup review queue (max 10 each) + NewsAPI poll summary
- **Cross-category dedup review queue** — flags cases where the same headline/entity/window landed in two categories (no auto-merge)

### Known gaps (honest)

- NewsAPI capped at 100 calls/day; one factor per cron tick
- NSE adapter can silently fail (logged, job continues)
- `factor_db_match` (25% of the PRD2 scorer) is implemented in P3-S1g (`confidence_scorer.py` + `event_factor_match.py`)
- Card pipeline still hardcodes **banking** sector for Evidence (`fetch_matrix_rows(sector_slug="banking")`), so non-banking stock linkage is limited until sector selection is wired
- No semantic “did we miss this story?” detector — coverage is source-list + keyword-driven

---

## 3. How correlation and impact scoring works — journey from event to stocks

There are **two different “scores”** in the system; they are often conflated.

### A. Event confidence score (routing / triage)

**At ingest (today):**

```
RawEvent → infer_event_category() → score() → persist_deduped_event()
```

Score formula (Phase 1):

- RBI RSS base: 88, NSE: 66, NewsAPI: 44
- + keyword bumps (RBI/repo/budget/etc., capped at +22)
- + tiny URL hash jitter

On dedup merge, `confidence_raw` is recomputed (interim blend of `source_count` + score). Full PRD2 scorer (source quality, factor match, recency, unique publishers) is **planned but not shipped** (P3-S1g).

### B. Stock/instrument impact (card content)

There is **no separate numeric “correlation engine”** that maps an event to stocks. The journey is:

```
Cron: event_detection
  → events row (lifecycle = draft)
  → PO: POST /api/cards/draft-from-event
  → Build Evidence layer (Factor DB matrix for sector)
  → LLM synthesis.v1
  → instrument_assessments array
  → Editor review (/admin/review)
  → Publish → users see card
```

#### Evidence layer (`card_pipeline._build_evidence_layer`)

- Loads full sensitivity matrix: every NSE ticker × 8 macro factors, each with sensitivity (−5…+5), MMJ tag, source URL
- Adds event snapshot (title, category, confidence, URL)
- Macro live-data feed is explicitly **not wired in Phase 1**

#### LLM decides instrument impact, grounded in that matrix

From `synthesis.v1.md`, each assessment includes:

- `instrument_id` — NSE ticker exactly as listed in Evidence (e.g. `HDFCBANK`)
- `signal_type` — one of `opportunity`, `headwind`, `watch`
- `reasoning` — 2–4 sentences; digits must trace to Evidence

Validators then check numbers and MMJ tags against Evidence — but **which stocks** and **opportunity vs headwind** is model judgment informed by Factor DB sensitivities, not a deterministic formula.

#### After publish

Signal monitoring (`signal_monitor` cron every 30 min during NSE hours) evaluates whether new market facts corroborate card signals — Jaccard text overlap + source counts, routed through `confidence_gate.route()` (high/medium/low). That is about **signal confirmation**, not initial stock selection.

---

## 4. Production admin workflow — visit the site or something else?

**Primary channel: web-based editorial UI**, plus scheduled background jobs and email digests.

### What runs automatically

| Job | Schedule |
|-----|----------|
| Event detection | Every 4 hours (Render cron) |
| Signal monitor | Every 30 min UTC (NSE hours only) |
| Weekly bias report | Monday 09:00 UTC |

### What you do manually

| Task | Where |
|------|-------|
| Triage ingested events | `/admin/queue` — table sorted by confidence, filter by category/source |
| Review slow-burn risks | `/editor/watchlist` (admin email allowlist required) |
| Review medium-confidence signal hits | `/admin/signal-queue` |
| Publish / regenerate drafts | `/admin/review/[draftId]` — 5-item checklist, publish, send-back with notes |

### Important operational detail

`/admin/queue` shows events but **does not have a “Generate card” button**. Draft generation is via API:

```http
POST /api/cards/draft-from-event
Content-Type: application/json

{ "event_id": "<uuid>", "editor_notes": null }
```

You then open `/admin/review/{card_id}`. In practice that means curl, Postman, or a script today — not a one-click queue action.

### Notifications

- **Sunday editorial digest email** exists (`backend/app/services/editorial_digest.py`) with watchlist + dedup queue + NewsAPI poll stats — but there is **no Render cron for it yet** in `render.yaml`; sending may be manual or added later
- **In-app notifications** fire on publish and on high-confidence signal hits (for users who logged predictions)

### Security posture (production caveat)

- Phase 1 admin queue/review APIs were built **without auth**
- Newer endpoints (`/editor/watchlist`, admin metrics) use `require_admin` — email allowlist from `ADMIN_EMAILS` / `FACTOR_DB_ADMIN_EMAILS`
- Production expects network perimeter or completing RBAC before exposing admin URLs publicly

**Bottom line:** You are expected to visit the site for editorial work. There is no separate admin app, Slack bot, or mobile workflow.

---

## 5. Can the system learn your editorial style and eventually replace you?

**Not today.** The architecture captures editorial *artifacts* but has no learning/training loop.

### What is captured now

| Data | Purpose |
|------|---------|
| `editor_notes` on regenerate | Injected into synthesis prompt |
| `editor_review_seconds` on publish | Time-on-task metric |
| `track_record` (append-only) | Immutable publish snapshot |
| `regen_history` (planned P3-S1k) | Section-level regen audit |
| `confidence_gate_log` + override deadlines | Signal auto-update vs editor reversal |
| Bias flags at publish | Post-publish audit |

### What Phase 3 plans (automation, not ML replacement)

- **P3-S1i–j:** Hard publish gates — number validator blocks publish; 4 automated checklist items + 1 manual “plain English” tick
- **P3-S1k:** Targeted section regen (preserve approved sections)
- **P3-S1m:** Structured override log with `{confirmed, incorrect, ambiguous}` for false-positive measurement
- **Day 30/60 calibration rituals** — threshold recalibration from override data, not model fine-tuning

### What would be required to truly “learn how you edit”

1. **Structured decision logging** — every publish/reject/regen with diff of what you changed vs draft (not fully built)
2. **Sufficient labeled corpus** — hundreds of (event, draft, final published card, editor_notes) pairs
3. **Evaluation harness** — automated graders + your override rate as ground truth
4. **Graduated autonomy** — auto-publish only when checklist + validator + confidence tier all pass, with override window (partially exists for *signals*, not for initial card publish)
5. **Sector-aware Evidence** — extend beyond banking-only matrix so automated drafts match your scope

The PRD vision is **human-gated ICE cards** with increasing software enforcement of your rules — not an agent that silently replaces editorial judgment. Full replacement would be a Phase 4+ research problem, not a current roadmap item.

---

## 6. Re-scoring, deduplication, and story developments (follow-up news)

### Dedup key (P3-S1c — shipped)

```
dedup_key = sha256(category | normalised_entity | 4h_window | headline_hash)
```

| Scenario | Behaviour |
|----------|-----------|
| Same story, different outlet, same headline | **Merge** into one `events` row; `source_count++`, `sources[]` appended, `confidence_raw` recomputed |
| Same entity, different headline in same 4h window | **Separate events** (by design — PO decision G-03) |
| Same headline, different category | Two rows + flagged in `dedup_review_queue` |

**Source:** `backend/app/services/event_dedup.py`

### Does it re-score the same event?

- **At the event row level:** only on **dedup merge** (more sources → higher confidence). There is no periodic re-scoring of stale draft events.
- **At the card level:** published cards are **not automatically re-drafted or re-scored** when new sources merge into the parent event. Card lifecycle moves forward independently (published → active → signal-triggered → resolved).

### How are “developments” (follow-up news) handled?

**By headline change → new event row**, not by updating the original:

- “RBI holds rates” and “RBI holds rates, cuts CCR by 50bps” have different `headline_hash` → different `dedup_key` → **two separate queue items**
- This is intentional: follow-ups with materially new information should enter editorial review again

### What is NOT built

- No “story thread” linking parent event → child development
- No automatic card update when a related event merges or a headline evolves
- No semantic similarity dedup (pure headline normalization, not “same story arc”)

### Partial bridge: signal monitor

After publish, if a card’s **signals** (hypothetical follow-on conditions written at synthesis time) match new facts, the monitor can auto-update on **high** confidence — but that is signal corroboration, not re-scoring the original event-to-stock mapping.

### Planned (P3-S1g)

`recompute_score(events.id)` on every upsert with full `factor_db_match` component — still at the **event** level, not card regeneration.

---

## Summary table

| Question | Short answer |
|----------|--------------|
| Extraction format | `RawEvent` schema at ingest; versioned LLM prompts only at card synthesis |
| Missing events | Multi-source cron + watchlist + digest; no full coverage guarantee |
| Stock impact | LLM interprets Factor DB matrix → `instrument_assessments`; no deterministic correlation score |
| Admin in production | Web UI + crons; draft-from-event via API; email digest for Sunday review |
| Learn & replace editor | Not built; Phase 3 adds hard gates + override measurement, not style cloning |
| Re-score / developments | Merge = same headline; new headline = new event; no card auto-regen on updates |

---

## Key file references

| Area | Path |
|------|------|
| Raw event schema | `backend/app/sources/base.py` |
| Event detection job | `backend/app/jobs/event_detection.py` |
| Classification | `backend/app/services/event_classification.py` |
| Confidence (Phase 1) | `backend/app/services/event_confidence.py` |
| Dedup | `backend/app/services/event_dedup.py` |
| NewsAPI keywords | `backend/app/config/newsapi_keywords.yaml` |
| Card pipeline | `backend/app/services/card_pipeline.py` |
| Factor DB lookups | `backend/app/services/factor_db.py` |
| LLM prompts | `backend/prompts/synthesis.v1.md`, `dissent.v1.md`, `framework.v1.md` |
| Draft API | `backend/app/api/cards.py` → `POST /draft-from-event` |
| Admin queue UI | `frontend/app/admin/queue/page.tsx` |
| Editorial review | `frontend/app/admin/review/` |
| Watchlist | `frontend/app/(app)/editor/watchlist/` |
| Render crons | `render.yaml` |
| Phase 3 plan (scorer, gates) | `docs/plans/finnwise-phase3-implementation-tasks.md` |
| PRD2 intelligence architecture | `docs/PRD/FinnWise_PRD2_Intelligence_Architecture.md` |

---

## Related post-implementation docs

- [Phase1_P1-S6 — Event-detection scheduled job and editorial queue](Post%20Implementation%20documentation/Phase1_P1-S6%20-%20Event-detection%20scheduled%20job%20and%20editorial%20queue.md)
- [Phase1_P1-S7 — LLM 3-call card-synthesis pipeline](Post%20Implementation%20documentation/Phase1_P1-S7%20-%20LLM%203-call%20card-synthesis%20pipeline%20(Gemini).md)
- [Phase1_P1-S8 — Editorial review interface for drafts](Post%20Implementation%20documentation/Phase1_P1-S8%20-%20Editorial%20review%20interface%20for%20drafts.md)
- [Phase3_P3-S1c — Event de-duplication pipeline](Post%20Implementation%20documentation/Phase3_P3-S1c%20-%20Event%20de-duplication%20pipeline.md)
- [Phase3_P3-S1d — NewsAPI factor keyword scheduler](Post%20Implementation%20documentation/Phase3_P3-S1d%20-%20NewsAPI%20factor%20keyword%20scheduler.md)
- [Phase3_P3-S1e — Slow-burn watchlist](Post%20Implementation%20documentation/Phase3_P3-S1e%20-%20Slow-burn%20watchlist.md)
