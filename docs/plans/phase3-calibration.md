# Phase 3 — Confidence calibration ritual

**Status:** `calibration_status: provisional` (see `backend/app/core/confidence_config.py`)  
**Gaps:** G-01 (scorer weights), G-02 (gate thresholds), G-11 (override log → recalibration)  
**Parent plan:** `docs/plans/finnwise-phase3-implementation-tasks.md` (P3-S1g, P3-T3, P3-S1m)

---

## Purpose

Confidence scores and gate tiers are **bootstrap estimates** until live editor overrides and signal false-positive data exist. This document defines **when** and **how** to review them — not auto-tuning in production.

---

## Week 2 (build gate — P3-S1g / P3-T3)

| Step | Action |
|------|--------|
| 1 | Run `python -m pytest backend/tests/test_confidence_scorer.py -q` — includes `test_synthetic_calibration_at_least_eighty_percent_match` (≥80% tier match on 20 synthetic fixtures). |
| 2 | If match &lt; 80%, tune `WEIGHTS` / `THRESHOLDS` in `confidence_config.py` only — do not change gate routing in `signal_monitor_runner.py` separately. |
| 3 | Keep `CALIBRATION_STATUS = "provisional"` until Day 60 review passes. |
| 4 | CI must stay green: `ruff check backend`, full `pytest backend/tests`, frontend lint/typecheck/test/build when UI touched. |

**P3-T3 gate (before P3-S1i):** `test_confidence_scoring_gate.py` + breakdown API shape + `ConfidenceComposition` RTL fixture.

---

## Day 30 — First live review

**Trigger:** Calendar Day 30 after synthetic seed (P3-S0) **or** first production deploy with rule-based scorer — whichever is later.

| Step | Action |
|------|--------|
| 1 | Export `confidence_gate_log` + `signal_override_log` (P3-S1m when live) for the prior 30 days. |
| 2 | Compute **override rate** = overrides ÷ high-confidence auto-actions (target ≤ 10%). |
| 3 | Compute **false-positive rate** for auto-signals (dismissed / wrong outcome ÷ total auto-fired) when P3-S1m data exists. |
| 4 | Compare breakdown API samples vs stored `confidence_raw` / `confidence_effective` on 5–10 random events (spot-check reproducibility via `confidence_score_audit`). |
| 5 | If override rate **≥ 10%** or FP rate **≥ 10%**, open a GitHub issue tagged `calibration-review` — **do not** auto-merge threshold changes. |
| 6 | Document decisions in `docs/notes/signal-override-log-YYYY-MM.md` (monthly note pattern). |

**Do not** start P3-S2 interaction model soak until synthetic history + this review are complete (see parent plan Week 4).

---

## Day 60 — Threshold validation

| Step | Action |
|------|--------|
| 1 | Repeat Day 30 metrics on a 60-day window. |
| 2 | If override rate ≤ 10% **and** FP rate ≤ 10% for two consecutive monthly windows, set `CALIBRATION_STATUS = "validated"` in `confidence_config.py` (deploy required). |
| 3 | If not, adjust `THRESHOLDS` in `confidence_config.py` with written rationale in the monthly note; keep `provisional` until the next 60-day window passes. |

---

## Monthly thereafter

| Condition | Action |
|-----------|--------|
| FP rate &gt; 10% (rolling 30 days) | Open `calibration-review` issue; review `WEIGHTS`, `THRESHOLDS`, and FoW `FOG_DAMPENER` |
| Override rate &gt; 10% | Same — distinguish editor fatigue vs scorer drift using override reason codes |
| Stable metrics | No change; log "no action" in monthly note |

---

## Files to touch during recalibration

| File | What may change |
|------|-----------------|
| `backend/app/core/confidence_config.py` | `WEIGHTS`, `THRESHOLDS`, `CALIBRATION_STATUS`, `FOG_DAMPENER` |
| `backend/tests/test_confidence_scorer.py` | Calibration fixture expectations if thresholds shift materially |
| `docs/plans/phase3-calibration.md` | This ritual (version note in commit message) |

**Do not** change gate tier strings (`high` / `medium` / `low`) or `confidence_gate.route()` semantics without updating P3-T3 tests and signal monitor integration tests.

---

## Related CI tests

| Module | Proves |
|--------|--------|
| `test_confidence_scorer.py` | Weights, FoW math, synthetic ≥80% tier match |
| `test_confidence_scoring_gate.py` | Breakdown sum = raw; FoW effective/tier; signal monitor uses `confidence_effective` |
| `test_confidence_breakdown_api.py` | HTTP contract + 404 |
| `ConfidenceComposition.test.tsx` | Five inputs visible after expand |
| `test_editorial_integrity_e2e.py` | Publish blocked until validator + checklist; regen cannot bypass publish gate |
| `ChecklistPanel.test.tsx` | Publish button disabled until auto checks + plain English |

---

_Last updated: P3-T4 (May 2026)_
