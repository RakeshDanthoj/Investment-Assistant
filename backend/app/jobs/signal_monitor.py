"""30-minute signal monitor (NSE cash hours 09:15–15:30 IST gate in runner) — P1-S11."""

from __future__ import annotations

import logging

from app.services.signal_monitor_runner import run_signal_monitor

_LOG = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = run_signal_monitor()
    if summary.skipped_market_hours:
        _LOG.info(
            "signal_monitor.exit outside NSE cash hours (Mon–Fri 09:15–15:30 IST) — "
            "cron may still fire anytime"
        )
    elif summary.skipped_no_db:
        _LOG.warning("signal_monitor.exit missing SUPABASE_DB_URL")
    else:
        _LOG.info(
            "signal_monitor.exit cards=%s checked=%s high=%s medium=%s low=%s",
            summary.cards_scanned,
            summary.signals_checked,
            summary.high_actions,
            summary.medium_actions,
            summary.low_actions,
        )


if __name__ == "__main__":
    main()
