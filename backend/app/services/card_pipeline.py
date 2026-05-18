"""Three-call ICE draft pipeline: synthesis → dissent → framework (P1-S7)."""

from __future__ import annotations

import json
from typing import Any, Protocol
from uuid import UUID

from app.services.card_repository import fetch_event_row, insert_draft_card_bundle
from app.services.cost_guard import consume_slot_or_raise, estimate_cost_usd, merge_usage
from app.services.factor_db import fetch_matrix_rows
from app.services.llm_client import LlmClient, load_prompt_markdown, render_prompt
from app.services.mmj_validator import validate_mmj_tags
from app.services.number_validator import validate_numbers_in_evidence

PROMPT_SYNTHESIS_VERSION = "synthesis.v1"
PROMPT_DISSENT_VERSION = "dissent.v1"
PROMPT_FRAMEWORK_VERSION = "framework.v1"

COMBINED_PROMPT_VERSION = (
    f"{PROMPT_SYNTHESIS_VERSION}|{PROMPT_DISSENT_VERSION}|{PROMPT_FRAMEWORK_VERSION}"
)


class SupportsCompletion(Protocol):
    def complete_json(
        self,
        *,
        system: str,
        user: str,
        prompt_version: str,
        max_tokens: int = 4096,
    ) -> tuple[dict[str, Any], dict[str, int]]: ...


class DissentQualityError(ValueError):
    """Dissent failed structural specificity checks."""


class FrameworkQualityError(ValueError):
    """Framework output missing a named transferable pattern."""


_GENERIC_DISSENT_MARKERS = frozenset(
    {
        "it remains to be seen",
        "only time will tell",
        "time will tell",
        "markets are unpredictable",
        "could go either way",
        "it is unclear how this will play out",
        "uncertainty remains high",
    }
)


def _evidence_corpus(evidence_layer: dict[str, Any]) -> str:
    parts = [
        str(evidence_layer.get("markdown") or ""),
        str(evidence_layer.get("macro_stub") or ""),
        json.dumps(evidence_layer.get("matrix_snapshot") or {}, sort_keys=True),
        json.dumps(evidence_layer.get("event_snapshot") or {}, sort_keys=True),
    ]
    return "\n\n".join(parts).replace(",", "").lower()


def _build_evidence_layer(event_row: dict[str, Any]) -> dict[str, Any]:
    matrix = fetch_matrix_rows(sector_slug="banking")
    lines: list[str] = [
        "### Banking sector factor sensitivities (Factor DB)",
        "Each line: `TICKER | factor_slug | sensitivity −5…+5 | MMJ | source`",
    ]
    sensitivities = matrix.get("sensitivities") or {}
    for ticker in sorted(sensitivities.keys()):
        for factor_slug, cell in sorted(sensitivities[ticker].items()):
            lines.append(
                f"{ticker} | {factor_slug} | sensitivity={cell.get('sensitivity')} "
                f"| mmj={cell.get('mmj_tag')} | source={cell.get('source_url')}"
            )
    macro_stub = (
        "Macro signals feed: **not wired in Phase 1**. Do not cite levels for crude, "
        "INR/USD, VIX, index prints, or policy rates unless they appear explicitly in "
        "the event title/metadata or Factor DB lines above."
    )
    event_snapshot = {
        "title": event_row.get("title"),
        "category": event_row.get("category"),
        "confidence_score": event_row.get("confidence_score"),
        "canonical_url": event_row.get("canonical_url"),
        "event_source": event_row.get("event_source"),
    }
    md = "\n".join(lines)
    return {
        "markdown": md,
        "macro_stub": macro_stub,
        "matrix_snapshot": matrix,
        "event_snapshot": event_snapshot,
    }


def _validate_dissent(text: str) -> None:
    stripped = text.strip()
    if len(stripped) < 160:
        raise DissentQualityError("dissenting_view too short to be specific")
    low = stripped.lower()
    if sum(1 for g in _GENERIC_DISSENT_MARKERS if g in low) >= 2:
        raise DissentQualityError("dissenting_view reads as generic disclaimer")


def _validate_framework(pattern_name: str, framework_text: str) -> None:
    if len(pattern_name.strip()) < 6:
        raise FrameworkQualityError("pattern_name missing or too short")
    if len(framework_text.strip()) < 120:
        raise FrameworkQualityError("framework_behind_this too short")


def _coerce_assessments(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw[:8]:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "instrument_id": str(item.get("instrument_id", "")),
                "signal_type": str(item.get("signal_type", "watch")),
                "reasoning": str(item.get("reasoning", "")),
                "entry_conditions": list(item.get("entry_conditions") or []),
                "exit_conditions": list(item.get("exit_conditions") or []),
            }
        )
    return out


