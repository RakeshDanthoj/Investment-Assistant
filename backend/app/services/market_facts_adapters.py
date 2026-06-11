"""Market-leaning fact streams for signal-monitor corroboration (P2-S14)."""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

import httpx

from app.core.settings import Settings, get_settings
from app.services.critical_facts_config import (
    CriticalFactDefinition,
    CriticalFactsConfig,
    load_critical_facts_config,
)
from app.services.signal_check import MarketFact
from app.sources.base import RawEvent, SourceAdapter, SourceFailure
from app.sources.nse_announcements import NSEAnnouncementsSourceAdapter
from app.sources.nse_index import NSEIndexSnapshotAdapter

_LOG = logging.getLogger(__name__)

FreshnessStatus = Literal["fresh", "stale", "unavailable"]

DEFAULT_MAX_FACTS_TOTAL = 300
DEFAULT_EVENTS_LIMIT = 200
DEFAULT_MARKET_STREAM_LIMIT = 120
MONITOR_NSE_PERIOD = "1D"
MONITOR_FETCH_WINDOW = timedelta(hours=6)

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
OPEN_EXCHANGE_RATES_URL = "https://openexchangerates.org/api/latest.json"
RBI_REFERENCE_RATE_URL = "https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx"
NSE_FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"
NSE_ORIGIN = "https://www.nseindia.com"

_HTTP_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-GB,en-US;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124 Safari/537.36"
    ),
}


@dataclass(frozen=True)
class QuoteObservation:
    display_value: str
    observed_at: datetime
    source: str


@dataclass(frozen=True)
class MarketQuoteFact:
    fact_id: str
    label: str
    display_value: str
    observed_at: datetime
    source: str
    freshness_status: FreshnessStatus


@dataclass(frozen=True)
class CriticalFactsGateResult:
    facts: tuple[MarketQuoteFact, ...]
    unavailable_critical: tuple[str, ...]
    has_stale_critical: bool

    @property
    def blocked(self) -> bool:
        return bool(self.unavailable_critical)


class CriticalFactsHoldError(RuntimeError):
    """Card pipeline must not proceed when a critical fact is unavailable."""

    def __init__(self, unavailable: Sequence[str]) -> None:
        ids = tuple(unavailable)
        joined = ", ".join(ids)
        super().__init__(f"critical facts unavailable: {joined}")
        self.unavailable_fact_ids = ids


def classify_freshness(
    *,
    has_value: bool,
    observed_at: datetime | None,
    reference_time: datetime,
    fresh_max_hours: float,
    stale_max_hours: float,
) -> FreshnessStatus:
    if not has_value or observed_at is None:
        return "unavailable"
    ref = _ensure_utc(reference_time)
    obs = _ensure_utc(observed_at)
    age = ref - obs
    if age <= timedelta(hours=fresh_max_hours):
        return "fresh"
    if age <= timedelta(hours=stale_max_hours):
        return "stale"
    return "stale"


def _fetch_yahoo_quote(
    symbol: str,
    *,
    client: httpx.Client | None = None,
) -> QuoteObservation | None:
    url = YAHOO_CHART_URL.format(symbol=symbol)
    owns_client = client is None
    http = client or httpx.Client(timeout=20.0, headers=_HTTP_HEADERS, follow_redirects=True)
    try:
        response = http.get(url, params={"interval": "1d", "range": "5d"})
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError, KeyError):
        return None
    finally:
        if owns_client:
            http.close()

    try:
        result = payload["chart"]["result"][0]
        timestamps = result.get("timestamp") or []
        closes = result["indicators"]["quote"][0].get("close") or []
        if not timestamps or not closes:
            return None
        for ts, close in zip(reversed(timestamps), reversed(closes), strict=False):
            if close is None:
                continue
            observed = datetime.fromtimestamp(int(ts), tz=UTC)
            return QuoteObservation(
                display_value=f"{float(close):,.2f}",
                observed_at=observed,
                source="yfinance",
            )
    except (IndexError, KeyError, TypeError, ValueError):
        return None
    return None


def _fetch_open_exchange_rates(settings: Settings) -> QuoteObservation | None:
    app_id = getattr(settings, "open_exchange_rates_app_id", "") or ""
    if not app_id.strip():
        return None
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(
                OPEN_EXCHANGE_RATES_URL,
                params={"app_id": app_id.strip(), "symbols": "INR", "base": "USD"},
            )
            response.raise_for_status()
            payload = response.json()
        rate = float(payload["rates"]["INR"])
        observed_raw = payload.get("timestamp")
        observed = (
            datetime.fromtimestamp(int(observed_raw), tz=UTC)
            if observed_raw is not None
            else datetime.now(tz=UTC)
        )
        return QuoteObservation(
            display_value=f"{rate:.2f}",
            observed_at=observed,
            source="open_exchange_rates",
        )
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        return None


