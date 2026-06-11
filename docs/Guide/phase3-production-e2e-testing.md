# Phase 3 — Production End-to-End Testing Guide

**Version:** v1.0  
**Date:** 31-05-2026  
**Scope:** First **14** Phase 3 deliverables (tasks **1.0**–**14.0** in `docs/plans/finnwise-phase3-implementation-tasks.md`)  
**Out of scope:** P3-S1l (FoW named banner), P3-S1m (signal override log), P3-T5 — not yet in this pause window  
**Parent plan:** `docs/plans/finnwise-phase3-implementation-tasks.md`  
**Go/no-go template:** `docs/plans/phase3-go-no-go.md`

---

## How to use this document

You are validating **production behaviour**, not re-running CI. CI already proved unit/integration contracts; this guide proves **deployed config, migrations, cron, UI, and operator workflows** work together on live infrastructure.

For each scenario:

| Column | Meaning |
|--------|---------|
| **ID** | Traceable reference (e.g. `P3-S0-01`) |
| **Where** | URL, API, SQL console, or Render/Vercel dashboard |
| **Role in the app** | Why this matters to users or editorial trust |
| **Steps** | Keystroke-level procedure |
| **Expected** | Pass criteria |
| **Edge / regression** | Non-happy paths and Phase 1/2 surfaces that must not break |

**Pass rule:** Record screenshot or curl output + timestamp. Mark **PASS / FAIL / BLOCKED** in the evidence table at the end.

---

## 0. Pre-flight — run once before scenario testing

Complete this checklist **after** you commit and deploy, **before** opening user-facing scenarios.

### 0.1 Deploy and migration order

| Step | Where | Action | Expected |
|------|-------|--------|----------|
| PF-01 | Local / CI | `python -m ruff check backend` && `python -m pytest -q backend/tests` | Green (baseline before deploy) |
| PF-02 | Render dashboard → **investment-assistant** service | Confirm latest commit deployed; note deploy timestamp | Status **Live**; build succeeded |
| PF-03 | Vercel dashboard → **investment-assistant-frontend** | Confirm latest commit deployed | Production deployment **Ready** |
| PF-04 | Supabase SQL editor (service role) | `SELECT * FROM schema_migrations` (or your migrate tracker) | Versions **0021** through **0028** present: `0021_synthetic_isolation`, `0023_dedup_key_review_queue`, `0024_factor_poll_log`, `0025_watchlist_items`, `0026_pipeline_runs_held_status`, `0027_confidence_audit`, `0028_card_regen_history` |
| PF-05 | Render shell / local with prod `SUPABASE_DB_URL` | `python backend/scripts/seed_synthetic_events.py` (once per environment) | Log: 20 upserted; **second run** inserts 0 new rows |
| PF-06 | Render + Vercel env | `ADMIN_EMAILS` identical on both (comma-separated PO emails) | Watchlist + admin-gated APIs work for your login |
| PF-07 | Render env | `SUPABASE_DB_URL`, `NEWSAPI_KEY`, `GEMINI_API_KEY` set | Cron ingest and card draft not `skipped_no_config` |

### 0.2 Production URLs (reference)

| Surface | URL |
|---------|-----|
| Frontend (Vercel) | `https://investment-assistant-frontend.vercel.app` |
| API (Render direct) | `https://investment-assistant-3eqc.onrender.com` |
| Browser API proxy | `https://investment-assistant-frontend.vercel.app/backend/...` |

Use the **browser proxy** for UI-driven tests (same-origin cookies/CORS). Use **Render direct** for operator curl when debugging upstream vs proxy.

### 0.3 Test accounts

| Persona | Requirement |
|---------|-------------|
| **Editor / PO** | Email in `ADMIN_EMAILS`; signed into Supabase auth on Vercel |
| **Regular user** | Any authenticated tester **not** on admin allow-list (optional, for 403 checks) |
| **SQL operator** | Supabase dashboard with service role (synthetic row verification only — never expose to users) |

---

## 1. Master decision trees

### How to read and use these trees

A **decision tree** here is not a test script — it is a **branching model of correct behaviour**. When you test in production, you observe one outcome (e.g. Publish button disabled) and walk **up** the tree to confirm that outcome is the **right** branch, not a bug.

| Layer | What it tells you | Typical tool |
|-------|-------------------|--------------|
| **SQL / Render logs** | Ground truth (rows exist, cron ran, merge happened) | Supabase, Render log search |
| **Network (API)** | What the server actually returned | Chrome DevTools → Network, or direct `/backend/...` URL |
| **UI** | What the editor/user sees; must **match** API, not replace it | Browser only |

**UI testing rule for Phase 3:** For every tree, do **both** where possible:

1. **See it on screen** (button state, badge, banner, dot colour).
2. **Confirm the same branch in API JSON** (status code + field) or SQL (one query).

If UI says PASS but API says FAIL (or the reverse), treat as **FAIL** and file under “UI/API drift”.

**SSR / RSC architecture (read before Network hunting):**

Pulse, Thread, and Mirror load their main payloads on the **Next.js server** during render (`fetchPulseFeed`, `fetchCardDetail`, `fetchMirrorInitialData` in `frontend/lib/api/server.ts`). Those calls go **Vercel → Render** and often **do not** appear in the browser Network tab on first paint.

| Surface | Server fetch (invisible in browser) | Client fetch (visible in Network) |
|---------|-------------------------------------|-----------------------------------|
| `/pulse` feed | `/api/feed` on page load | `/backend/api/feed` after category change, stale feed (over 60s), holdings change, or token mismatch |
| `/thread/[id]` card | `/api/cards/{id}` on page load | Same path when switching to **Original** view or when SSR failed |
| `/mirror` dashboard | `/api/mirror/dashboard` on page load (signed in) | Same path after ~60s stale remount or status filter change |
| Pulse/Thread chips | — | `/backend/api/market-facts` (always client) |
| Confidence aside | — | `/backend/api/events/.../confidence-breakdown` after expand (lazy) |

