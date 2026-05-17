"""Cron placeholder for FinnWise bias report job (planned follow-up slice)."""

from __future__ import annotations

import logging

_LOG = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    _LOG.info("weekly_bias_report placeholder")


if __name__ == "__main__":
    main()
