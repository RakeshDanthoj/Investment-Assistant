"""Thread detail payload: ICE layers, aside widgets, evidence freshness (P1-S10)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.services.bias_detector import build_bias_audit
from app.services.card_repository import (
    fetch_card_detail_bundle,
    fetch_card_detail_for_review,
    fetch_track_record_initial_publish,
)
from app.services.factor_db import freshness_for_retrieved_at
from app.services.feed import confidence_tier, tier_label

_MMJ_BRACKET = re.compile(r"\[(MEASURED|MODELLED|JUDGED)]", re.IGNORECASE)
_STEP_SPLIT = re.compile(r"\n(?=\s*\d+[\).\]\-\s])")


def _normalize_evidence_layer(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    return {}


def _parse_iso_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def mmj_composition_from_text(*chunks: str) -> dict[str, Any]:
    blob = "\n".join(c for c in chunks if c)
    measured = len(re.findall(r"\[MEASURED\]", blob, flags=re.IGNORECASE))
    modelled = len(re.findall(r"\[MODELLED\]", blob, flags=re.IGNORECASE))
    judged = len(re.findall(r"\[JUDGED\]", blob, flags=re.IGNORECASE))
    total = measured + modelled + judged
    if total == 0:
        measured, modelled, judged = 1, 1, 1
        total = 3
    return {
        "measured": measured / total,
        "modelled": modelled / total,
        "judged": judged / total,
        "counts": {"measured": measured, "modelled": modelled, "judged": judged},
    }


def parse_context_steps(context_layer: str) -> list[dict[str, Any]]:
    text = context_layer.strip()
    if not text:
        return []
    parts = _STEP_SPLIT.split(text)
    if len(parts) <= 1 and not re.match(r"^\s*\d+", text):
        parts = [text]
    steps: list[dict[str, Any]] = []
    for raw in parts:
        block = raw.strip()
        if not block:
            continue
        mm = _MMJ_BRACKET.search(block)
        mmj = mm.group(1).upper() if mm else None
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        title = lines[0][:240] if lines else ""
        body_lines = lines[1:] if len(lines) > 1 else []
        body = "\n".join(body_lines).strip()
        steps.append({"title": title, "body": body, "mmj": mmj})
    return steps


def normalize_signal_label(raw: str | None) -> str:
    x = (raw or "watch").strip().lower()
    if x in {"positive", "opportunity", "opportunity_signal"}:
        return "opportunity signal"
    if x in {"negative", "headwind", "headwind_signal"}:
        return "headwind signal"
    return "watch"


def _should_skip_source_name(name: str) -> bool:
    low = name.lower()
    return "llm" in low or "gemini" in low or "gpt" in low


def build_evidence_rows(
    evidence_layer: dict[str, Any],
    *,
    ref: datetime | None = None,
) -> list[dict[str, Any]]:
    reference = ref or datetime.now(tz=UTC)
    rows: list[dict[str, Any]] = []

    sources = evidence_layer.get("sources")
    if isinstance(sources, list):
        for item in sources:
            if not isinstance(item, dict):
                continue
            claim = str(item.get("claim") or item.get("title") or "").strip()
            src = str(item.get("source_name") or item.get("source") or "").strip()
            if not claim or not src or _should_skip_source_name(src):
                continue
            retrieved = _parse_iso_dt(item.get("retrieved_at") or item.get("date_retrieved"))
            date_label = str(item.get("date_label") or "")
            if retrieved:
                date_label = retrieved.date().isoformat()
            mmj_raw = str(item.get("mmj_type") or item.get("mmj") or "MEASURED")
            mmj = mmj_raw.upper().split()[0] if mmj_raw else "MEASURED"
            freshness = (
                freshness_for_retrieved_at(retrieved, reference=reference)
                if retrieved
                else "amber"
            )
            rows.append(
                {
                    "claim": claim,
                    "source_name": src,
                    "date_label": date_label or "—",
                    "retrieved_at": retrieved.isoformat() if retrieved else None,
                    "freshness": freshness,
                    "mmj": mmj if mmj in {"MEASURED", "MODELLED", "JUDGED"} else "MEASURED",
                }
            )

    if rows:
        return rows

    ms = evidence_layer.get("matrix_snapshot") or {}
    sens = ms.get("sensitivities") or {}
    if isinstance(sens, dict):
        for ticker, factors in sens.items():
            if not isinstance(factors, dict):
                continue
            for fslug, cell in factors.items():
                if not isinstance(cell, dict):
                    continue
                retrieved = _parse_iso_dt(cell.get("retrieved_at"))
                src_url = str(cell.get("source_url") or "")
                src_name = src_url[:120] if src_url else "Factor exposure database"
                claim = f"{ticker} exposure — {fslug.replace('_', ' ')}"
                mmj_tag = str(cell.get("mmj_tag") or "MEASURED").upper()
                freshness = (
                    freshness_for_retrieved_at(retrieved, reference=reference)
                    if retrieved
                    else "amber"
                )
                rows.append(
                    {
                        "claim": claim,
                        "source_name": src_name,
                        "date_label": retrieved.date().isoformat() if retrieved else "—",
                        "retrieved_at": retrieved.isoformat() if retrieved else None,
                        "freshness": freshness,
                        "mmj": mmj_tag
                        if mmj_tag in {"MEASURED", "MODELLED", "JUDGED"}
                        else "MEASURED",
                    }
                )
    return rows


def bias_audit_placeholder() -> dict[str, Any]:
    return {
        "flags": [],
        "monitored": [
            {
                "id": "recency",
                "label": "Recency bias",
                "status": "monitored",
                "detail": (
                    "Watching whether near-term headlines overweight "
                    "versus slower fundamentals."
                ),
            },
            {
                "id": "narrative",
                "label": "Narrative anchoring",
                "status": "monitored",
                "detail": "Watching whether a single storyline crowds out alternative mechanisms.",
            },
        ],
        "note": "Editorial bias audit fills this panel when available (P1-S13).",
    }


def lifecycle_tracker_states(current_state: str) -> list[dict[str, Any]]:
    order = [
        "published",
        "active",
        "signal_triggered",
        "thesis_confirmed",
        "thesis_weakened",
        "resolved",
        "archived",
    ]
    cur = current_state.strip().lower()
    try:
        idx = order.index(cur)
    except ValueError:
        idx = 0
    out: list[dict[str, Any]] = []
    for i, slug in enumerate(order):
        label = slug.replace("_", " ").title()
        if i < idx:
            status = "done"
        elif i == idx:
            status = "current"
        else:
            status = "future"
        out.append({"slug": slug, "label": label, "status": status})
    return out


def week_number_hint(card_created_at: Any) -> int | None:
    dt = _parse_iso_dt(card_created_at)
    if dt is None:
        return None
    delta = datetime.now(tz=UTC) - dt
    weeks = max(1, min(4, delta.days // 7 + 1))
    return weeks


def build_card_detail(card_id: UUID, *, view: str) -> dict[str, Any] | None:
    track: dict[str, Any] | None = None
    bias_audit: dict[str, Any] | None = None
    bias_rows: list[dict[str, Any]] | None = None

    if view == "original":
        detail = fetch_card_detail_for_review(card_id)
        if detail is None:
            return None
        track = fetch_track_record_initial_publish(card_id)
        if track is None:
            return None
        stored = track.get("bias_audit")
        if isinstance(stored, dict):
            bias_audit = stored
        ice = track.get("ice_snapshot") or {}
        if not isinstance(ice, dict):
            ice = {}
        signals_raw = track.get("signals_snapshot") or []
        instruments_raw = ice.get("instruments") or []
        title = str(ice.get("title") or "")
        insight_layer = str(ice.get("insight_layer") or "")
        context_layer = str(ice.get("context_layer") or "")
        evidence_layer = _normalize_evidence_layer(ice.get("evidence_layer"))
        dissenting_view = str(ice.get("dissenting_view") or "")
        framework_behind_this = str(ice.get("framework_behind_this") or "")
        event_title = str(ice.get("event_title") or "")
        event_score = ice.get("event_confidence_score")
        lifecycle_for_tracker = str(ice.get("lifecycle_state") or "published")
    else:
        bundle = fetch_card_detail_bundle(card_id)
        if bundle is None:
            return None
        detail = bundle.detail
        bias_rows = bundle.bias_flags
        ice = {}
        signals_raw = bundle.signals
        instruments_raw = bundle.instruments
        title = str(detail["title"])
        insight_layer = str(detail["insight_layer"])
        context_layer = str(detail["context_layer"])
        evidence_layer = _normalize_evidence_layer(detail["evidence_layer"])
        dissenting_view = str(detail["dissenting_view"])
        framework_behind_this = str(detail["framework_behind_this"])
        event_title = str(detail["event_title"])
        event_score = detail.get("event_confidence_score")
        lifecycle_for_tracker = str(detail["lifecycle_state"])

    instruments_out: list[dict[str, Any]] = []
    for row in instruments_raw:
        if not isinstance(row, dict):
            continue
        instruments_out.append(
            {
                "instrument_id": str(row.get("instrument_id") or "").upper(),
                "signal_label": normalize_signal_label(str(row.get("signal_type"))),
                "reasoning": row.get("reasoning"),
                "entry_conditions": list(row.get("entry_conditions") or []),
                "exit_conditions": list(row.get("exit_conditions") or []),
            }
        )

    signals_out: list[dict[str, Any]] = []
    for row in signals_raw:
        if isinstance(row, dict):
            signals_out.append(
                {
                    "signal_text": str(row.get("signal_text") or ""),
                    "state": str(row.get("state") or "pending"),
                }
            )

    score_i = int(event_score) if event_score is not None else None
    direction_tier = confidence_tier(score_i)
    mag_score = None if score_i is None else max(0, min(100, score_i - 12))
    magnitude_tier = confidence_tier(mag_score)

    evidence_rows = build_evidence_rows(evidence_layer)
    md = str(evidence_layer.get("markdown") or "")
    macro_stub = str(evidence_layer.get("macro_stub") or "")
    comp = mmj_composition_from_text(insight_layer, context_layer, md, dissenting_view)

    return {
        "view": view,
        "card_id": str(card_id),
        "event_id": str(detail["event_id"]),
        "title": title,
        "event_title": event_title,
        "category": str(detail["event_category"]),
        "lifecycle_state": lifecycle_for_tracker,
        "lifecycle_tracker": lifecycle_tracker_states(lifecycle_for_tracker),
        "week_number": week_number_hint(detail.get("card_created_at")),
        "direction_confidence": {"tier": direction_tier, "label": tier_label(direction_tier)},
        "magnitude_confidence": {"tier": magnitude_tier, "label": tier_label(magnitude_tier)},
        "event_confidence_score": score_i,
        "insight_layer": insight_layer,
        "context_layer": context_layer,
        "context_steps": parse_context_steps(context_layer),
        "evidence_layer": evidence_layer,
        "evidence_rows": evidence_rows,
        "evidence_markdown": md,
        "evidence_macro_stub": macro_stub,
        "dissenting_view": dissenting_view,
        "framework_behind_this": framework_behind_this,
        "instruments": instruments_out,
        "signals": signals_out,
        "confidence_composition": comp,
        "bias_audit": (
            bias_audit
            if bias_audit is not None
            else build_bias_audit(card_id=card_id, bias_rows=bias_rows)
        ),
        "published_at": detail.get("card_created_at"),
    }


__all__ = [
    "bias_audit_placeholder",
    "build_card_detail",
    "build_evidence_rows",
    "lifecycle_tracker_states",
    "mmj_composition_from_text",
    "normalize_signal_label",
    "parse_context_steps",
]
