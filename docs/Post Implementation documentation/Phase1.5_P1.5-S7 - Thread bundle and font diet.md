# Post Implementation Detailed Document — P1.5-S7

**Version:** v1.0 | **Date:** 23-05-2026  
**Story ID:** P1.5-S7 (Phase 1.5, Story 7)  
**Reference plan:** `docs/plans/finnwise-phase1.5-implementation-tasks.md`

---

## Narrative style

**P1.5-S5/S6** removed the client-fetch waterfall: Pulse and Thread now ship card data in the first HTML response. Baseline Lighthouse (May 2026) still showed **Thread TBT ~710 ms** on mobile — heavy JavaScript parse/execute (ICE layers, aside widgets, three Google fonts) blocked main-thread interactivity after content appeared.

**P1.5-S7** reduces that main-thread cost without changing editorial behaviour. **`ThreadExperience`** code-splits inactive ICE tabs and all aside widgets via **`next/dynamic`**: **Insight** stays eager (default tab); **Context** and **Evidence** load only after unlock/tab selection. Aside blocks (**LifecycleTracker**, **SignalsToWatch**, **ConfidenceComposition**, **BiasFlags**) defer with **`ssr: false`** (below fold, hidden on mobile). **Playfair Display** and **DM Mono** moved out of the root layout into **`thread/layout.tsx`** via **`lib/fonts/editorial.ts`**; **Inter** remains global. Pulse filter-refetch skeletons use **fixed 152px rows** mirroring **`EventCard`** layout to avoid skeleton→card height jumps.

**Tests executed and passed:** TypeScript **`npm run typecheck`**; Jest **`npm test`** — **22 suites, 47 tests** (including Thread **`InsightLayer`**, **`BiasFlags`**, **`useCard`**, Pulse **`EventCard`**, **`usePulseFeed`**); production **`npm run build`** succeeded. Local Lighthouse mobile (prod server, CPU 4× slowdown) on Thread: **TBT 70 ms** (baseline production trace: **710 ms**). No new backend tests (no backend changes).

If you only remember **three anchors**: (1) **Insight stays static-imported** — do not lazy-load the default tab; (2) **editorial fonts only under `/thread`** — Pulse/onboarding fall back to Georgia/system mono; (3) **aside dynamic imports use `ssr: false`** — intentional TBT trade-off for mobile.

---

## PART A — CORE DOCUMENT

### A1. HIGH LEVEL USER STORY DESCRIPTION

| Field | Value |
|--------|--------|
| **Story ID** | P1.5-S7 |
| **Title** | Thread bundle and font diet |
| **Category** | **Frontend** (code splitting, font loading, Pulse skeleton UX) |

**What this story aimed to achieve (plain language)**

Make Thread interactive quickly after SSR content appears by shrinking the initial JavaScript bundle and font payload. Lazy-load non-default ICE tabs and sidebar widgets, scope editorial fonts to Thread routes, and fix Pulse skeleton row heights so filter refetches do not shift layout.

**How it fits into the overall application**

Phase 1.5 optimizes Pulse + Thread end-to-end performance. **P1.5-S5/S6** delivered SSR data loading; **P1.5-S7** addresses main-thread blocking (TBT) that SSR alone cannot fix. **P1.5-S8** (a11y), **P1.5-S9** (Lighthouse CI), and **P1.5-S10** (production sign-off) depend on Thread components being stable after this split.

---

### A2. LOWER LEVEL DETAILS OF THE USER STORY

**Sub-stories / checklist items and what each delivers**