def _fetch_rbi_reference_rate(*, client: httpx.Client | None = None) -> QuoteObservation | None:
    owns_client = client is None
    http = client or httpx.Client(timeout=25.0, headers=_HTTP_HEADERS, follow_redirects=True)
    try:
        response = http.get(RBI_REFERENCE_RATE_URL)
        response.raise_for_status()
        html = response.text
    except httpx.HTTPError:
        return None
    finally:
        if owns_client:
            http.close()

    match = re.search(r"USD/INR[^0-9]*([0-9]+\.[0-9]+)", html, re.IGNORECASE)
    if not match:
        return None
    return QuoteObservation(
        display_value=match.group(1),
        observed_at=datetime.now(tz=UTC),
        source="rbi_ref",
    )


def _parse_nse_fii_trade_payload(payload: object) -> QuoteObservation | None:
    """Parse NSE ``fiidiiTradeReact`` JSON (category/netValue rows or legacy fiiNet)."""
    if not isinstance(payload, list) or not payload:
        return None

    def _net_value(row: dict) -> float | None:
        raw = row.get("netValue") or row.get("fiiNet") or row.get("fii_net") or row.get("netFII")
        if raw is None:
            return None
        try:
            return float(str(raw).replace(",", ""))
        except ValueError:
            return None

    def _observed_at(row: dict) -> datetime:
        date_raw = row.get("date")
        if isinstance(date_raw, str):
            try:
                parsed = datetime.strptime(date_raw.strip(), "%d-%b-%Y")
                return parsed.replace(tzinfo=UTC)
            except ValueError:
                pass
        return datetime.now(tz=UTC)

    def _observation(row: dict, value: float) -> QuoteObservation:
        sign = "+" if value >= 0 else ""
        return QuoteObservation(
            display_value=f"{sign}{value:,.2f} Cr",
            observed_at=_observed_at(row),
            source="nse_csv",
        )

    for item in payload:
        if not isinstance(item, dict):
            continue
        category = str(item.get("category") or "").upper()
        if "FII" not in category and "FPI" not in category:
            continue
        value = _net_value(item)
        if value is not None:
            return _observation(item, value)

    first = payload[0]
    if isinstance(first, dict):
        value = _net_value(first)
        if value is not None:
            return _observation(first, value)
    return None


def _fetch_nse_fii_csv(*, client: httpx.Client | None = None) -> QuoteObservation | None:
    owns_client = client is None
    http = client or httpx.Client(timeout=25.0, headers=_HTTP_HEADERS, follow_redirects=True)
    try:
        cookies: dict[str, str] = {}
        try:
            warm = http.get(NSE_ORIGIN + "/")
            if warm.status_code < 400:
                cookies = dict(warm.cookies.items())
        except httpx.HTTPError:
            pass
        response = http.get(NSE_FII_DII_URL, cookies=cookies)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return None
    finally:
        if owns_client:
            http.close()

    return _parse_nse_fii_trade_payload(payload)


def _fetch_cdsl_portal_stub() -> QuoteObservation | None:
    """CDSL portal fallback — not automated in Phase 3; chain ends with stale/unavailable."""
    return None


def _fetch_repo_rate_from_events(reference_time: datetime) -> QuoteObservation | None:
    from app.services.market_facts import fetch_recent_event_facts

    ref = _ensure_utc(reference_time)
    events = fetch_recent_event_facts(since=ref - timedelta(days=90), reference_time=ref, limit=50)
    pattern = re.compile(r"repo\s*rate[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*%?", re.IGNORECASE)
    for fact in events:
        match = pattern.search(fact.summary)
        if match:
            return QuoteObservation(
                display_value=f"{match.group(1)}%",
                observed_at=fact.observed_at,
                source="rbi_events",
            )
    return None


def _fetch_nse_index_level(label_match: str, reference_time: datetime) -> QuoteObservation | None:
    ref = _ensure_utc(reference_time)
    try:
        rows = fetch_index_snapshot_facts(reference_time=ref)
    except SourceFailure:
        return None
    needle = label_match.lower()
    for row in rows:
        if needle not in row.summary.lower():
            continue
        level_match = re.search(r"level\s+([0-9,]+\.?[0-9]*)", row.summary, re.IGNORECASE)
        if level_match:
            return QuoteObservation(
                display_value=level_match.group(1).replace(",", ""),
                observed_at=row.observed_at,
                source="nse_index",
            )
    return None


