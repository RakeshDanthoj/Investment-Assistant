# Post Implementation Detailed Document — P2-S9

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S9 (Phase 2, Story 9)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Narrative style (read this first)

**Phase 1 (P1-S9)** gave Portfolio Protectors a Pulse feed filtered by onboarding horizon and category — but not by what they actually own. **P2-S9** adds **session-only holdings personalisation**: users open **Session holdings** from the sidebar user chip, search instruments from the Factor DB `instruments` table, and save tickers that stay **only in this browser tab** (HMAC-sealed `sessionStorage`, keyed to `finnwise_session_id` in `localStorage`). FinnWise never persists holdings server-side.

For **The Pulse**, the client sends an opaque `personalisation_token` (`v1:` + sorted HMAC-SHA256 digests per ticker) on `GET /api/feed`; the backend **`feed_ranker.rerank()`** promotes cards whose `instrument_assessments` intersect that token. For **The Thread**, intersection is computed **entirely on the client** — `HoldingCallout` shows *“What this means for your {name}”* when a card assessment matches a saved holding. Raw ticker lists never appear in API query strings as a separate parameter.

**Tests executed and passed (at story close-out):**

| Suite | Command | Result |
|-------|---------|--------|
| Backend | `python -m pytest tests/test_feed_personalisation.py tests/test_personalisation_token.py -q` | **5 passed** |
| Backend regression | `python -m pytest tests/test_feed_filtering.py -q` | **4 passed** |
| Frontend | `npm test -- lib/personalisation/sessionHoldings.test.ts` | **5 passed** |
| Frontend | `npm test -- --testPathPattern="HoldingCallout\|UserChip"` | **6 passed** (2 + 4) |

**Three anchors:** (1) **No server storage of holdings** — PRD §11.1 / plan legal note; (2) **Wire format is token-only** — backend ranks by digest intersection, not a `holdings[]` body; (3) **Session id required to save** — seal HMAC uses onboarding `session_id`, not Supabase JWT (holdings are pre-auth-bridge friendly for session profile users).

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P2-S9 |
| **Title** | Portfolio Protector personalisation (session-only holdings) |
| **Category** | **Full Stack** (session UI + feed API + ranker + instrument search + tests) |

**What this story aimed to achieve (plain language)**

Portfolio Protectors want The Pulse and The Thread to surface events that matter to **what they hold today**, without FinnWise storing bank balances, demat IDs, or a permanent holdings file. This story adds a lightweight **Session holdings** modal, keeps data in **tab-scoped browser storage**, and personalises Pulse ordering and Thread copy using **hashed instrument tokens** — not plain ticker lists on the server.

**How it fits into the overall application**

- **Upstream:** **P1-S2** (mode detection → Pulse-first for protectors), **P1-S9** (Pulse feed + `instrument_assessments` on cards), **P1-S5** (`public.instruments` for typeahead), **P1-S10** (Thread ICE + instrument rows).
- **Parallel:** **P2-S8** (Lens), **P2-S11** (Map sectors).
- **Downstream:** **P2-S10** (email on signals) may combine with saved threads; **Phase 3** legal pass re-reviews §11.1 storage; no new Lighthouse route in this story (**P2-S15**).

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items (plan mapping)**

| Sub-task | Delivered |
|----------|-----------|
| **9.1** | `HoldingsModal` — user chip menu → modal; debounced typeahead via `GET /api/instruments/search?q=` |
| **9.2** | `saveSessionHoldings` / `getSessionHoldings` / `clearSessionHoldings` — `sessionStorage` key `finnwise_session_holdings_v1`, HMAC seal keyed by `getStoredSessionId()` |
| **9.3** | `buildPersonalisationToken()` / `getPersonalisationToken()` — `v1:<digest>.<digest>…` from sorted tickers + shared salt |
| **9.4** | `GET /api/feed?personalisation_token=` → `feed_ranker.rerank()` on raw pulse rows before `build_card_payload` |
| **9.5** | `HoldingCallout` in `InsightLayer` when `intersectHoldingsWithInstruments()` non-empty |
| **9.6** | Modal copy: *“This data is not stored on our servers — it stays in this browser tab only…”* |
| **9.7** | Automated tests: re-rank, token parse, session-only storage, tamper rejection, callout visibility, UserChip menu |

