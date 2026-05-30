# Phase 3 — Launch-readiness go/no-go checklist (draft)

**Status:** Draft template for **P3-S8** — fill evidence links as gates complete.  
**Parent plan:** `docs/plans/finnwise-phase3-implementation-tasks.md`

---

## PRD2 intelligence test gates (T1–T5)

| Gate | Story | Evidence (CI) | Status |
|------|-------|---------------|--------|
| T1 | P3-T1 Synthetic isolation | `backend/tests/test_synthetic_isolation.py`, `test_query_synthetic_filter.py` | Green |
| T2 | P3-T2 Data pipeline | `backend/tests/test_data_pipeline_integration.py` | Green |
| T3 | P3-T3 Confidence scoring | `backend/tests/test_confidence_scoring_gate.py`, `test_confidence_breakdown_api.py`, `frontend/.../ConfidenceComposition.test.tsx` | Green |
| T4 | P3-T4 Editorial integrity | `backend/tests/test_editorial_integrity_e2e.py`, `frontend/app/admin/review/_components/ChecklistPanel.test.tsx` | Green |
| T5 | P3-T5 FoW + signal | _(pending P3-S1l, P3-S1m)_ | — |

**P3-T4 combined (recommended):**

```powershell
python -m pytest -q backend/tests/test_editorial_integrity_e2e.py
pnpm test ChecklistPanel.test.tsx
```

Proves: ungrounded number → publish 422; fix Evidence → auto checklist PASS → plain-English confirm → publish 200; section regen cannot bypass publish validator.

---

## Other P3-S8 sections (to complete in P3-S8)

- [ ] Legal sign-off (P3-S3)
- [ ] SLOs satisfied (P3-S5)
- [ ] Productisation dossier (P3-S4)
- [ ] Synthetic isolation spot-check in production
- [ ] Signal FP rate ≤ 10% or remediation plan (P3-S1m)
- [ ] Cross-phase performance standards (`docs/plans/cross-phase-performance-standards.md`)
- [ ] P3-S6 / P3-S7 **deferred** until this checklist returns **go** + RA path confirmed

---

## Decision log

| Date | Decision | Owner | Notes |
|------|----------|-------|-------|
| _TBD_ | go / wait / no-go | PO | P3-S8 review |