ChainFetcher = Callable[[CriticalFactDefinition, datetime, Settings], QuoteObservation | None]

_CHAIN_FETCHERS: dict[str, ChainFetcher] = {}


def _register_chain(fn: ChainFetcher) -> ChainFetcher:
    step_name = fn.__name__.removeprefix("_chain_")
    _CHAIN_FETCHERS[step_name] = fn
    return fn


@_register_chain
def _chain_yfinance(
    defn: CriticalFactDefinition,
    ref: datetime,
    _settings: Settings,
) -> QuoteObservation | None:
    del ref
    symbol = defn.yfinance_symbol
    if not symbol:
        return None
    return _fetch_yahoo_quote(symbol)


@_register_chain
def _chain_open_exchange_rates(
    _defn: CriticalFactDefinition, _ref: datetime, settings: Settings
) -> QuoteObservation | None:
    return _fetch_open_exchange_rates(settings)


@_register_chain
def _chain_rbi_ref(
    _defn: CriticalFactDefinition,
    _ref: datetime,
    _settings: Settings,
) -> QuoteObservation | None:
    return _fetch_rbi_reference_rate()


@_register_chain
def _chain_rbi_events(
    defn: CriticalFactDefinition,
    ref: datetime,
    _settings: Settings,
) -> QuoteObservation | None:
    del defn
    return _fetch_repo_rate_from_events(ref)


@_register_chain
def _chain_config_fallback(
    defn: CriticalFactDefinition,
    ref: datetime,
    _settings: Settings,
) -> QuoteObservation | None:
    if not defn.config_fallback_value:
        return None
    hours_ago = defn.config_fallback_observed_hours_ago or 720.0
    return QuoteObservation(
        display_value=defn.config_fallback_value,
        observed_at=ref - timedelta(hours=hours_ago),
        source="config_fallback",
    )


@_register_chain
def _chain_nse_index(
    defn: CriticalFactDefinition,
    ref: datetime,
    _settings: Settings,
) -> QuoteObservation | None:
    if defn.fact_id == "nifty_50":
        return _fetch_nse_index_level("nifty 50", ref)
    if defn.fact_id == "india_vix":
        return _fetch_nse_index_level("india vix", ref)
    return None


@_register_chain
def _chain_nse_fii_csv(
    _defn: CriticalFactDefinition,
    _ref: datetime,
    _settings: Settings,
) -> QuoteObservation | None:
    return _fetch_nse_fii_csv()


@_register_chain
def _chain_cdsl_portal(
    _defn: CriticalFactDefinition,
    _ref: datetime,
    _settings: Settings,
) -> QuoteObservation | None:
    return _fetch_cdsl_portal_stub()


def resolve_quote_fact(
    defn: CriticalFactDefinition,
    *,
    reference_time: datetime,
    settings: Settings | None = None,
    config: CriticalFactsConfig | None = None,
    chain_fetchers: dict[str, ChainFetcher] | None = None,
) -> MarketQuoteFact:
    cfg = config or load_critical_facts_config()
    cfg_settings = settings or get_settings()
    ref = _ensure_utc(reference_time)
    fetchers = chain_fetchers or _CHAIN_FETCHERS

    observation: QuoteObservation | None = None
    for step in defn.chain:
        fetcher = fetchers.get(step)
        if fetcher is None:
            _LOG.warning(
                "market_facts.unknown_chain_step",
                extra={"step": step, "fact_id": defn.fact_id},
            )
            continue
        try:
            observation = fetcher(defn, ref, cfg_settings)
        except Exception as exc:  # noqa: BLE001 — fallback chain continues
            _LOG.warning(
                "market_facts.chain_step_error",
                extra={"step": step, "fact_id": defn.fact_id, "error": str(exc)},
            )
            observation = None
        if observation is not None:
            break

    freshness = classify_freshness(
        has_value=observation is not None,
        observed_at=observation.observed_at if observation else None,
        reference_time=ref,
        fresh_max_hours=cfg.staleness.fresh_max_hours,
        stale_max_hours=cfg.staleness.stale_max_hours,
    )
    if observation is None:
        return MarketQuoteFact(
            fact_id=defn.fact_id,
            label=defn.label,
            display_value="—",
            observed_at=ref,
            source="none",
            freshness_status="unavailable",
        )
    return MarketQuoteFact(
        fact_id=defn.fact_id,
        label=defn.label,
        display_value=observation.display_value,
        observed_at=observation.observed_at,
        source=observation.source,
        freshness_status=freshness,
    )