**Functional breakdown**

1. **Entry:** Sidebar `UserChip` → **Session holdings (N)** → `HoldingsModal`.
2. **Search:** ≥2 characters → `searchInstruments()` → up to 10 rows from `instruments` (ticker + display name); already-selected tickers filtered out.
3. **Save:** Seal JSON `{ holdings: [...] }` with HMAC(sessionId, body); write `sessionStorage`; dispatch `finnwise-holdings-changed`.
4. **Pulse:** `usePulseFeed` appends `personalisation_token` when holdings exist; listens for `HOLDINGS_CHANGED_EVENT` to refetch.
5. **Feed API:** Optional query param; ranker counts assessment `instrument_id` digests in token set; sort key `(-intersection_count, -created_at)` with stable tie-break.
6. **Thread:** `useSessionHoldings` + intersection helper; blue alert above Insight with per-holding sentence.

**Edge cases, validations, and error handling**

| Scenario | Behaviour |
|----------|-----------|
| **No `finnwise_session_id` in localStorage** | `saveSessionHoldings` no-ops; holdings cannot be sealed (by design). |
| **Tampered sessionStorage** | `unsealHoldings` HMAC mismatch → returns `[]`. |
| **Empty / missing token on feed** | `rerank` returns rows unchanged. |
| **Salt mismatch client vs server** | Digests never match → re-rank has no effect (silent). |
| **Empty salt on server** | `rerank` no-op even if token present. |
| **Instrument search &lt; 2 chars** | No API call; suggestions cleared. |
| **DB unavailable** | `GET /api/instruments/search` → **503** `db_unavailable`; modal shows search error string. |
| **Tab closed** | `sessionStorage` cleared by browser — holdings gone. |
| **Sign out** | Holdings remain in tab until close (not tied to Supabase session). |

**Business rules enforced (PRD-aligned)**

- **§11.1 — no user financial data beyond session:** holdings never POSTed to backend; only opaque token on feed GET.
- **Instrument id = NSE ticker** (matches `instrument_assessments.instrument_id` text, e.g. `HDFCBANK`).
- **Case-insensitive intersection** for Thread callouts and token normalisation (`toUpperCase()`).
- **Explicit privacy disclosure** in modal header (task 9.6).

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **HMAC digest token (`v1:hex.hex…`)** | Server can rank by intersection without accepting `holdings[]` JSON; token opaque in logs. | Encrypted blob with server decrypt key: more coupling; still “sees” IDs server-side. |
| **Re-rank raw DB rows before `build_card_payload`** | Preserves `created_at` + full `instruments` list for scoring; payload stays unchanged. | Re-rank API cards after build: `created_at` dropped from payload. |
| **Thread personalisation client-only** | Card detail already loaded; no second API; no holdings on wire for Thread. | `personalisation_token` on `GET /api/cards/{id}`: unnecessary for callout-only UX. |
| **Seal key = onboarding `session_id`** | Plan tech note: HMAC keyed by user session; available before full JWT flows on all paths. | Supabase `user.id`: holdings lost for users without session id bridge. |
| **`sessionStorage` not `localStorage` for holdings** | Tab-scoped = “session-only” per PRD; survives refresh, not cross-tab persistence. | `localStorage`: would survive browser restart — weaker §11.1 story. |
| **Instrument search reads Factor DB table** | Plan: typeahead from `instruments`; banking seed provides tickers in dev. | Hard-coded ticker list: drifts from assessments. |
| **Shared salt via env (public on client)** | Required so client and server compute identical digests; salt is not secret holdings data. | Server-only salt with client sending raw IDs: violates “backend never sees list”. |

**⚠️ Critical — do not reverse without replanning**

- **Do not** add `holdings` JSON body or query param to any API — legal/product boundary for Phase 2.
- **Do not** persist holdings in Postgres, Supabase, or cookies — only `sessionStorage` + feed token.
- **Do not** change digest algorithm or `v1:` prefix without updating **both** `personalisation_token.py` and `crypto.ts` + redeploying matching env salts.
- **Do not** use `public` HTTP cache on feed when token is present (existing P1.5 guidance: feed is personalised).

