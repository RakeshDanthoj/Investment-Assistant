"""CLI entry for signal-fired email fan-out (P2-S10)."""

from __future__ import annotations

import argparse
import logging

from app.db.connection import connection
from app.services.email_on_signal import fan_out

_LOG = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send signal-fired emails for a card/signal pair")
    parser.add_argument("--card-id", required=True)
    parser.add_argument("--signal-id", required=True)
    parser.add_argument("--card-title", default="Event card")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    with connection() as conn, conn.cursor() as cur:
        with conn.transaction():
            sent = fan_out(
                cur,
                card_id=args.card_id,
                signal_id=args.signal_id,
                card_title=args.card_title,
            )
    _LOG.info("email_on_signal.manual_complete sent=%s", sent)


if __name__ == "__main__":
    main()