**Three ways to get inspectable JSON** (use any; same pass criteria):

1. **Direct proxy URL (recommended):** While on the Vercel site, open a new tab to `https://investment-assistant-frontend.vercel.app/backend/api/feed` (or `/api/cards/{id}`, `/api/mirror/dashboard` while signed in). Same-origin proxy as the app.
2. **Force a client refetch:** On Pulse, change a **category filter** chip; on Mirror, change the **status** filter; on Thread, switch to **Original** view. Then filter Network for `feed`, `cards`, or `mirror`.
3. **RSC payload search:** Click the `pulse`, `thread/...`, or `mirror` request with `?_rsc=` in the name → **Response** → `Ctrl+F` for `synthetic` or seed titles (harder to read than clean JSON).

**DevTools setup (use for all UI trees below):**

1. Open production site in Chrome/Edge (not localhost unless you are testing staging).
2. `F12` → **Network** tab → check **Preserve log**.
3. Filter box: type `backend` or the endpoint name (`feed`, `market-facts`, `cards`, `mirror`). Expect **client-only** calls here unless you forced a refetch (see table above).
4. Optional: **Network** → right-click a request → **Copy as cURL** for evidence; or use §7 curl cheatsheet against Render direct.

Record in your evidence log: **Tree ID → branch name → UI screenshot + JSON source (Network row, proxy URL, or curl) + status code**.

---

### 1.1 Synthetic data visibility (P3-S0, P3-T1)

**What the tree means**

Synthetic events are **real database rows** used for calibration and future FoW backtests. They are **not** fake UI mocks. The product promise is: users only ever see **live** editorial content on Pulse, Thread, and Mirror. SQL (service role) may show 20 synthetic rows; the **browser must never** surface their titles, URLs, or card links.

```
[SQL only] events WHERE is_synthetic = TRUE  →  expect 20 rows after seed

[UI + API] User surfaces (Pulse / Thread / Mirror)
├── No synthetic titles/URLs in feed or card JSON     → PASS (isolation)
└── synthetic://seed/ or known fixture headline appears → FAIL
```

**How to UI-test this tree**

There is **no** “synthetic” label in the UI — you prove isolation by **absence** on screen and by spot-checking **API JSON** (see SSR table above: first paint may not show `/api/feed` in Network).

**Search strings** (from `backend/scripts/seed_data/synthetic_events.json`):

- Literal: `synthetic` (catches `synthetic://seed/` URLs if leaked)
- Example seed titles: `INR weakens past 87 per USD`, `RBI announces liquidity injection via variable rate repo`, `TCS and Infosys Q3 FY25`

| Step | Action | Which branch |
|------|--------|--------------|
| 1 | Sign in as a normal user (or your PO account — same rule applies on user routes). | — |
| 2 | Go to `/pulse`. Wait until feed cards render. Visually confirm **no** Jan–Jun 2025 seed headlines in the feed. | — |
| 3 | **Get feed JSON** (pick one): **(A)** open `.../backend/api/feed` in a new tab; **(B)** change a Pulse **category** filter and find `GET .../backend/api/feed` in Network; **(C)** search the `pulse?_rsc=...` Response. | — |
| 4 | In feed JSON, `Ctrl+F` for `synthetic` and the seed titles above. | **PASS** = zero matches |
| 5 | Open 2–3 cards → `/thread/[id]`. Get card JSON via **(A)** `.../backend/api/cards/{id}?view=current`, **(B)** switch to **Original** view and watch Network, or **(C)** RSC response on `thread/...?_rsc=...`. Same search. | **PASS** = still zero |
| 6 | Go to `/mirror` (signed in). Get dashboard JSON via **(A)** `.../backend/api/mirror/dashboard` (auth cookies from session), **(B)** change **status** filter and watch Network, or **(C)** RSC on `mirror?_rsc=...`. Same search. | **PASS** = zero |
| 7 | **Optional FAIL reproduction (staging only):** If you temporarily break isolation in dev, you would see seed headlines on Pulse — in **production** you must **not** see that. | FAIL branch |

**What you cannot prove from UI alone**

- That exactly **20** synthetic rows exist → use SQL once (scenario P3-S0-01).
- That RLS blocks PostgREST direct access → API uses service layer + mixin; UI test covers **API paths users hit**.

**UI pass statement:** “Pulse, Thread, and Mirror API responses (feed, card detail, mirror dashboard) contain no `synthetic` substring and no seed fixture titles.”

---

### 1.2 Event deduplication (P3-S1c)

**What the tree means**

Ingest merges duplicate wire stories into **one** editorial queue row (`source_count` goes up). The UI does not show `dedup_key`; it shows **fewer duplicate headlines** and optionally higher confidence / an editorial badge later. Cross-category collisions stay as two rows and appear in Sunday digest / SQL queue — **not** as a merged row in `/admin/queue`.

```
Same story, same category + entity + headline (4h window)
├── One row in /admin/queue, source_count > 1 (SQL)     → merge PASS
├── Two queue rows, same headline, different category   → no auto-merge PASS
└── Two rows, same entity, different headlines         → distinct events PASS
```

**How to UI-test this tree**

Dedup is **mostly invisible** on user routes; test it on **editorial** surfaces.

| Step | Action | Which branch |
|------|--------|--------------|
| 1 | Open `/admin/queue`. | — |
| 2 | Scan for **duplicate headlines** on the same day (same RBI move reported by two outlets). | **Merge PASS** = one row; title appears once; you may see higher confidence score on that row |
| 3 | Click a row you suspect was merged. Note `event_id` from URL or Network if you open draft later. | — |
| 4 | **SQL (one query):** `SELECT source_count, jsonb_array_length(sources) FROM events WHERE id = '<event_id>';` | **Merge PASS** = `source_count >= 2` after multi-outlet coverage |
| 5 | **False-merge check:** Find two **different** stories same afternoon (e.g. two distinct RBI headlines). | **Distinct PASS** = two separate queue rows |
| 6 | **Cross-category:** Rare in manual test; if you have `dedup_review_queue` seeds, Sunday digest / SQL lists them — **not** merged in queue UI. | **No auto-merge PASS** |