| Sub-task | Scope |
|----------|--------|
| **1.5.7.1** | **`ContextLayer`** and **`EvidenceLayer`** dynamic-imported; render gated by **`maxUnlockedTier`** / active tab. **`InsightLayer`** static (active tab first). |
| **1.5.7.2** | Aside widgets dynamic-imported with loading skeletons and **`ssr: false`**. |
| **1.5.7.3** | **`lib/fonts/editorial.ts`** + **`thread/layout.tsx`** scope Playfair/DM Mono; root layout keeps Inter only. |
| **1.5.7.4** | **`FeedSkeletonRow`** in **`PulseClient`** — fixed **152px** height matching EventCard structure. |
| **1.5.7.5** | Lighthouse mobile performance on Thread: **TBT 70 ms** local prod (<250 ms acceptance). |

**Functional breakdown — ICE lazy load**

```
ThreadExperience (client)
├── InsightLayer          ← static import (always in initial chunk)
├── ContextLayer          ← dynamic(); mounts when maxTier ≥ 1 OR iceTab = context
└── EvidenceLayer         ← dynamic(); mounts when maxTier ≥ 2 OR iceTab = evidence
```

**Functional breakdown — aside lazy load**

```
aside (lg:block only)
├── LifecycleTracker      ← dynamic(), ssr: false
├── SignalsToWatch        ← dynamic(), ssr: false
├── ConfidenceComposition ← dynamic(), ssr: false
└── BiasFlags             ← dynamic(), ssr: false
```

**Functional breakdown — font scoping**

```
app/layout.tsx                    → Inter only (--font-inter on <html>)
app/(app)/thread/layout.tsx       → Playfair + DM Mono CSS vars on wrapper div
Pulse / onboarding / admin / sign-in → font-display / font-mono use fallbacks (Georgia, ui-monospace)
```

**Edge cases, validations, and error handling**

| Scenario | Behaviour |
|----------|-----------|
| User on Insight tab (default) | No Context/Evidence chunks downloaded |
| User unlocks Context (tier 1) | Context chunk loads; **`IceLayerSkeleton`** during fetch |
| User taps Evidence before Context | ICE hint: "Reveal Context first…"; tier gate unchanged |
| User unlocks Evidence (tier 2) | Evidence chunk loads after Context tier satisfied |
| Mobile viewport | Aside chunks deferred; no aside SSR HTML |
| Pulse category filter change | Fixed-height skeleton rows; cards replace without large vertical jump |
| Current/Original toggle | Unchanged from S6 — not part of S7 scope |

**Business rules and logic enforced**

- ICE progressive unlock (Insight → Context → Evidence) unchanged.
- Aside and ICE panel data still sourced from same **`CardDetailResponse`** — no API changes.
- MMJ, SEBI, bias-flag, and track-record behaviour untouched.

---

### A3. DECISIONS MADE DURING EXECUTION

| Decision | Rationale | Alternatives not chosen |
|----------|-----------|-------------------------|
| **Insight static, Context/Evidence dynamic** | Acceptance: active tab first; Insight is default on every load. | **Dynamic all three tabs**: delays first meaningful ICE paint. |
| **Conditional render + dynamic import** | Prevents chunk download until tier/tab gate passes. | **Dynamic import only**: chunks may still prefetch when referenced. |
| **Aside `ssr: false`** | Hidden on mobile (`lg:block`); reduces SSR HTML + initial JS on small viewports. | **SSR aside**: larger initial payload on desktop for marginal SEO gain. |
| **Fonts scoped to `/thread` layout** | Removes two font families from Pulse first load. | **Keep all fonts global**: simpler but wastes bytes on Pulse. |
| **152px skeleton height** | Matches typical EventCard without instrument chips. | **Match max card height**: over-reserves space on short cards. |

**Assumptions**

- Users spend most Thread time on Insight tab first — lazy tabs rarely needed on first paint.
- Pulse **`font-display`** / **`font-mono`** on non-Thread routes are acceptable with system fallbacks until a future story scopes fonts to Pulse editorial surfaces.

**⚠️ Critical — do not reverse lightly**

- **Do not lazy-load `InsightLayer`** — regresses default-tab first paint and acceptance criteria.
- **Do not move Playfair/DM Mono back to root `app/layout.tsx`** without measuring Pulse TBT impact.
- **Do not SSR aside widgets without re-benchmarking mobile TBT**.