def build_quoted_market_facts(
    *,
    reference_time: datetime | None = None,
    settings: Settings | None = None,
    config: CriticalFactsConfig | None = None,
    chain_fetchers: dict[str, ChainFetcher] | None = None,
) -> list[MarketQuoteFact]:
    cfg = config or load_critical_facts_config()
    ref = _ensure_utc(reference_time)
    return [
        resolve_quote_fact(
            defn,
            reference_time=ref,
            settings=settings,
            config=cfg,
            chain_fetchers=chain_fetchers,
        )
        for defn in cfg.facts
    ]


def evaluate_critical_facts_gate(
    *,
    reference_time: datetime | None = None,
    settings: Settings | None = None,
    config: CriticalFactsConfig | None = None,
    chain_fetchers: dict[str, ChainFetcher] | None = None,
) -> CriticalFactsGateResult:
    cfg = config or load_critical_facts_config()
    facts = tuple(
        build_quoted_market_facts(
            reference_time=reference_time,
            settings=settings,
            config=cfg,
            chain_fetchers=chain_fetchers,
        )
    )
    critical_ids = set(cfg.critical_fact_ids)
    unavailable = tuple(
        f.fact_id
        for f in facts
        if f.fact_id in critical_ids and f.freshness_status == "unavailable"
    )
    has_stale = any(
        f.fact_id in critical_ids and f.freshness_status == "stale" for f in facts
    )
    return CriticalFactsGateResult(
        facts=facts,
        unavailable_critical=unavailable,
        has_stale_critical=has_stale,
    )


def assert_critical_facts_available(
    *,
    reference_time: datetime | None = None,
    settings: Settings | None = None,
    config: CriticalFactsConfig | None = None,
    chain_fetchers: dict[str, ChainFetcher] | None = None,
) -> CriticalFactsGateResult:
    gate = evaluate_critical_facts_gate(
        reference_time=reference_time,
        settings=settings,
        config=config,
        chain_fetchers=chain_fetchers,
    )
    if gate.blocked:
        raise CriticalFactsHoldError(gate.unavailable_critical)
    return gate


def quote_facts_to_macro_lines(facts: Sequence[MarketQuoteFact]) -> str:
    lines = ["### Live market fact chips (merged stream)"]
    for fact in facts:
        if fact.freshness_status == "unavailable":
            lines.append(f"- {fact.label}: unavailable ({fact.freshness_status})")
            continue
        lines.append(
            f"- {fact.label}: {fact.display_value} [{fact.freshness_status}] "
            f"source={fact.source} observed={fact.observed_at.isoformat()}"
        )
    return "\n".join(lines)

DEFAULT_MAX_FACTS_TOTAL = 300
DEFAULT_EVENTS_LIMIT = 200
DEFAULT_MARKET_STREAM_LIMIT = 120
MONITOR_NSE_PERIOD = "1D"
MONITOR_FETCH_WINDOW = timedelta(hours=6)


def merge_market_facts(
    *streams: Sequence[MarketFact],
    max_total: int = DEFAULT_MAX_FACTS_TOTAL,
) -> list[MarketFact]:
    """
    Merge fact streams: dedupe by ``source_id`` (keep newest ``observed_at``),
    order newest-first, cap list size.
    """
    by_id: dict[str, MarketFact] = {}
    for stream in streams:
        for fact in stream:
            existing = by_id.get(fact.source_id)
            if existing is None or fact.observed_at > existing.observed_at:
                by_id[fact.source_id] = fact

    merged = sorted(by_id.values(), key=lambda f: f.observed_at, reverse=True)
    if len(merged) > max_total:
        merged = merged[:max_total]
    return merged


def _raw_to_market_fact(
    raw: RawEvent,
    *,
    source_prefix: str,
    reference_time: datetime,
) -> MarketFact | None:
    title = (raw.title or "").strip()
    if not title:
        return None
    digest = hashlib.sha256(raw.canonical_url.encode("utf-8")).hexdigest()[:16]
    source_id = f"{source_prefix}:{digest}"
    observed = raw.published_at or reference_time
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=UTC)
    return MarketFact(source_id=source_id, summary=title, observed_at=observed)