**UI signals (secondary)**

- After merge, parent event may show **`force_editorial_review`** when `source_count > 5` → on Thread/Lens, expanded confidence panel shows **Editorial review** badge (tree 1.5/1.6 overlap). That badge is **not** dedup itself but confirms post-dedup counts reached the guardrail.

**UI pass statement:** “Queue does not show obvious duplicate headlines for the same story; spot-checked event has `source_count` consistent with merge.”

---

### 1.3 NewsAPI poll outcome (P3-S1d)

**What the tree means**

Each 4-hour cron tick polls **one** macro factor, logs to `factor_poll_log`, and may ingest articles. **`ok` / `empty` / `error`** are all valid if logged; only “no log row and no NewsAPI attempt” is a failure. This tree is **primarily ops/SQL**; the UI does not show poll status except indirectly (new queue rows, digest email).

```
Cron tick
├── factor_poll_log row with status ok | empty | error  → ingest path alive
├── No row, budget exhausted (100/day UTC)              → expected late day
└── No row, no NewsAPI GET in logs                      → FAIL
```

**How to UI-test what you can**

Full branch classification needs **SQL or Render logs**. UI testing confirms **downstream effects**:

| Step | Action | Which branch |
|------|--------|--------------|
| 1 | Note UTC time. Wait for next **event_detection** cron (every 4h) or check last cron in Render. | — |
| 2 | **SQL:** `SELECT status, article_count, polled_at FROM factor_poll_log ORDER BY polled_at DESC LIMIT 3;` | Map to **ok** / **empty** / **error** branch |
| 3 | **UI:** Refresh `/admin/queue` after cron. | **ok** with articles → possible **new** or **updated** rows (not guaranteed same tick) |
| 4 | If you use editorial digest preview/send, open HTML and find **NewsAPI factor poll** table. | Confirms digest wiring; statuses should match SQL |

**Do not UI-fail on:** Empty queue after cron — `empty` poll is valid. **Do UI+ops-fail on:** No `factor_poll_log` rows for 24h after deploy with cron enabled.

---

### 1.4 Market facts freshness (P3-S1f)

**What the tree means**

Macro chips on Pulse/Thread carry a **freshness tristate** (green / amber / red). Card **drafting** is held if any **critical** fact is **unavailable**; **stale** still allows draft but warns. The tree splits on **unavailable** vs **fresh/stale** — different UI and API behaviour.

```
Market facts state
├── All critical: fresh OR stale
│   ├── Chips: green or amber dots
│   ├── draft-from-event: succeeds (200)
│   └── /admin/queue: no “blocked” banner (stale may still warn)
└── Any critical: unavailable
    ├── Chips: red dot on that fact
    ├── /admin/queue: MarketFactsBanner (degraded / hold)
    └── draft-from-event: 423 critical_facts_held
```

**How to UI-test this tree**

This is one of the **richest UI trees** — you can walk every branch without SQL if Network is open.

| Step | Action | Which branch |
|------|--------|--------------|
| 1 | Open `/pulse`. Locate **market facts strip** (horizontal chips: INR/USD, repo, Nifty, etc.). | — |
| 2 | Per chip, note dot colour: **green** = fresh, **amber** = stale, **red** = unavailable. | fresh/stale vs unavailable |
| 3 | **Network:** `GET .../backend/api/market-facts`. In JSON, each fact has `freshness_status`: `fresh` \| `stale` \| `unavailable`. | **Must match** dot colours |
| 4 | **Branch A (fresh/stale):** If no red dots, open `/admin/queue`. | Banner absent or only “stale” warning — not hard hold |
| 5 | **Branch B (unavailable):** If any red dot, stay on `/pulse` then go to `/admin/queue`. | Banner visible explaining missing critical data |
| 6 | **Draft hold (editor):** From queue, pick an event; trigger draft (UI if you have it, else curl `POST .../draft-from-event`). Watch Network. | **unavailable** → **423** + body `critical_facts_held`; **fresh/stale** → 200 and redirect/review URL |
| 7 | Open `/thread/[publishedCard]` — chips should still show dots (regression). | Same colour logic as Pulse |

**UI pass statement:** “Dot colours match `freshness_status` in `/api/market-facts`; unavailable branch shows banner on queue and blocks draft with 423.”

**Do not confuse:** ICE Evidence freshness (18-month rule on card Evidence) is **tree 1.6 / checklist**, not market-fact chips.

---

### 1.5 Confidence tier routing (P3-S1g, P3-S1h)

**What the tree means**

**Event routing tier** (HIGH / MEDIUM / LOW) comes from `confidence_effective` and PO thresholds (≥0.75, 0.55–0.74, &lt;0.55). That is **separate** from the ICE bar (Measured / Modelled / Judged %) on the same aside. **Fog of War** dampens effective score when many `is_major` events are active; the explainability panel should show raw vs effective and optionally a FoW callout.

```
confidence_effective
├── ≥ 0.75   → HIGH   (UI: tier label + blue-ish styling)
├── 0.55–0.74 → MEDIUM
└── < 0.55   → LOW

FoW active (≥3 major events)
├── effective ≈ raw × 0.6
└── UI: FoW callout in expanded breakdown
```

**How to UI-test this tree**

All of this lives on **`/thread/[cardId]`** or **Lens result card** after you expand **“Why this confidence tier?”**