---

### A4. APPLICATION LINKAGE SUMMARY

| Direction | Dependency |
|-----------|------------|
| **Upstream** | **P1.5-S5** (Pulse SSR), **P1.5-S6** (Thread SSR + stable **`ThreadExperience`**) |
| **Downstream** | **P1.5-S8** (a11y on Thread components), **P1.5-S9** (Lighthouse CI budgets), **P1.5-S10** (production sign-off) |
| **Shared** | **`ThreadExperience.tsx`**, **`PulseClient.tsx`**, **`app/layout.tsx`**, **`tailwind.config.ts`** (`font-display`, `font-mono` tokens) |

---

### A5. DESIGN CHOICES

| Area | Choice |
|------|--------|
| **Architecture** | **`next/dynamic`** code splitting in client **`ThreadExperience`**; nested route layout for font CSS variables |
| **Database** | **None** |
| **API** | **None** — read-only consumption of existing **`GET /api/cards/{id}`** payload from S6 SSR |
| **UI/UX** | Brief skeleton placeholders for lazy ICE/aside chunks; Pulse skeleton mirrors card anatomy at fixed height |
| **Libraries** | **None added** — Next.js **`next/dynamic`**, existing **`next/font/google`** |

---

### A6. FILES CREATED

| File Name | File Path | Purpose |
|-----------|-----------|---------|
| `editorial.ts` | `frontend/lib/fonts/editorial.ts` | Playfair + DM Mono definitions; **`editorialFontVariables`** class string |
| `layout.tsx` | `frontend/app/(app)/thread/layout.tsx` | Applies editorial font CSS variables to all Thread routes |

---

### A7. FILES MODIFIED

| File Name | File Path | What Changed |
|-----------|-----------|--------------|
| `ThreadExperience.tsx` | `frontend/app/(app)/thread/_components/ThreadExperience.tsx` | Dynamic ICE/aside imports; tier-gated panel render; **`IceLayerSkeleton`** / **`AsideBlockSkeleton`** |
| `layout.tsx` | `frontend/app/layout.tsx` | Inter only; removed global Playfair/DM Mono from `<html>` |
| `PulseClient.tsx` | `frontend/app/(app)/pulse/_components/PulseClient.tsx` | **`FeedSkeletonRow`** with fixed **152px** height |
| `finnwise-phase1.5-implementation-tasks.md` | `docs/plans/finnwise-phase1.5-implementation-tasks.md` | P1.5-S7 acceptance criteria and tasks marked complete |

---

### A8. TESTS EXECUTED

**Summary**

| Suite / script | Command | Result | Date |
|----------------|---------|--------|------|
| TypeScript | `npm run typecheck` (from `frontend/`) | **Passed** | 23-05-2026 |
| Jest (full frontend) | `npm test` (from `frontend/`) | **22 suites, 47 tests passed** | 23-05-2026 |
| Production build | `npm run build` (from `frontend/`) | **Passed** — `/thread/[cardId]` 11.1 kB, First Load JS 189 kB | 23-05-2026 |
| Lighthouse mobile | `npx lighthouse` on local prod Thread (CPU 4×) | **TBT 70 ms** | 23-05-2026 |
| Backend pytest | Not run for S7 (no backend changes) | N/A | — |

**Thread-related Jest suites (regression after code split)**

| Test file | What it verifies | Status |
|-----------|------------------|--------|
| `InsightLayer.test.tsx` | Insight panel rendering with instruments/dissent | ✅ Passed |
| `BiasFlags.test.tsx` | Aside bias audit display | ✅ Passed |
| `DissentingView.test.tsx` | Dissent section copy/structure | ✅ Passed |
| `InstrumentCard.test.tsx` | Instrument row badges | ✅ Passed |
| `PredictionLogger.test.tsx` | Prediction logger interaction | ✅ Passed |
| `screen3CopyLint.test.ts` | Thread copy lint rules | ✅ Passed |
| `useCard.test.ts` | SSR hydration, Original toggle, Current restore (S6) | ✅ Passed |