def _coerce_signals(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw[:5]:
        if isinstance(item, dict) and item.get("signal_text"):
            out.append({"signal_text": str(item["signal_text"])})
    return out


def _validate_layers(
    *,
    corpus: str,
    insight: str,
    context: str,
    assessments: list[dict[str, Any]],
) -> None:
    for prose in (insight, context):
        validate_mmj_tags(prose=prose)
        validate_numbers_in_evidence(prose=prose, evidence_corpus=corpus)

    for asm in assessments:
        reasoning = str(asm.get("reasoning") or "")
        joined_conds = " ".join(
            list(asm.get("entry_conditions") or []) + list(asm.get("exit_conditions") or [])
        )
        for chunk in (reasoning, joined_conds):
            if chunk.strip():
                validate_mmj_tags(prose=chunk)
                validate_numbers_in_evidence(prose=chunk, evidence_corpus=corpus)


def draft_card_from_event(
    event_id: UUID,
    *,
    editor_notes: str | None = None,
    llm: SupportsCompletion | None = None,
) -> UUID:
    """
    Runs synthesis → validators → dissent → framework → persist.
    Consumes one daily LLM slot (UTC) immediately before the first model call.
    """
    row = fetch_event_row(event_id)
    if row is None:
        raise LookupError(f"event not found: {event_id}")

    evidence_layer = _build_evidence_layer(row)
    model = llm or LlmClient()
    usage_acc: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}

    consume_slot_or_raise()
    evidence_md = str(evidence_layer.get("markdown") or "")
    evidence_block = f"{evidence_md}\n\n{evidence_layer.get('macro_stub') or ''}\n"
    corpus = _evidence_corpus(evidence_layer)

    syn_t = load_prompt_markdown("synthesis.v1.md")
    notes_block = (
        f"\n## Editor notes\n{editor_notes.strip()}\n"
        if editor_notes and editor_notes.strip()
        else "\n## Editor notes\n(none)\n"
    )
    syn_user = render_prompt(
        syn_t,
        {
            "evidence_markdown": evidence_block,
            "event_title": str(row.get("title") or ""),
            "event_category": str(row.get("category") or ""),
            "confidence_score": str(row.get("confidence_score") or ""),
            "canonical_url": str(row.get("canonical_url") or ""),
            "editor_notes": notes_block,
        },
    )
    syn_data, syn_usage = model.complete_json(
        system="Respond with a single JSON object only. No markdown, no commentary.",
        user=syn_user,
        prompt_version=PROMPT_SYNTHESIS_VERSION,
    )
    merge_usage(usage_acc, syn_usage)

    title = str(syn_data.get("title") or row.get("title") or "Untitled card")
    insight = str(syn_data.get("insight_layer") or "")
    context = str(syn_data.get("context_layer") or "")
    assessments = _coerce_assessments(syn_data.get("instrument_assessments"))
    signals = _coerce_signals(syn_data.get("signals"))

    if not insight.strip() or not context.strip():
        raise ValueError("synthesis returned empty insight_layer or context_layer")

    _validate_layers(corpus=corpus, insight=insight, context=context, assessments=assessments)

    dis_t = load_prompt_markdown("dissent.v1.md")
    dis_user = render_prompt(
        dis_t,
        {
            "evidence_markdown": evidence_block,
            "insight_layer": insight,
            "context_layer": context,
        },
    )
    dis_data, dis_usage = model.complete_json(
        system="Respond with a single JSON object only. No markdown, no commentary.",
        user=dis_user,
        prompt_version=PROMPT_DISSENT_VERSION,
    )
    merge_usage(usage_acc, dis_usage)

    dissenting_view = str(dis_data.get("dissenting_view") or "").strip()
    if not dissenting_view:
        raise DissentQualityError("dissenting_view empty")
    _validate_dissent(dissenting_view)
    validate_mmj_tags(prose=dissenting_view)
    validate_numbers_in_evidence(prose=dissenting_view, evidence_corpus=corpus)

    fw_t = load_prompt_markdown("framework.v1.md")
    fw_user = render_prompt(
        fw_t,
        {
            "evidence_markdown": evidence_block,
            "insight_layer": insight,
            "context_layer": context,
            "dissenting_view": dissenting_view,
        },
    )
    fw_data, fw_usage = model.complete_json(
        system="Respond with a single JSON object only. No markdown, no commentary.",
        user=fw_user,
        prompt_version=PROMPT_FRAMEWORK_VERSION,
    )
    merge_usage(usage_acc, fw_usage)

    pattern_name = str(fw_data.get("pattern_name") or "").strip()
    framework_text = str(fw_data.get("framework_behind_this") or "").strip()
    _validate_framework(pattern_name, framework_text)
    validate_mmj_tags(prose=framework_text)
    validate_numbers_in_evidence(prose=framework_text, evidence_corpus=corpus)

    cost = estimate_cost_usd(
        input_tokens=int(usage_acc["input_tokens"]),
        output_tokens=int(usage_acc["output_tokens"]),
    )

    return insert_draft_card_bundle(
        event_id=event_id,
        title=title,
        insight_layer=insight,
        context_layer=context,
        evidence_layer=evidence_layer,
        dissenting_view=dissenting_view,
        framework_behind_this=f"**{pattern_name}**\n\n{framework_text}",
        prompt_version=COMBINED_PROMPT_VERSION,
        llm_input_tokens=int(usage_acc["input_tokens"]),
        llm_output_tokens=int(usage_acc["output_tokens"]),
        llm_cost_usd=cost,
        signals=signals,
        instrument_assessments=assessments,
    )


__all__ = [
    "COMBINED_PROMPT_VERSION",
    "DissentQualityError",
    "FrameworkQualityError",
    "draft_card_from_event",
]