| Step | Action | Which branch |
|------|--------|--------------|
| 1 | Open a **published** card from Pulse (`/thread/[id]`). Card body is SSR — you may see `thread/...?_rsc=...` instead of `/api/cards/...` on first paint. | — |
| 2 | In aside, find ICE bar (Measured/Modelled/Judged) — **ignore for tier**; scroll to **“Why this confidence tier?”** | — |
| 3 | **Before click:** Network tab — confirm **no** `confidence-breakdown` request yet (lazy client fetch only). | Perf contract |
| 4 | Click to expand panel. Wait for skeleton → content. | — |
| 5 | Read **tier label** (HIGH / MEDIUM / LOW) and **raw %** vs **effective %**. | Map to threshold branches |
| 6 | **Network:** `GET .../confidence-breakdown`. Compare `tier`, `confidence_raw`, `confidence_effective`, `fog_active` to UI. | UI must match API |
| 7 | **FoW branch:** If `fog_active: true` and effective &lt; raw, UI shows FoW dampener callout. If API says fog but UI silent → **investigate** (partial P3-S1l) | FoW sub-branch |
| 8 | **Escalation:** Pick event with `source_count > 5` (SQL) or high-source story. Re-open panel. | **Editorial review** amber badge |
| 9 | Repeat on **Lens** result card if you use Lens in prod. | Same panel behaviour |

**Mapping UI to tree (quick reference)**

| UI element | API field | Branch |
|------------|-----------|--------|
| Tier badge “HIGH” | `tier` or effective ≥ 0.75 | HIGH |
| Tier “MEDIUM” | effective in [0.55, 0.74] | MEDIUM |
| Tier “LOW” | effective &lt; 0.55 | LOW |
| FoW callout box | `fog_active` + effective &lt; raw | FoW dampener |
| Editorial review badge | `force_editorial_review` | Dedup guardrail (related) |

**UI pass statement:** “Expanded panel tier and raw/effective match breakdown API; lazy load respected; FoW callout present iff API `fog_active`.”

---

### 1.6 Publish gate stack (P3-S1i, P3-S1j, P3-S1k, P3-T4)

**What the tree means**

Publish is a **stack** of gates evaluated in order. The UI should **disable** Publish early; the API must still **422** if someone bypasses the button. Section regen **re-runs** validator/checklist — you can move from “all pass” back to “blocked” without leaving the page.

```
Click Publish (or POST publish)
├── number_validation FAIL     → disabled button + 422 number_validator_failed
├── checklist auto FAIL        → disabled + 422 editorial_checklist_failed
├── plain English not ticked   → disabled + 422 publish_rejected
└── all pass                   → 200, card on Pulse

After section regen
├── validator FAIL again       → still blocked
└── validator PASS + checklist + tick → publish allowed
```

**How to UI-test this tree (full walk)**

Use **`/admin/review/[draftId]`** only. Keep Network open on `admin/cards` requests.

**Phase A — Observe blocked states (top of tree)**

| Step | Action | UI signal | Network (if you force submit) |
|------|--------|-----------|-------------------------------|
| A1 | Open draft known to fail numbers (or break Insight in staging). | **Publish** greyed/disabled; red list of **ungrounded** sentences | `GET .../admin/cards/{id}` → `number_validation.status: "FAIL"` |
| A2 | Fix numbers only; leave dissent short or SEBI violation. | Publish still disabled; checklist item(s) **FAIL** badge | `editorial_checklist.items[].status` |
| A3 | Fix auto items; leave **Plain English** unchecked. | Publish disabled; manual box empty | — |
| A4 | With Plain English unchecked, use DevTools or curl to `POST .../publish` anyway. | — | **422** `publish_rejected` |

**Phase B — Walk down to success (bottom of tree)**

| Step | Action | UI signal | Network |
|------|--------|-----------|---------|
| B1 | Fix Evidence / regen section until **Number validator** shows **PASS**. | Green PASS on checklist item 1 | `number_validation.status: "PASS"` |
| B2 | Ensure dissent, freshness, SEBI items **PASS**. | Four auto badges PASS | `editorial_checklist` all automated PASS |
| B3 | Check **Plain English** checkbox. | **Publish** enabled | — |
| B4 | Click **Publish**. Confirm dialog if any. | Success toast or navigation | **200** on `POST .../publish` |
| B5 | Open `/pulse`. | Card appears in feed | Confirm via `.../backend/api/feed` (direct tab or category-filter refetch); SSR first paint may not list the request in Network |

**Phase C — Regen branch (after section regen)**

| Step | Action | Which branch |
|------|--------|--------------|
| C1 | On same draft (or new draft), open **Regen section** → choose **Insight** → note: “Add unsourced figure 99%” (or similar) → submit. | — |
| C2 | Wait for regen complete; page reloads card state. | Post-regen badges refresh |
| C3 | If validator **FAIL**: Publish disabled again; ungrounded list returns. | **regen → FAIL** branch |
| C4 | `POST publish` via Network replay or curl. | **422** `number_validator_failed` — proves API stack |
| C5 | Fix content → PASS → tick Plain English → Publish. | **regen → PASS** branch |

**UI vs API order (why both matter)**

The server checks **number validator first**, then checklist, then plain English. The UI may show all failures at once, but when you fix issues, watch **which gate re-enables Publish** — that should follow the same order (numbers before checklist before tick).

**UI pass statement:** “Publish disabled iff any gate fails; 200 only after full stack; section regen can re-block and 422 on publish.”

---

### 1.7 Quick reference — which trees are UI-heavy vs ops-heavy

| Tree | Primary UI surfaces | SQL/logs still needed? |
|------|---------------------|-------------------------|
| 1.1 Synthetic | Pulse, Thread, Mirror (proxy URL or forced client refetch; SSR hides first-paint feed) | Yes — confirm 20 seed rows once |
| 1.2 Dedup | `/admin/queue` headline scan | Yes — `source_count` proof |
| 1.3 NewsAPI | Queue refresh (indirect); digest HTML | Yes — `factor_poll_log` |
| 1.4 Market facts | Pulse, Thread chips, `/admin/queue` banner | Optional — API matches dots |
| 1.5 Confidence | Thread/Lens aside expand panel | Optional — breakdown API |
| 1.6 Publish stack | `/admin/review` PublishGate + ChecklistPanel + RegenSection | Optional — forced POST for 422 proof |

---

## 2. Story-by-story test scenarios

