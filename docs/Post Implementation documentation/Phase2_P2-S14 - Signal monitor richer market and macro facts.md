# Post Implementation Detailed Document — P2-S14

**Version:** v1.0 | **Date:** 24-05-2026  
**Story ID:** P2-S14 (Phase 2, Story 14)  
**Reference plan:** `docs/plans/finnwise-phase2-implementation-tasks.md`

---

## Summary

The scheduled signal monitor now corroborates card signals against a **merged fact feed**: recent **`events`** rows (macro/editorial proxy) plus **market-leaning** lines from **NSE corporate announcements** (`period=1D` for monitor) and optional **Nifty 50 / Sensex** index snapshots. Stream failures are logged; optional streams do not abort the run.

**Tests (story close-out):**

| Suite | Command | Result |
|-------|---------|--------|
| Merge + build | `python -m pytest tests/test_market_facts_merge.py -q` | **5 passed** |
| NSE/index contract | `python -m pytest tests/test_nse_facts_adapter_contract.py -q` | **4 passed** |
| Regression | `python -m pytest tests/test_signal_check.py tests/test_source_adapters.py -q` | **6 passed** |

---

## Operational playbook

| Stream | Env toggle | Required? | On failure |
|--------|------------|-----------|------------|
| `events` (DB) | `SIGNAL_FACTS_EVENTS_ENABLED` (default `true`) | **Yes** when enabled — monitor needs DB | `RuntimeError` propagates (no DB URL / query failure) |
| NSE announcements | `SIGNAL_FACTS_NSE_ENABLED` (default `true`) | No | `SourceFailure` logged; merge continues |
| NSE index snapshot | `SIGNAL_FACTS_INDEX_ENABLED` (default `true`) | No | `SourceFailure` logged; merge continues |

**Cap:** `SIGNAL_FACTS_MAX_TOTAL` (default `300`) after dedupe-by-`source_id` (newest `observed_at` wins), newest-first ordering.

**Cron vs market hours:** Render cron remains `*/30 * * * *` UTC; `run_signal_monitor` still self-gates to NSE cash session (Mon–Fri 09:15–15:30 IST). Outside session = cheap no-op. **Market holidays** behave like weekends for the IST gate (no card scans).

**Rate limits / brittle sources:** NSE may block scripted access; disable `SIGNAL_FACTS_NSE_ENABLED` or `SIGNAL_FACTS_INDEX_ENABLED` without deploy if needed. Event ingest (P1-S6) remains the fallback macro proxy.

**Key files:** `backend/app/services/market_facts.py` (`build_market_facts`), `market_facts_adapters.py`, `signal_monitor_runner.py` (default `facts_provider`), `app/sources/nse_announcements.py`, `nse_index.py`, `nse_datetime.py`.
