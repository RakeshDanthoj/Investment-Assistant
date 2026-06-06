# FinnWise — Admin Guide (Editorial + Operations)

**Version:** v1.0  
**Audience:** Product Owners / Editors / Admin operators  
**Scope:** Editorial queue, review workspace (draft → publish), signals, factor DB view, editor watchlist  

---

## How to use this guide

This guide is organised by **page**. For each page you get:

- **What it’s for**
- **Where to look for critical information**
- **Happy path workflow**
- **Common issues and what they usually mean**

---

## 1) Roles and access boundaries

### 1.1 Editor/admin allow-list (important)

Some editorial pages are gated by the **comma-separated** environment variable `ADMIN_EMAILS`.

- If your email is not in `ADMIN_EMAILS`, you will see a **403** on editor-only surfaces (e.g. Watchlist).
- `ADMIN_EMAILS` must be set consistently in both frontend and backend environments for a smooth workflow.

### 1.2 Editorial vs user surfaces

You will use both:

- **User surfaces** (Pulse/Thread) to verify what end users see after publishing.
- **Editorial surfaces** (admin queue/review/watchlist) to create, validate, and publish content.

---

## 2) Editorial workflow (happy path)

### 2.1 Happy path — ingest → draft → review → publish → verify

1. **Draft events arrive** in the **Draft event queue** (`/admin/queue`).
2. Pick a high-confidence event and open the source link to confirm it’s real.
3. Create or open the associated draft in the **Review workspace** (`/admin/review/[draftId]`).
4. Ensure the draft passes the **publish gate stack**:
   - Number validation
   - Editorial checklist items (automated)
   - Plain-English confirmation (manual)
5. Publish.
6. Verify on **Pulse** (`/pulse`) and **Thread** (`/thread/[cardId]`) as a normal user would.

---

## 3) Draft event queue (`/admin/queue`)

### What this page is for

This is the editorial “inbox” of ingested events that are still in **draft** lifecycle state.

### Where to look for critical information

- **Header copy**: confirms you’re looking at “Draft event queue”.
- **Market facts banner** (top of page): critical operational signal.
  - If critical facts are **unavailable**, drafting/publishing flows may be held downstream.
- **Filters**
  - **Category toggles**: narrow by event category.
  - **Source toggles**: isolate ingestion channels (NewsAPI, RBI RSS, NSE/BSE, etc.).
- **Table**
  - **Confidence**: the primary sorting signal (highest first).
  - **Title**: event title (editorial should check it’s not redundant).
  - **Category / Source**: helps interpret why it appears and how reliable it is.
  - **Link**: open canonical URL (or fallback).

### Happy path workflow

1. Start with **All categories** + **All sources**.
2. Scan top 5 rows by **Confidence**.
3. Open the **Link** for your chosen event and confirm:
   - It’s a real source
   - It’s not obviously duplicated in the queue
4. Proceed to draft/review workflow (your org may have a separate “draft creation” step; the queue itself is an ingest view).

### Common issues and what they mean

- **Queue is empty**
  - Usually: ingestion jobs haven’t run recently, or no matches for the filters.
  - Confirm filters are reset to “All”.
- **Banner shows market facts degraded/unavailable**
  - Usually: upstream market-facts provider issue. Draft creation may be held until critical facts recover.
- **Page shows a network error and hints about `NEXT_PUBLIC_API_BASE_URL`**
  - Usually: frontend can’t reach backend, or CORS/proxy mismatch in environment config.

---

## 4) Review workspace (`/admin/review/[draftId]`)

### What this page is for

This is the editorial workspace for converting a draft into a publishable Event Intelligence Card.

### The publish gate stack (what blocks publishing)

Publishing is intentionally not a single button—it’s a stack of gates:

- **Number validation gate**: blocks if the draft contains ungrounded numeric claims.
- **Editorial checklist**: automated checks (e.g., dissent length, freshness rules, SEBI language).
- **Plain-English confirmation**: manual checkbox that confirms the writing is understandable.