### P3-S0 — Synthetic historical seed + triple-layer isolation

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S0-01** | Supabase SQL (service role) | Calibration data exists | Run: `SELECT COUNT(*) FROM events WHERE is_synthetic = TRUE;` | Count = **20** | If 0, re-run seed script (PF-05) |
| **P3-S0-02** | Supabase SQL | Major-event FoW prep | `SELECT COUNT(*) FROM events WHERE is_synthetic = TRUE AND is_major = TRUE;` | Count = **7** | — |
| **P3-S0-03** | Supabase SQL | Idempotent seed | Re-run `seed_synthetic_events.py`; repeat count query | Still **20** rows; no duplicates on `external_id` | — |
| **P3-S0-04** | Browser → `/pulse` | User feed must exclude synthetic | 1. Open `https://investment-assistant-frontend.vercel.app/pulse` 2. Sign in if prompted 3. Scroll full feed — no seed headlines visible 4. Inspect feed JSON: open `.../backend/api/feed` in a new tab **or** change a category filter and use DevTools → Network → `feed` **or** search `pulse?_rsc=...` Response 5. `Ctrl+F` for `synthetic` and titles from `synthetic_events.json` | No `canonical_url` containing `synthetic://seed/`; no Jan–Jun 2025 synthetic fixture titles | First paint is SSR — filtering Network for `feed` alone often shows nothing until step 4b |
| **P3-S0-05** | Browser → `/mirror` | Mirror predictions isolation | 1. Navigate to `/mirror` (signed in) 2. Load prediction list 3. Inspect `.../backend/api/mirror/dashboard` (direct tab or status-filter refetch / `mirror?_rsc=...`) | Zero rows tied to synthetic events; no seed titles in JSON | Phase 2 Mirror must still load; dashboard SSR on first paint |
| **P3-S0-06** | curl (Render direct) | API layer filter | `curl -s "https://investment-assistant-3eqc.onrender.com/api/feed" \| jq '.cards[].title'` then spot-check card detail: `curl -s ".../api/cards/<CARD_ID>?view=current" \| jq .` | No synthetic event titles | Service role DB can still `SELECT` synthetic — that is correct |

---

### P3-T1 — Synthetic isolation verification gate (production spot-check)

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-T1-01** | Manual repeat of P3-S0-04, P3-S0-05 | CI gate manual confirmation | Execute S0-04 and S0-05; document screenshots | PASS on both | This is the **P3-S8 go/no-go** "synthetic isolation spot-check in production" item |
| **P3-T1-02** | `/thread/[publishedCardId]` | Thread detail path | Open any **published** card from Pulse → inspect aside | Card loads; confidence composition renders; no 500 | Phase 2 Thread perf baseline |

---

### P3-S1c — Event de-duplication pipeline

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1c-01** | Supabase SQL | Schema | `SELECT column_name FROM information_schema.columns WHERE table_name='events' AND column_name IN ('dedup_key','source_count','sources','force_editorial_review');` | All columns present | — |
| **P3-S1c-02** | Render → Logs → event_detection cron | Live merge behaviour | 1. Note UTC time before next 4h cron 2. After cron, query: `SELECT id, title, source_count, dedup_key, force_editorial_review FROM events WHERE created_at > NOW() - INTERVAL '6 hours' ORDER BY source_count DESC LIMIT 10;` | Recent real ingests show `source_count ≥ 1`; high-volume stories show `source_count > 1` after multi-outlet coverage | Empty cron → check `SUPABASE_DB_URL` |
| **P3-S1c-03** | Supabase SQL | Cross-category queue | `SELECT COUNT(*), status FROM dedup_review_queue GROUP BY status;` | Table exists; pending rows acceptable | Zero rows is OK if no collisions yet |
| **P3-S1c-04** | Supabase SQL | Editorial escalation flag | `SELECT id, title, source_count, force_editorial_review FROM events WHERE force_editorial_review = TRUE LIMIT 5;` | Any row with `source_count > 5` has flag **true** | — |
| **P3-S1c-05** | `/admin/queue` | Editorial sees merged rows | 1. Open `/admin/queue` 2. Sort by confidence 3. Click row with highest `source_count` (if any) | Single queue row (not duplicate titles for same story) | Phase 1 queue sort/filter still works |

---

### P3-S1d — NewsAPI factor keyword scheduler

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1d-01** | Supabase SQL | Poll audit trail | `SELECT factor_id, status, article_count, polled_at FROM factor_poll_log ORDER BY polled_at DESC LIMIT 8;` | Rows exist after at least one cron since deploy; `status` ∈ {`ok`,`empty`,`error`} | No rows → see decision tree §1.3 |
| **P3-S1d-02** | Render logs | Round-robin | Search logs for `newsapi.poll_status` across **two consecutive** cron runs | `factor_id` (or slug) **changes** between runs | Same factor twice → rotation bug |
| **P3-S1d-03** | Supabase SQL | Daily cap | `SELECT COUNT(*) FROM factor_poll_log WHERE polled_at::date = CURRENT_DATE AT TIME ZONE 'UTC';` | Count ≤ **100** | — |
| **P3-S1d-04** | Render logs (optional) | RSS fallback on 429 | If `status=error` rows exist, grep log for `rss_fallback` or ET Markets/Mint adapter | 429 path attempted RSS without extra NewsAPI GET | — |
| **P3-S1d-05** | Local/script or manual | Digest template | Run editorial digest preview if you have a script; else skip and mark BLOCKED | HTML includes NewsAPI poll summary table | Full send not required — template exists per S1d |

---