def _adapter_facts(
    adapter: SourceAdapter,
    *,
    source_prefix: str,
    reference_time: datetime,
    window: timedelta,
    period: str | None = None,
    limit: int = DEFAULT_MARKET_STREAM_LIMIT,
) -> list[MarketFact]:
    try:
        if period is not None and isinstance(adapter, NSEAnnouncementsSourceAdapter):
            raw_rows = adapter.fetch(window, period=period)
        else:
            raw_rows = adapter.fetch(window)
    except SourceFailure as exc:
        raise exc

    facts: list[MarketFact] = []
    for raw in raw_rows:
        fact = _raw_to_market_fact(raw, source_prefix=source_prefix, reference_time=reference_time)
        if fact is not None:
            facts.append(fact)
    facts.sort(key=lambda f: f.observed_at, reverse=True)
    return facts[:limit]


def fetch_nse_announcement_facts(
    *,
    reference_time: datetime | None = None,
    window: timedelta | None = None,
    limit: int = DEFAULT_MARKET_STREAM_LIMIT,
) -> list[MarketFact]:
    ref = _ensure_utc(reference_time)
    window_eff = window or MONITOR_FETCH_WINDOW
    adapter = NSEAnnouncementsSourceAdapter()
    return _adapter_facts(
        adapter,
        source_prefix="nse",
        reference_time=ref,
        window=window_eff,
        period=MONITOR_NSE_PERIOD,
        limit=limit,
    )


def fetch_index_snapshot_facts(
    *,
    reference_time: datetime | None = None,
    window: timedelta | None = None,
    limit: int = 10,
) -> list[MarketFact]:
    ref = _ensure_utc(reference_time)
    window_eff = window or MONITOR_FETCH_WINDOW
    adapter = NSEIndexSnapshotAdapter()
    return _adapter_facts(
        adapter,
        source_prefix="nse-index",
        reference_time=ref,
        window=window_eff,
        limit=limit,
    )


def _ensure_utc(reference_time: datetime | None) -> datetime:
    ref = reference_time or datetime.now(tz=UTC)
    if ref.tzinfo is None:
        return ref.replace(tzinfo=UTC)
    return ref


def collect_market_stream_facts(
    settings: Settings,
    *,
    reference_time: datetime,
    events_facts: Sequence[MarketFact],
) -> list[Sequence[MarketFact]]:
    """Return enabled non-event streams for merge (events passed separately)."""
    streams: list[Sequence[MarketFact]] = [events_facts]
    ref = _ensure_utc(reference_time)

    if settings.signal_facts_nse_enabled:
        try:
            nse = fetch_nse_announcement_facts(reference_time=ref)
            if not nse:
                _LOG.warning(
                    "market_facts.stream_empty",
                    extra={"stream": "nse_announcements", "required": False},
                )
            else:
                _LOG.info(
                    "market_facts.stream_ok",
                    extra={"stream": "nse_announcements", "count": len(nse)},
                )
            streams.append(nse)
        except SourceFailure as exc:
            _LOG.warning(
                "market_facts.stream_error",
                extra={"stream": "nse_announcements", "error": str(exc), "required": False},
            )
    else:
        _LOG.info("market_facts.stream_disabled", extra={"stream": "nse_announcements"})

    if settings.signal_facts_index_enabled:
        try:
            index_rows = fetch_index_snapshot_facts(reference_time=ref)
            if not index_rows:
                _LOG.warning(
                    "market_facts.stream_empty",
                    extra={"stream": "nse_index", "required": False},
                )
            else:
                _LOG.info(
                    "market_facts.stream_ok",
                    extra={"stream": "nse_index", "count": len(index_rows)},
                )
            streams.append(index_rows)
        except SourceFailure as exc:
            _LOG.warning(
                "market_facts.stream_error",
                extra={"stream": "nse_index", "error": str(exc), "required": False},
            )
    else:
        _LOG.info("market_facts.stream_disabled", extra={"stream": "nse_index"})

    return streams


__all__ = [
    "DEFAULT_EVENTS_LIMIT",
    "DEFAULT_MAX_FACTS_TOTAL",
    "CriticalFactsGateResult",
    "CriticalFactsHoldError",
    "FreshnessStatus",
    "MarketQuoteFact",
    "assert_critical_facts_available",
    "build_quoted_market_facts",
    "classify_freshness",
    "collect_market_stream_facts",
    "evaluate_critical_facts_gate",
    "fetch_index_snapshot_facts",
    "fetch_nse_announcement_facts",
    "merge_market_facts",
    "quote_facts_to_macro_lines",
    "resolve_quote_fact",
]