Even if the UI disables the button, the backend must still reject invalid publish attempts (hard 422-type failures).

### Where to look for critical information

- **Publish section**
  - Button enabled/disabled state is the fastest overall health signal.
- **Number validator output**
  - Look for lists of ungrounded sentences or failing statuses.
- **Checklist panel**
  - PASS/FAIL per item. Treat FAIL as “must fix” unless your internal policy says otherwise.
- **Regeneration controls (section regen)**
  - Regenerating a section can move you from PASS → FAIL again; always re-check gates after regen.

### Happy path workflow

1. Read the **Insight** and ensure it matches the event claim you intend to publish.
2. Review **Evidence** for grounding, then fix any number-validation failures.
3. Ensure all checklist items show **PASS**.
4. Tick **Plain English** only after you actually read the draft end-to-end.
5. Publish.
6. Verify on user surfaces:
   - **Pulse**: card appears and reads well in the feed context.
   - **Thread**: full card renders and confidence breakdown is consistent.

### Common issues and what they mean

- **Publish disabled even after edits**
  - Usually: one gate still failing (often a hidden number-validation or checklist failure).
- **After regenerating a section, publish becomes blocked again**
  - Expected behaviour: regen re-runs validators; fix new failures before publishing.

---

## 5) Signal queue (`/admin/signal-queue`)

### What this page is for

This is an operational view of surfaced signals (typically during market hours) used for monitoring and editorial awareness.

### Where to look for critical information

- **Tier / confidence labels**: interpret urgency and uncertainty.
- **Timestamps / recency**: signals are time-sensitive; treat stale signals as historical, not actionable.

### Happy path workflow

1. Scan newest items first.
2. Open the relevant Thread card for context and evidence.
3. If required, escalate into editorial drafting workflow (team process-dependent).

---

## 6) Factor DB view (`/admin/factor-db`)

### What this page is for

This is an admin view into the factor database—used to understand what structured factors and instrument mappings exist for the intelligence pipeline.

### Where to look for critical information

- **Factor names / coverage**: what the pipeline can detect and explain.
- **Instrument mappings**: which tickers/entities are in scope.

### Happy path workflow

1. Use this page when a card/event looks “thin” and you suspect missing factor coverage.
2. Correlate with the editorial experience: if a sector lacks factors, Lens/Thread may be less specific.

---

## 7) Editor watchlist (`/editor/watchlist`)

### What this page is for

The watchlist is for **slow-burn** risks/themes that don’t fit a single breaking-news event but should be tracked and periodically reviewed.

### Access control (critical)

- Requires you to be signed in and included in `ADMIN_EMAILS`.
- If `ADMIN_EMAILS` is not set, the page will show “Watchlist unavailable” with setup instructions.

### Where to look for critical information

- **Item status**: watching / closed / escalated (exact labels may vary).
- **Last reviewed timestamp** (if visible): indicates whether the theme is being actively monitored.
- **Escalate action**: sends an item into the editorial pipeline as an event (expect it to surface in the draft queue).

### Happy path workflow

1. Review “watching” items and update their status after checking reality.
2. If a theme becomes acute, click **Escalate**.
3. Confirm the escalated item appears downstream (typically in `/admin/queue` as a watchlist-sourced draft).

### Common issues and what they mean

- **403 restricted to editors**
  - Your email isn’t allow-listed. Add to `ADMIN_EMAILS` and redeploy/reload.
- **Watchlist unavailable**
  - `ADMIN_EMAILS` env var is missing/empty in the current environment.

---

## 8) Verification checklist (what to confirm before you call something “done”)

- **User-visible check**
  - Card shows correctly on `/pulse`
  - Card reads correctly on `/thread/[id]`
- **Uncertainty honesty**
  - Confidence tier breakdown renders when expanded
  - If uncertainty is high, the UI reflects that (no hidden “certainty”)
- **Compliance posture**
  - No “buy/sell/hold” language or personalised advice tone in published content