**Pulse / shared suites**

| Test file | What it verifies | Status |
|-----------|------------------|--------|
| `usePulseFeed.test.ts` | SSR **`initialData`** hydration, filter refetch | ✅ Passed |
| `EventCard.test.tsx` | Event card rendering/selection | ✅ Passed |
| `server.test.ts` | Server-side fetch helpers (S5/S6) | ✅ Passed |

**Manual / script validation (required before production sign-off)**

| Check | What to verify | Status |
|-------|----------------|--------|
| Thread ICE tab lazy load | Context/Evidence load on unlock; Insight immediate | ⏳ **Manual — see B5** |
| Thread aside on desktop | Aside widgets appear after brief skeleton | ⏳ Manual |
| Pulse filter skeleton CLS | Skeleton rows stable height during refetch | ⏳ Manual |
| Fonts on Pulse vs Thread | Thread uses Playfair/DM Mono; Pulse uses fallbacks | ⏳ Manual |
| Production Lighthouse Thread TBT | **<250 ms** on Vercel mobile | ⏳ **P1.5-S10** |
| DevTools Coverage (optional) | Context/Evidence chunks not loaded until tab unlock | ⏳ Manual |

---

## PART B — EXTENDED REFERENCE

### B1. DATABASE / DATA MODEL CHANGES

- **None.** S7 is frontend bundle and font loading only.

### B2. API / INTEGRATION CONTRACTS

- **None created or modified.** Thread still consumes **`CardDetailResponse`** from **`GET /api/cards/{id}`** (SSR via S6, client toggle via existing **`useCard`**).

### B3. BUSINESS LOGIC & RULES (Detailed)

**ICE tier gating (unchanged behaviour, new load timing)**

```
maxUnlockedTier = 0 → Insight only (Context/Evidence chunks not mounted)
User unlocks Context (tier 1) → revealContext(); ContextLayer chunk loads
User unlocks Evidence (tier 2) → EvidenceLayer chunk loads (requires tier ≥ 1)
```

**Font resolution by route**

| Route | `--font-playfair` | `--font-dm-mono` | Visible typography |
|-------|-------------------|------------------|-------------------|
| `/thread/*` | Set on layout wrapper | Set on layout wrapper | Editorial display + mono labels |
| `/pulse`, `/onboarding`, etc. | Unset (inherits empty) | Unset | Tailwind fallbacks: Georgia, ui-monospace |

### B4. KNOWN CONSTRAINTS & TECH DEBT

- **Pulse/onboarding `font-display` / `font-mono`** no longer load Playfair/DM Mono — intentional trade-off; Pulse headlines use Georgia until a future font-scoping story if product requires editorial fonts on Pulse.
- **Aside `ssr: false`** — desktop users may see aside skeleton flash on first paint; acceptable for TBT win.
- **Local Lighthouse TBT (70 ms)** used loopback prod server — production Vercel + Render proxy path may differ; **P1.5-S10** owns prod re-benchmark.
- ⚠️ **After font layout change**, dev server may log **404 on `.woff2`** until cache cleared or dev restarted — hard refresh if fonts look wrong.
- **No automated test for dynamic import boundaries** — manual Network/Coverage tab check recommended.

### B5. TESTING NOTES

**Manual checklist (run locally before merge/deploy)**

1. **Start stack**
   - Backend: `uvicorn` on port 8000
   - Frontend: `npm run dev` from `frontend/` with root **`.env.local`**

2. **Thread — Insight first paint (S6 + S7)**
   - Open **`/thread/{cardId}`** from Pulse
   - **Expect:** title + Insight tab content immediately (SSR); no full-page skeleton
   - DevTools → **Network** → filter JS: **no** `ContextLayer` / `EvidenceLayer` chunks on initial load