**Assumptions**

- `PERSONALISATION_TOKEN_SALT` and `NEXT_PUBLIC_PERSONALISATION_TOKEN_SALT` are set to the **same value** in production (defaults match for local dev only).
- Users who skip onboarding may lack `session_id` — holdings UI works but save is ineffective until session id exists.
- Re-ranking is **relevance ordering only** — not filtering; non-matching cards remain in feed.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Linkage |
|-----------|---------|
| **Depends on** | **P1-S2** mode routing; **P1-S9** Pulse feed + assessments on cards; **P1-S5** `public.instruments`; **P1-S10** Thread `InsightLayer` / instrument rows; `getStoredSessionId()` from onboarding. |
| **Enables** | Stronger Portfolio Protector UX on Pulse/Thread; future stories may reuse token on other read paths (not in scope). |
| **Touches** | `GET /api/feed`, new `GET /api/instruments/search`, sidebar `UserChip`, `usePulseFeed`, `InsightLayer`. |
| **Legal / compliance** | Plan §754 — re-review in Phase 3; this story enforces session-only + token wire format. |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Pattern** | Client session store + opaque token; pure `feed_ranker` + `personalisation_token` helpers on server |
| **Database** | **No migration** — read-only `instruments` search; re-rank uses existing `instrument_assessments` on feed rows |
| **API** | `GET /api/feed?personalisation_token=` (optional); `GET /api/instruments/search?q=` (no auth; `Cache-Control: no-store`) |
| **UI** | Native `<dialog>` + fixed overlay; debounced search list; holdings chips with remove |
| **Crypto** | Web Crypto `HMAC-SHA256` (browser); Python `hmac` + `hashlib` (server); Jest polyfill via `webcrypto` in `jest.setup.ts` |
| **Events** | `finnwise-holdings-changed` window event for Pulse refetch + `useSessionHoldings` refresh |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `HoldingsModal.tsx` | `frontend/components/Holdings/` | Session holdings entry UI + privacy copy |
| `sessionHoldings.ts` | `frontend/lib/personalisation/` | Seal/unseal, token derivation, intersection helper |
| `sessionHoldings.test.ts` | `frontend/lib/personalisation/` | Session-only + tamper + token opacity tests |
| `crypto.ts` | `frontend/lib/personalisation/` | HMAC helpers + salt + token builder |
| `useSessionHoldings.ts` | `frontend/lib/personalisation/` | React hook + holdings-changed listener |
| `instruments.ts` | `frontend/lib/api/` | Client fetch for instrument search |
| `HoldingCallout.tsx` | `frontend/app/(app)/thread/_components/` | Per-holding Thread callout |
| `HoldingCallout.test.tsx` | `frontend/app/(app)/thread/_components/` | Empty vs non-empty render |
| `personalisation_token.py` | `backend/app/services/` | Digest + parse `v1:` token |
| `feed_ranker.py` | `backend/app/services/` | Intersection count + stable re-order |
| `instruments_search.py` | `backend/app/services/` | ILIKE search on `instruments` |
| `instruments.py` | `backend/app/api/` | `GET /instruments/search` route |
| `test_feed_personalisation.py` | `backend/tests/` | Re-rank promotion + no-op cases |
| `test_personalisation_token.py` | `backend/tests/` | Token parse + invalid prefix |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `feed.py` | `backend/app/api/` | Optional `personalisation_token` query param |
| `feed.py` | `backend/app/services/` | Call `rerank()` before `build_card_payload`; import ranker + settings |
| `settings.py` | `backend/app/core/` | `personalisation_token_salt` / `PERSONALISATION_TOKEN_SALT` |
| `main.py` | `backend/app/` | Register `instruments_router` under `/api` |
| `UserChip.tsx` | `frontend/components/Sidebar/` | Session holdings menu item + count |
| `UserChipContainer.tsx` | `frontend/components/Sidebar/` | Modal state + `useSessionHoldings` |
| `UserChip.test.tsx` | `frontend/components/Sidebar/` | Menu invokes `onManageHoldings` |
| `usePulseFeed.ts` | `frontend/lib/cards/` | Append token; refetch on holdings event |
| `InsightLayer.tsx` | `frontend/app/(app)/thread/_components/` | `HoldingCallout` + intersection |
| `jest.setup.ts` | `frontend/` | `TextEncoder` + `webcrypto` polyfill for HMAC tests |
| `finnwise-phase2-implementation-tasks.md` | `docs/plans/` | P2-S9 acceptance + tasks **9.0–9.7** marked complete |