### P3-S1e — Slow-burn watchlist

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1e-01** | Browser → `/editor/watchlist` | Long-lead risk tracking | 1. Sign in with **ADMIN_EMAILS** account 2. Navigate to `https://investment-assistant-frontend.vercel.app/editor/watchlist` | Table loads with **5 seed rows** (monsoon, budget, etc.) | Non-admin → forbidden page |
| **P3-S1e-02** | `/editor/watchlist` | Status update | 1. Pick row **"Monsoon progression"** (or any `watching` row) 2. Open status dropdown 3. Select **closed** 4. Wait for PATCH to complete (network 200) 5. Refresh page | Status persists **closed**; `last_reviewed_at` updated (visible or via API) | — |
| **P3-S1e-03** | `/editor/watchlist` | Escalate to editorial pipeline | 1. Pick a **watching** row (re-open closed seed in SQL if needed) 2. Click **Escalate** 3. Confirm dialog if shown 4. Note escalated state | Row status → **escalated**; button disabled or shows escalated | Second escalate → 409 `already_escalated` |
| **P3-S1e-04** | `/admin/queue` | Escalated event visible | 1. Open `/admin/queue` 2. Filter or scan for `event_source = watchlist` (column or title match) | New **draft** event with title from watchlist item | — |
| **P3-S1e-05** | curl + admin JWT | API auth | `curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer <non-admin-token>" https://investment-assistant-3eqc.onrender.com/api/editor/watchlist` | **403** | Admin token → **200** |

---

### P3-S1f — Market facts freshness + fallback chain

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1f-01** | Browser → `/pulse` | User-facing freshness | 1. Open `/pulse` 2. Locate market facts strip (macro chips above/beside feed) 3. Hover or inspect each chip | Coloured dot per chip: **green** = fresh, **amber** = stale | Phase 2 Pulse layout not broken |
| **P3-S1f-02** | Browser → `/thread/[cardId]` | Thread chips | Open published card → same strip in thread header/aside | Dots match `/api/market-facts` freshness | — |
| **P3-S1f-03** | curl | API contract | `curl -s "https://investment-assistant-3eqc.onrender.com/api/market-facts" \| jq '.facts[] \| {id, freshness_status, value}'` | Each critical fact has `freshness_status` ∈ {`fresh`,`stale`,`unavailable`} | — |
| **P3-S1f-04** | `/admin/queue` | Editorial degraded banner | Open `/admin/queue` | If any critical fact stale/unavailable, **MarketFactsBanner** visible with explanation | All fresh → banner absent or informational only |
| **P3-S1f-05** | curl (operator) | Critical-fact hold | 1. Pick `event_id` from `/admin/queue` 2. `curl -s -X POST "https://investment-assistant-3eqc.onrender.com/api/cards/draft-from-event" -H "Content-Type: application/json" -d '{"event_id":"<uuid>"}'` | **200** if facts available; **423** with `critical_facts_held` if unavailable (document which branch you hit) | Do not force-unavailable in prod unless you accept failed draft |

---

### P3-T2 — Data pipeline integration gate (production smoke)

CI runs `test_data_pipeline_integration.py`. In production, run this **short cross-check** instead of re-implementing the fixture.

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-T2-01** | Combined | Dedup + queue | Verify **P3-S1c-02** shows merge semantics | `source_count` can exceed 1 | — |
| **P3-T2-02** | Combined | NewsAPI + dedup | Verify **P3-S1d-01** + new events in queue after cron | Ingest pipeline alive | — |
| **P3-T2-03** | Combined | Watchlist → queue | Complete **P3-S1e-03** + **P3-S1e-04** | Escalated event in queue | — |
| **P3-T2-04** | Combined | Facts hold | **P3-S1f-05** branch documented | Either draft proceeds or 423 hold — both valid if explained | — |

---

### P3-S1g — Rule-based confidence scorer + gate swap

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1g-01** | Supabase SQL | Stored scores | `SELECT id, title, confidence_raw, confidence_effective, factor_db_match_count, is_major FROM events WHERE is_synthetic = FALSE ORDER BY created_at DESC LIMIT 5;` | `confidence_raw` and `confidence_effective` populated (0–1 range) | — |
| **P3-S1g-02** | Supabase SQL | Audit trail | `SELECT event_id, scorer_version, created_at FROM confidence_score_audit ORDER BY created_at DESC LIMIT 5;` | Rows exist for recent upserts | Empty → migration 0027 not applied |
| **P3-S1g-03** | curl | Breakdown API | `curl -s "https://investment-assistant-3eqc.onrender.com/api/events/<event_uuid>/confidence-breakdown" \| jq '{tier, confidence_raw, confidence_effective, inputs: .inputs \| keys}'` | JSON with **5 input keys**, tier label, sources array | 404 → bad uuid |
| **P3-S1g-04** | `/admin/signal-queue` | Signal routing uses float tiers | 1. Open `/admin/signal-queue` 2. Inspect medium-confidence hits (if any) | Queue populated; no obvious Phase 1 "source count only" labelling regression | Empty queue OK outside market hours |

---

### P3-S1h — Confidence explainability UI

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1h-01** | `/thread/[cardId]` | Lazy-load perf | 1. Open published card with known `event_id` 2. Open DevTools → Network 3. **Before** expanding panel, confirm **no** request to `confidence-breakdown` 4. In aside, click **"Why this confidence tier?"** (or collapsible trigger) 5. Watch network | Single fetch to `/backend/api/events/.../confidence-breakdown` **after** expand only | No layout shift on initial paint |
| **P3-S1h-02** | Thread aside (expanded) | Five inputs + tier | After expand: verify **five** progress bars (source count, source quality, factor match, recency, unique publishers), tier badge (HIGH/MEDIUM/LOW), raw vs effective % | Matches breakdown API when curl same `event_id` | — |
| **P3-S1h-03** | Thread aside | FoW callout | If `confidence_effective` ≪ `confidence_raw` on API, UI shows Fog of War dampener callout | Callout visible when API `fog_active` true | Hidden when equal |
| **P3-S1h-04** | Thread aside | Editorial badge | Find event with `force_editorial_review=true` (SQL or high `source_count`) | Amber **Editorial review** badge in panel | — |
| **P3-S1h-05** | `/lens` → result card | Lens surface | 1. Run a Lens query that returns a card 2. Expand confidence panel same as Thread | Same behaviour as Thread | ICE Measured/Modelled/Judged bar **still present** above panel |

---