3. **Thread — ICE progressive unlock**
   - Tap **Context** tab
   - **Expect:** brief skeleton, then context steps; **`revealContext`** still fires
   - Tap **Evidence** (after Context unlocked)
   - **Expect:** evidence panel loads; tier hint if Context not unlocked first

4. **Thread — aside (desktop ≥1024px)**
   - **Expect:** lifecycle, signals, confidence, bias blocks appear (may flash skeleton first)
   - Resize to mobile: aside hidden; no horizontal overflow errors

5. **Thread — Current/Original toggle (regression)**
   - Toggle **Original** → client fetch
   - Toggle **Current** → restores SSR data without refetch

6. **Pulse — skeleton CLS**
   - Change category filter pills
   - **Expect:** three fixed-height skeleton rows; cards replace without large layout jump

7. **Fonts — visual spot check**
   - **Thread:** card title in Playfair (serif display)
   - **Pulse:** card headlines use fallback serif (Georgia) — verify acceptable with design

8. **Production (after deploy — P1.5-S10)**
   - Lighthouse mobile on production **`/thread/{cardId}`**
   - **Expect:** TBT **<250 ms**; compare to baseline **710 ms**
   - Optional: save trace to **`Page Load Performance/`**

| Area | Automated | Manual |
|------|-----------|--------|
| Typecheck + Jest regression | ✅ | — |
| ICE lazy chunks not on first load | — | ⏳ Network / Coverage |
| ICE tier unlock behaviour | — | ⏳ Manual |
| Pulse skeleton height | — | ⏳ Manual |
| Font scoping Pulse vs Thread | — | ⏳ Visual |
| Production Lighthouse TBT | — | ⏳ P1.5-S10 |

### B6. CONFIGURATION & ENVIRONMENT NOTES

| Variable | Role |
|----------|------|
| `NEXT_PUBLIC_API_BASE_URL` | Unchanged from S6 — SSR card fetch (not S7-specific) |
| (none new) | S7 introduces no new env vars or feature flags |

**Deploy sequencing:** deploy frontend after S5/S6 are live. No backend deploy required for S7 alone.

**Local prod Lighthouse (optional re-run):**

```powershell
cd frontend
npm run build
npm run start -- -p 3001
# separate terminal:
npx lighthouse http://localhost:3001/thread/{cardId} --only-categories=performance --form-factor=mobile --screenEmulation.mobile=true --throttling.cpuSlowdownMultiplier=4
```

### B7. HANDOVER NOTES FOR DEVELOPERS

- **Start here:** `frontend/app/(app)/thread/_components/ThreadExperience.tsx`, `frontend/lib/fonts/editorial.ts`, `frontend/app/(app)/thread/layout.tsx`, `frontend/app/layout.tsx`
- **Common mistake:** lazy-loading **`InsightLayer`** — breaks "active tab first" acceptance criteria
- **Common mistake:** moving editorial fonts back to root layout — regresses Pulse font payload
- **Common mistake:** removing **`shouldLoadContext` / `shouldLoadEvidence` guards** — downloads inactive tab chunks on every load
- **S8 owner:** contrast/heading fixes touch same Thread components — test after a11y token changes
- **S9 owner:** add Lighthouse budget script; Thread TBT budget **<200 ms** per phase plan
- **Where to benchmark:** compare against `Page Load Performance/investment-assistant-frontend.vercel.app-20260523T151456- Thread.json` (baseline TBT 710 ms)

---

## Baseline vs post-S7 metrics

| Metric | Baseline (prod mobile, 2026-05-23) | Post-S7 (local prod, 2026-05-2026) |
|--------|-------------------------------------|-------------------------------------|
| Thread TBT | 710 ms | **70 ms** |
| Thread Performance score | 78 | Re-run on prod in **P1.5-S10** |
| Pulse CLS | ~0.0001 (minor skeleton shift noted in plan) | Fixed-height skeleton (verify manually) |