---

### A8. TESTS EXECUTED

| Test file | What it verifies | Status |
|-----------|------------------|--------|
| `test_feed_personalisation.py::test_rerank_promotes_cards_with_holding_intersection` | Card with matching ticker sorts first | **Pass** |
| `test_feed_personalisation.py::test_rerank_noop_without_token` | `None` / `""` token leaves order | **Pass** |
| `test_feed_personalisation.py::test_rerank_noop_with_empty_salt` | Empty server salt disables re-rank | **Pass** |
| `test_personalisation_token.py::test_parse_token_extracts_digest_set` | `v1:` body parses to frozenset | **Pass** |
| `test_personalisation_token.py::test_parse_invalid_token_returns_empty` | Bad/missing prefix → empty set | **Pass** |
| `test_feed_filtering.py` (regression) | P1-S9 feed build unchanged | **Pass** (4 tests) |
| `sessionHoldings.test.ts` | sessionStorage only; seal round-trip | **Pass** |
| `sessionHoldings.test.ts` | Tampered payload rejected | **Pass** |
| `sessionHoldings.test.ts` | Token has no raw tickers | **Pass** |
| `sessionHoldings.test.ts` | `clear` empties store + token | **Pass** |
| `sessionHoldings.test.ts` | Case-insensitive intersection | **Pass** |
| `HoldingCallout.test.tsx` | Empty hidden; copy when hit | **Pass** |
| `UserChip.test.tsx` | Holdings menu + existing chip tests | **Pass** |

**Not automated in P2-S9:** E2E browser flow (chip → save → Pulse order change); production env salt parity check; instrument search against empty DB.

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

**No migration in P2-S9.**

| Table | Use |
|-------|-----|
| `public.instruments` | Typeahead: `ticker`, `display_name`, `exchange` |
| `public.instrument_assessments` | Feed rows include `instrument_id` (text ticker) for intersection |
| `public.cards` / `public.events` | Unchanged Pulse query |

**Seed dependency:** Banking sector seed (`backend/db/seeds/banking_sector.sql`) populates `instruments` for local/staging search.

---

### B2. API / INTEGRATION CONTRACTS

**`GET /api/feed`** (modified)

- **New query:** `personalisation_token` (optional, max 4096 chars) — opaque `v1:` digest list.
- **Auth:** None (same as P1-S9); still accepts `session_id`, `horizon`, `category`.
- **Behaviour:** When token + salt valid, card order re-ranked; response shape unchanged.
- **Example:**  
  `GET /api/feed?session_id=<uuid>&personalisation_token=v1:abc123...def456`

**`GET /api/instruments/search`** (new)

- **Query:** `q` (required, 1–64 chars)
- **Auth:** None
- **Cache:** `Cache-Control: no-store`
- **200 example:**
  ```json
  {
    "results": [
      {
        "instrument_id": "HDFCBANK",
        "display_name": "HDFC Bank Ltd",
        "exchange": "NSE"
      }
    ]
  }
  ```

**⚠️ There is no endpoint that accepts a holdings array.**

---

### B3. BUSINESS LOGIC & RULES (Detailed)

**Token construction (client)**

```
for each unique ticker T (uppercase):
  digest[T] = HMAC-SHA256(salt, T) as hex
token = "v1:" + sort(digest values).join(".")
```

**Re-rank (server)**

```
token_hashes = parse(token)  // frozenset of hex digests
for each card row:
  score = count of assessments where instrument_digest(id, salt) ∈ token_hashes
sort rows by (-score, -created_at, original_index)
```

**Thread callout (client)**

```
holdingIds = Set(holdings.map(h => upper(h.instrumentId)))
for each instrument on card:
  if upper(instrument_id) in holdingIds → show HoldingCallout line
```

**Session seal**