### P3-T3 — Confidence scoring verification gate (production spot-check)

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-T3-01** | API + UI | Scores agree | Compare **P3-S1g-03** JSON `confidence_raw` to UI displayed raw % (×100) | Within rounding (±1%) | — |
| **P3-T3-02** | API | Weighted sum | From breakdown JSON, manually verify `sum(input.value × input.weight) ≈ confidence_raw` | Within ε 0.02 | Document arithmetic in evidence |
| **P3-T3-03** | `/thread/[cardId]` | RTL-equivalent manual | Expand panel → all five inputs render with labels | PASS | 404 event → red error alert; ICE bar still visible |

---

### P3-S1i — Number validator hard publish gate

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1i-01** | `/admin/review/[draftId]` | Load-time gate | 1. Open draft card in review workspace 2. Scroll to **Publish** section (`PublishGate`) 3. If validator FAIL: note **Publish** button state | Button **disabled** when `number_validation.status !== PASS` | — |
| **P3-S1i-02** | Review workspace | Sentence-level diff | On FAIL card: inspect ungrounded list | Shows **sentence text** + offending number token | — |
| **P3-S1i-03** | curl | Hard 422 | `curl -s -X POST "https://investment-assistant-3eqc.onrender.com/api/admin/cards/<draft_id>/publish" -H "Content-Type: application/json" -d '{"plain_english_confirmed":true}'` on FAIL draft | **422** body includes `number_validator_failed` and `ungrounded[]` | No override endpoint exists |
| **P3-S1i-04** | Review workspace | Comparative soft flags | Find prose with "doubled" or "record high" (if any) | Soft warning shown; **does not** alone block publish | — |

**Creating a FAIL draft for testing:** Use an existing draft or run `draft-from-event` then manually edit Insight in DB **only in staging** — in production prefer a card you already know fails validator.

---

### P3-S1j — Editorial checklist (4 automated + 1 manual)

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1j-01** | `/admin/review/[draftId]` | Automated items | On card load, locate **ChecklistPanel** | Four items show **PASS/FAIL** badges (numbers, dissent, evidence freshness, SEBI); fifth **Plain English** is manual checkbox only | No manual ticks for auto items |
| **P3-S1j-02** | Checklist | Dissent gate | Open draft with `dissenting_view` ≤ 100 chars (or truncate in staging) | Dissent item **FAIL** | — |
| **P3-S1j-03** | Checklist | SEBI allowlist | Card containing phrase **"repo rate hold"** in macro context | SEBI scan **PASS** | — |
| **P3-S1j-04** | Checklist | SEBI block | Card containing **"buy HDFC Bank"** recommendation language | SEBI **FAIL** with violation detail | — |
| **P3-S1j-05** | Publish flow | Manual tick required | 1. Fix all automated FAILs 2. Leave Plain English **unchecked** 3. Click Publish | Button disabled; API 422 if forced | — |
| **P3-S1j-06** | Publish flow | Full pass | 1. All automated PASS 2. Check **Plain English** 3. Click **Publish** | **200**; redirect or success toast; card appears on Pulse | `track_record` row created (SQL optional) |

---

### P3-S1k — Targeted section regen

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-S1k-01** | `/admin/review/[draftId]` | Section regen UI | 1. Open draft 2. Locate **RegenSection** in aside 3. Select section **Insight** from dropdown 4. Click note field; type: `Shorten opening paragraph; remove unsourced percentage.` 5. Click **Regenerate section** (or equivalent submit) 6. Wait for loading spinner to finish | Insight updates; Context/Evidence/Dissent/Framework text **unchanged** (hash/compare visually) | Empty note → 422 |
| **P3-S1k-02** | Review workspace | Post-regen validation | After regen completes | `number_validation` and checklist **refresh**; PASS/FAIL badges update | — |
| **P3-S1k-03** | Supabase SQL | Audit trail | `SELECT regen_history, full_regen_count FROM cards WHERE id = '<draft_id>';` | `regen_history` JSON array appended with section, timestamp, note | Migration 0028 required |
| **P3-S1k-04** | RegenSection | Full regen guard | 1. Click **Full regen** (same card) 2. Confirm dialog if `full_regen_count >= 1` | First full regen: succeeds; counter increments | Third without PO flag → 423 blocked |
| **P3-S1k-05** | Review workspace | Legacy send-back | Click **Regenerate draft (new card)** (Phase 1) | Creates **new** draft id; old archived — distinct from in-place section regen | — |

---

### P3-T4 — Editorial integrity verification gate (golden path E2E)

This is the **most important manual regression** for Phase 3 editorial trust. Execute as one continuous session.

| ID | Where | Role | Steps | Expected | Edge / regression |
|----|-------|------|-------|----------|-------------------|
| **P3-T4-01** | End-to-end | Ungrounded block | 1. Open draft known to fail number validator **OR** regen Insight with note asking for a specific unsourced `%` (if LLM complies) 2. Confirm Publish disabled 3. `curl -X POST .../publish` | **422** `number_validator_failed` | Matches CI `test_ungrounded_number_blocks_publish_with_422` |
| **P3-T4-02** | End-to-end | Happy path publish | 1. Start from FAIL draft 2. Switch to **Evidence** tab 3. Add/fix evidence so numbers in Insight appear in Evidence (or **Regenerate section → Evidence** to rebuild Factor DB layer) 4. Wait for validator **PASS** 5. Confirm checklist auto items **PASS** 6. Check **Plain English** 7. Click **Publish** 8. Open `/pulse` | Publish **200**; card visible on Pulse; Thread loads | Matches CI happy path test |
| **P3-T4-03** | End-to-end | Regen bypass impossible | 1. From passing draft, regen **Insight** with note that invites a new unsourced number 2. If validator FAIL after regen, attempt Publish | Still **blocked** | Matches CI `test_section_regen_cannot_bypass_validator` |

---

## 3. Cross-cutting regression suite (Phase 1 / 2)

Run after Phase 3 scenarios to ensure nothing regressed.

