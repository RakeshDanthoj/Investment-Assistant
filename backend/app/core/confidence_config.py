"""Rule-based confidence scorer weights and thresholds (P3-S1g / G-01, G-02)."""

from __future__ import annotations

from app.models.enums import EventCategory

SCORER_VERSION = "confidence_scorer.v1"

WEIGHTS: dict[str, float] = {
    "source_count": 0.30,
    "source_quality": 0.30,
    "factor_db_match": 0.25,
    "recency": 0.05,
    "unique_publisher": 0.10,
}

THRESHOLDS: dict[str, float] = {
    "high": 0.75,
    "medium_low": 0.55,
    "medium_high": 0.74,
}

FOG_DAMPENER = 0.6
CALIBRATION_STATUS = "provisional"

FOG_ACTIVE_MAJOR_THRESHOLD = 3

MAJOR_CATEGORIES: frozenset[EventCategory] = frozenset(
    {
        EventCategory.RBI_POLICY,
        EventCategory.GEOPOLITICAL,
        EventCategory.BUDGET,
        EventCategory.MACRO,
    }
)

IS_MAJOR_MIN_RAW = 0.75
IS_MAJOR_MIN_FACTOR_MATCHES = 2

FORCE_REVIEW_SOURCE_THRESHOLD = 5
UNIQUE_PUBLISHER_CAP = 3
SOURCE_COUNT_CAP = 3

# Indian financial source tiers (PRD2 §3.1)
SOURCE_QUALITY_BY_ADAPTER: dict[str, float] = {
    "rbi_rss": 1.0,
    "nse_bse": 1.0,
    "newsapi": 0.50,
}

SOURCE_QUALITY_BY_DOMAIN: dict[str, float] = {
    "rbi.org.in": 1.0,
    "nseindia.com": 1.0,
    "bseindia.com": 1.0,
    "indiabudget.gov.in": 1.0,
    "pib.gov.in": 0.80,
    "reuters.com": 0.80,
    "ptinews.com": 0.80,
    "economictimes.indiatimes.com": 0.65,
    "livemint.com": 0.65,
    "business-standard.com": 0.65,
    "thehindubusinessline.com": 0.65,
    "moneycontrol.com": 0.50,
    "fda.gov": 0.80,
    "opec.org": 0.65,
    "ustr.gov": 0.80,
    "mausam.imd.gov.in": 0.80,
    "ibja.co.in": 0.65,
}

DEFAULT_SOURCE_QUALITY = 0.50