```
body = JSON.stringify({ holdings })
sig = HMAC-SHA256(sessionId, body)
stored = JSON.stringify({ v: 1, holdings, sig })
→ sessionStorage["finnwise_session_holdings_v1"]
```

---

### B4. KNOWN CONSTRAINTS & TECH DEBT

| Item | Notes |
|------|--------|
| **Salt visible in frontend** | `NEXT_PUBLIC_*` required for digest parity — not a substitute for protecting holdings at rest (holdings never sent). |
| **No holdings without session id** | Onboarding must persist `finnwise_session_id` for save to work. |
| **Re-rank is sort-only** | Low-relevance cards still appear; no “holdings-only feed”. |
| **Instrument universe** | Search limited to seeded `instruments` (Phase 1 banking); assessments may reference tickers not in table. |
| **SSR Pulse** | Server `fetchPulseFeed` does not pass token — first paint unranked; client refetch applies personalisation. |
| **Sign-out does not clear holdings** | Tab session storage independent of Supabase; may be desirable or confusing — document for support. |

---

### B5. TESTING NOTES

| Layer | Coverage |
|-------|----------|
| **Backend unit** | Token parse, re-rank ordering, no-op paths |
| **Backend regression** | Existing feed filtering tests |
| **Frontend unit** | Storage, tamper, token opacity, callout, chip menu |
| **Manual (recommended)** | Onboarding → add HDFCBANK → Pulse Network tab shows `personalisation_token` without `HDFCBANK` in URL → open Thread card with bank assessment → see callout |

**Manual checklist**

1. Confirm `finnwise_session_id` in Application → Local Storage.
2. User chip → Session holdings → search `HDFC` → add → Save.
3. Pulse: cards mentioning `HDFCBANK` rise (if present in feed).
4. Thread: open card with `HDFCBANK` assessment → blue “Your holdings” block.
5. Close tab → reopen → holdings gone.
6. Production: verify both salt env vars match after deploy.

---

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Where | Purpose |
|----------|--------|---------|
| `PERSONALISATION_TOKEN_SALT` | Backend (Render / `.env.local`) | Server-side digest + re-rank |
| `NEXT_PUBLIC_PERSONALISATION_TOKEN_SALT` | Frontend (Vercel / `.env.local`) | **Must match backend salt** |
| Default (dev only) | Both codebases | `dev-personalisation-salt-change-me` |

**Deploy sequencing:** Set salts → deploy backend → deploy frontend. Mismatched salt = personalisation silently disabled.

**No feature flag** — token omitted when user has no holdings.

---

### B7. HANDOVER NOTES FOR DEVELOPERS

**Before changing this code**

1. Read PRD §11.1 and plan risk note on personalisation drift.
2. Trace: `sessionHoldings.ts` → `usePulseFeed.ts` → `feed.py` / `feed_ranker.py`.
3. Thread-only UX: `InsightLayer.tsx` + `HoldingCallout.tsx` (no backend).

**Common mistakes**

- Adding `holdings` to API payloads “for convenience”.
- Storing holdings in `localStorage` or Supabase.
- Changing ticker normalisation on one side only (client vs server).
- Forgetting to redeploy both apps after salt rotation.

**Key paths**

| Concern | Path |
|---------|------|
| Modal UI | `frontend/components/Holdings/HoldingsModal.tsx` |
| Session store | `frontend/lib/personalisation/sessionHoldings.ts` |
| Pulse fetch | `frontend/lib/cards/usePulseFeed.ts` |
| Feed API | `backend/app/api/feed.py` |
| Re-rank | `backend/app/services/feed_ranker.py` |
| Token crypto | `backend/app/services/personalisation_token.py`, `frontend/lib/personalisation/crypto.ts` |

**Contact:** Product / compliance for any server-side storage of holdings; backend lead for feed cache policy if adding CDN to feed.

---

## Audit style summary

| Area | Status |
|------|--------|
| Plan tasks 9.0–9.7 | Complete |
| Acceptance criteria (5) | Met |
| Migrations | None required |
| Breaking API changes | None (`personalisation_token` optional) |
| PRD §11.1 session-only | Enforced in code + tests |

---

*End of document — P2-S9 v1.0*