| ID | Where | Steps | Expected |
|----|-------|-------|----------|
| **REG-01** | `/pulse` | Load feed; click first card | Feed p95 acceptable; Thread opens |
| **REG-02** | `/thread/[id]` | Switch ICE tabs Insight → Context → Evidence → Dissent → Framework | All tabs render; Evidence matrix loads |
| **REG-03** | `/mirror` | Log prediction on published card (if enrolled) | Prediction saves; no synthetic leakage |
| **REG-04** | `/lens` | Submit query; open result | Lazy confidence panel optional; no 500 |
| **REG-05** | `/map` + one sector slug | Open Map index and one deep-dive | 200; Lighthouse not re-run here but page loads |
| **REG-06** | `/admin/queue` | Filter by category; open event row | Queue works without auth (known Phase 1 caveat — document exposure) |
| **REG-07** | Notifications | Publish card (P3-T4-02) | In-app notification for subscribers (if configured) |
| **REG-08** | Signal monitor | During NSE hours, wait 30 min or inspect `confidence_gate_log` | Monitor job runs; uses float tier not source-count heuristic |

---

## 4. Recommended test execution order

Execute in this order to minimize setup duplication:

1. **Pre-flight** (§0)  
2. **P3-S0 / P3-T1** — isolation first (trust foundation)  
3. **P3-S1f** — market facts (blocks draft if broken)  
4. **P3-S1d / P3-S1c** — ingest pipeline (SQL + logs)  
5. **P3-S1e** — watchlist escalate  
6. **P3-T2 smoke** — combined pipeline  
7. **P3-S1g / P3-S1h / P3-T3** — confidence API + UI  
8. **P3-S1i → P3-S1j → P3-S1k → P3-T4** — full editorial golden path (allow 30–60 min; LLM regen consumes budget)  
9. **Regression** (§3)

---

## 5. Evidence capture template

Copy into your test log (Notion, sheet, or `docs/plans/phase3-go-no-go.md` evidence links).

| Scenario ID | Date (UTC) | Tester | Result | Evidence link / notes |
|-------------|------------|--------|--------|------------------------|
| P3-S0-04 | | | PASS/FAIL | |
| P3-T4-02 | | | PASS/FAIL | |
| … | | | | |

**Minimum bar for "Phase 3 pause go":**

- All **P3-T*** spot-checks PASS (T1, T2 smoke, T3, T4 golden path)  
- Zero synthetic leakage in Pulse/Mirror (S0/T1)  
- Publish golden path (T4-02) PASS on production  
- Regression REG-01–REG-06 PASS  

---

## 6. Known production caveats (do not fail wrong branch)

| Topic | Behaviour |
|-------|-----------|
| `/admin/queue` auth | Phase 1 routes may lack RBAC — network perimeter expected until hardened |
| Sunday digest | Template exists; **no Render cron** yet — digest send is manual |
| Draft from event | No UI button on queue — use `POST /api/cards/draft-from-event` |
| FoW banner | Full named banner is **P3-S1l** — dampener + aside callout may work without feed banner |
| LLM caps | Section/full regen counts against daily Gemini budget — sequence tests to avoid 429 |
| API proxy latency | Feed p95 may exceed 800 ms (Phase 2.5 PO waiver) — not a Phase 3 functional fail |
| SSR / RSC first paint | Pulse feed, Thread card, and Mirror dashboard are fetched on the **server**; browser Network may only show `?_rsc=` flights plus client calls (`market-facts`, `saved-threads`). Use §1 “Three ways to get inspectable JSON” — not finding `feed` on first load is **not** a fail |

---

## 7. Appendix — operator curl cheatsheet

Replace placeholders before running.

```bash
# Pulse feed (synthetic isolation spot-check)
curl -s "https://investment-assistant-3eqc.onrender.com/api/feed" | jq '.cards[].title'

# Same via browser proxy (while on Vercel origin)
# https://investment-assistant-frontend.vercel.app/backend/api/feed

# Thread card detail
curl -s "https://investment-assistant-3eqc.onrender.com/api/cards/<CARD_UUID>?view=current" | jq .

# Mirror dashboard (requires Bearer token from signed-in session)
curl -s "https://investment-assistant-3eqc.onrender.com/api/mirror/dashboard" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq .

# Market facts
curl -s "https://investment-assistant-3eqc.onrender.com/api/market-facts" | jq .

# Confidence breakdown
curl -s "https://investment-assistant-3eqc.onrender.com/api/events/<EVENT_UUID>/confidence-breakdown" | jq .

# Draft from event (editorial)
curl -s -X POST "https://investment-assistant-3eqc.onrender.com/api/cards/draft-from-event" \
  -H "Content-Type: application/json" \
  -d '{"event_id":"<EVENT_UUID>","editor_notes":null}' | jq .

# Admin publish (requires passing validator + checklist)
curl -s -X POST "https://investment-assistant-3eqc.onrender.com/api/admin/cards/<CARD_UUID>/publish" \
  -H "Content-Type: application/json" \
  -d '{"plain_english_confirmed":true}' | jq .

# Section regen
curl -s -X POST "https://investment-assistant-3eqc.onrender.com/api/admin/cards/<CARD_UUID>/regenerate-section" \
  -H "Content-Type: application/json" \
  -d '{"section":"insight","editor_note":"Tighten lede; ground all numbers."}' | jq .
```

---

## 8. Related documentation

| Document | Purpose |
|----------|---------|
| `docs/plans/finnwise-phase3-implementation-tasks.md` | Story acceptance criteria |
| `docs/plans/phase3-go-no-go.md` | Launch checklist — fill evidence after this run |
| `docs/intelligence-pipeline-overview.md` | Pipeline mental model |
| `docs/Post Implementation documentation/Phase3_*.md` | Per-story implementation detail |
| `docs/plans/phase3-calibration.md` | Day 30/60 scorer recalibration (after soak) |

---

*After completing this pass, update `docs/plans/phase3-go-no-go.md` T1–T4 evidence with links to your captured results, then proceed to P3-S1l only when editorial golden path is green.*
