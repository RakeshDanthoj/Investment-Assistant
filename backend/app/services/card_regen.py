"""Targeted section regen + tiered full regen (P3-S1k, G-09)."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from app.core.settings import get_settings
from app.services.card_pipeline import (
    COMBINED_PROMPT_VERSION,
    SupportsCompletion,
    _build_evidence_layer,
    _coerce_assessments,
    _coerce_signals,
    _evidence_corpus,
    _validate_dissent,
    _validate_framework,
    _validate_layers,
)
from app.services.card_repository import (
    fetch_card_detail_for_review,
    fetch_event_row,
    fetch_instrument_assessments_for_card,
    update_card_after_full_regen,
    update_card_after_section_regen,
)
from app.services.consistency_check import SectionKey, check_after_regen
from app.services.cost_guard import (
    check_monthly_budget_or_raise,
    consume_slot_or_raise,
    estimate_cost_usd,
    merge_usage,
)
from app.services.llm_client import LlmClient, load_prompt_markdown, render_prompt
from app.services.market_facts_adapters import (
    assert_critical_facts_available,
    quote_facts_to_macro_lines,
)
from app.services.mmj_validator import validate_mmj_tags
from app.services.number_validator import (
    NumberValidationResult,
    check_card,
    validate_numbers_in_evidence,
)

PROMPT_REGEN_SECTION_VERSION = "regen_section.v1"

SECTION_LABELS: dict[SectionKey, str] = {
    "insight": "Insight",
    "context": "Context",
    "evidence": "Evidence",
    "dissent": "Dissent",
    "framework": "Framework",
}

SECTION_JSON_KEYS: dict[SectionKey, str] = {
    "insight": "insight_layer",
    "context": "context_layer",
    "dissent": "dissenting_view",
    "framework": "framework_behind_this",
}


class CardRegenError(ValueError):
    """Business-rule rejection before regen runs."""


class FullRegenConfirmRequiredError(CardRegenError):
    """Second+ full regen requires explicit confirmation."""


class FullRegenBlockedError(CardRegenError):
    """Third+ full regen blocked until PO clears the flag."""


@dataclass(frozen=True)
class RegenPostCheck:
    number_validation: NumberValidationResult
    consistency_check: dict[str, Any]


@dataclass(frozen=True)
class SectionRegenResult:
    card_id: UUID
    section: SectionKey
    previous_hash: str
    new_hash: str
    post_check: RegenPostCheck


@dataclass(frozen=True)
class FullRegenResult:
    card_id: UUID
    full_regen_count: int
    post_check: RegenPostCheck


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_evidence_layer(card: dict[str, Any]) -> dict[str, Any]:
    evidence = card.get("evidence_layer")
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence) if evidence.strip() else {}
        except json.JSONDecodeError:
            evidence = {}
    return evidence if isinstance(evidence, dict) else {}


def _approved_sections_block(card: dict[str, Any], *, exclude: SectionKey) -> str:
    blocks: list[str] = []
    mapping: list[tuple[SectionKey, str, str]] = [
        ("insight", "Insight", str(card.get("insight_layer") or "")),
        ("context", "Context", str(card.get("context_layer") or "")),
        ("dissent", "Dissent", str(card.get("dissenting_view") or "")),
        ("framework", "Framework", str(card.get("framework_behind_this") or "")),
    ]
    for key, label, text in mapping:
        if key == exclude or not text.strip():
            continue
        blocks.append(f"### {label}\n{text.strip()}")
    return "\n\n".join(blocks) if blocks else "(no other prose sections yet)"


def _regen_history_entry(
    *,
    regen_type: Literal["section", "full"],
    section: SectionKey | None,
    editor_note: str,
    input_tokens: int,
    output_tokens: int,
) -> dict[str, Any]:
    return {
        "regen_type": regen_type,
        "section": section,
        "editor_note": editor_note.strip(),
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "model": get_settings().llm_model,
        "tokens_used": int(input_tokens) + int(output_tokens),
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
    }


def _run_post_checks(card: dict[str, Any], *, regen_section: SectionKey | None) -> RegenPostCheck:
    number_validation = check_card(card)
    consistency_payload: dict[str, Any]
    if regen_section is None:
        consistency_payload = {"status": "PASS", "conflicts": []}
    else:
        regen_text = _section_text_from_card(card, regen_section)
        consistency_payload = check_after_regen(
            card=card,
            regen_section=regen_section,
            regen_text=regen_text,
        ).to_dict()
    return RegenPostCheck(
        number_validation=number_validation,
        consistency_check=consistency_payload,
    )


def _section_text_from_card(card: dict[str, Any], section: SectionKey) -> str:
    if section == "insight":
        return str(card.get("insight_layer") or "")
    if section == "context":
        return str(card.get("context_layer") or "")
    if section == "dissent":
        return str(card.get("dissenting_view") or "")
    if section == "framework":
        return str(card.get("framework_behind_this") or "")
    evidence = _parse_evidence_layer(card)
    return json.dumps(evidence, sort_keys=True)


def _validate_draft_card(card: dict[str, Any]) -> None:
    if str(card.get("lifecycle_state")) != "draft":
        raise CardRegenError("only draft cards can be regenerated")


def _llm_regen_section(
    *,
    card: dict[str, Any],
    section: SectionKey,
    editor_note: str,
    llm: SupportsCompletion,
) -> tuple[str, dict[str, int]]:
    if section == "evidence":
        raise CardRegenError("evidence section uses factor DB rebuild, not LLM")

    evidence_layer = _parse_evidence_layer(card)
    evidence_md = str(evidence_layer.get("markdown") or "")
    evidence_block = f"{evidence_md}\n\n{evidence_layer.get('macro_stub') or ''}\n"
    json_key = SECTION_JSON_KEYS[section]

    template = load_prompt_markdown("regen_section.v1.md")
    user = render_prompt(
        template,
        {
            "target_section_label": SECTION_LABELS[section],
            "json_key": json_key,
            "approved_sections_block": _approved_sections_block(card, exclude=section),
            "evidence_markdown": evidence_block,
            "editor_note": editor_note.strip(),
        },
    )
    data, usage = llm.complete_json(
        system="Respond with a single JSON object only. No markdown, no commentary.",
        user=user,
        prompt_version=PROMPT_REGEN_SECTION_VERSION,
    )
    text = str(data.get(json_key) or "").strip()
    if not text:
        raise ValueError(f"regen returned empty {json_key}")

    corpus = _evidence_corpus(evidence_layer)
    validate_mmj_tags(prose=text)
    validate_numbers_in_evidence(prose=text, evidence_corpus=corpus)
    if section == "dissent":
        _validate_dissent(text)
    if section == "framework":
        body = text
        pattern = "Transferable pattern"
        if body.startswith("**"):
            end = body.find("**", 2)
            if end > 2:
                pattern = body[2:end].strip()
                body = body[end + 2 :].lstrip("\n")
        _validate_framework(pattern, body)

    return text, usage


def regenerate_section(
    card_id: UUID,
    *,
    section: SectionKey,
    editor_note: str,
    llm: SupportsCompletion | None = None,
) -> SectionRegenResult:
    """Regenerate one ICE section in-place; approved sections stay unchanged."""
    note = editor_note.strip()
    if len(note) > 500:
        raise CardRegenError("editor_note must be at most 500 characters")
    if not note:
        raise CardRegenError("editor_note is required")

    card = fetch_card_detail_for_review(card_id)
    if card is None:
        raise LookupError(f"card not found: {card_id}")
    _validate_draft_card(card)

    previous_text = _section_text_from_card(card, section)
    previous_hash = _content_hash(previous_text)

    check_monthly_budget_or_raise()
    usage_acc: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}
    new_text: str
    regen_type: Literal["section", "full"] = "section"

    if section == "evidence":
        event_id = UUID(str(card["event_id"]))
        event_row = fetch_event_row(event_id)
        if event_row is None:
            raise LookupError(f"event not found: {event_id}")
        facts_gate = assert_critical_facts_available()
        new_evidence = _build_evidence_layer(
            event_row,
            macro_fact_lines=quote_facts_to_macro_lines(facts_gate.facts),
        )
        new_text = json.dumps(new_evidence, sort_keys=True)
        history_entry = _regen_history_entry(
            regen_type=regen_type,
            section=section,
            editor_note=note,
            input_tokens=0,
            output_tokens=0,
        )
        update_card_after_section_regen(
            card_id,
            section=section,
            content=new_evidence,
            regen_history_entry=history_entry,
            llm_input_tokens=0,
            llm_output_tokens=0,
            llm_cost_usd=0.0,
        )
    else:
        consume_slot_or_raise()
        model = llm or LlmClient()
        new_text, usage = _llm_regen_section(
            card=card,
            section=section,
            editor_note=note,
            llm=model,
        )
        merge_usage(usage_acc, usage)
        cost = estimate_cost_usd(
            input_tokens=int(usage_acc["input_tokens"]),
            output_tokens=int(usage_acc["output_tokens"]),
        )
        history_entry = _regen_history_entry(
            regen_type=regen_type,
            section=section,
            editor_note=note,
            input_tokens=int(usage_acc["input_tokens"]),
            output_tokens=int(usage_acc["output_tokens"]),
        )
        update_card_after_section_regen(
            card_id,
            section=section,
            content=new_text,
            regen_history_entry=history_entry,
            llm_input_tokens=int(usage_acc["input_tokens"]),
            llm_output_tokens=int(usage_acc["output_tokens"]),
            llm_cost_usd=cost,
        )

    refreshed = fetch_card_detail_for_review(card_id)
    if refreshed is None:
        raise RuntimeError("card missing after section regen")
    refreshed["instrument_assessments"] = fetch_instrument_assessments_for_card(card_id)

    new_hash = _content_hash(_section_text_from_card(refreshed, section))
    post_check = _run_post_checks(refreshed, regen_section=section)
    return SectionRegenResult(
        card_id=card_id,
        section=section,
        previous_hash=previous_hash,
        new_hash=new_hash,
        post_check=post_check,
    )


def regenerate_full(
    card_id: UUID,
    *,
    editor_notes: str | None = None,
    confirmed: bool = False,
    llm: SupportsCompletion | None = None,
) -> FullRegenResult:
    """
    Full 3-call pipeline on the same card row.
    First full regen is silent; second requires confirm; third+ blocked without PO flag.
    """
    card = fetch_card_detail_for_review(card_id)
    if card is None:
        raise LookupError(f"card not found: {card_id}")
    _validate_draft_card(card)

    full_regen_count = int(card.get("full_regen_count") or 0)
    po_cleared = bool(card.get("po_regen_flag_cleared"))

    if full_regen_count >= 2 and not po_cleared:
        raise FullRegenBlockedError(
            "full regen blocked — Product Owner review required (full_regen_count >= 2)"
        )
    if full_regen_count >= 1 and not confirmed:
        raise FullRegenConfirmRequiredError(
            "confirmation required for full regen when full_regen_count >= 1"
        )

    event_id = UUID(str(card["event_id"]))
    event_row = fetch_event_row(event_id)
    if event_row is None:
        raise LookupError(f"event not found: {event_id}")

    check_monthly_budget_or_raise()
    started = time.perf_counter()
    usage_acc: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}

    facts_gate = assert_critical_facts_available()
    evidence_layer = _build_evidence_layer(
        event_row,
        macro_fact_lines=quote_facts_to_macro_lines(facts_gate.facts),
    )
    model = llm or LlmClient()

    consume_slot_or_raise()
    evidence_md = str(evidence_layer.get("markdown") or "")
    evidence_block = f"{evidence_md}\n\n{evidence_layer.get('macro_stub') or ''}\n"
    corpus = _evidence_corpus(evidence_layer)

    notes_block = (
        f"\n## Editor notes\n{editor_notes.strip()}\n"
        if editor_notes and editor_notes.strip()
        else "\n## Editor notes\n(none)\n"
    )
    syn_t = load_prompt_markdown("synthesis.v1.md")
    syn_user = render_prompt(
        syn_t,
        {
            "evidence_markdown": evidence_block,
            "event_title": str(event_row.get("title") or ""),
            "event_category": str(event_row.get("category") or ""),
            "confidence_score": str(event_row.get("confidence_score") or ""),
            "canonical_url": str(event_row.get("canonical_url") or ""),
            "editor_notes": notes_block,
        },
    )
    syn_data, syn_usage = model.complete_json(
        system="Respond with a single JSON object only. No markdown, no commentary.",
        user=syn_user,
        prompt_version="synthesis.v1",
    )
    merge_usage(usage_acc, syn_usage)

    title = str(syn_data.get("title") or event_row.get("title") or "Untitled card")
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
        prompt_version="dissent.v1",
    )
    merge_usage(usage_acc, dis_usage)

    dissenting_view = str(dis_data.get("dissenting_view") or "").strip()
    if not dissenting_view:
        raise ValueError("dissenting_view empty")
    _validate_dissent(dissenting_view)

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
        prompt_version="framework.v1",
    )
    merge_usage(usage_acc, fw_usage)

    pattern_name = str(fw_data.get("pattern_name") or "").strip()
    framework_text = str(fw_data.get("framework_behind_this") or "").strip()
    _validate_framework(pattern_name, framework_text)

    validate_mmj_tags(prose=dissenting_view)
    validate_numbers_in_evidence(prose=dissenting_view, evidence_corpus=corpus)
    validate_mmj_tags(prose=framework_text)
    validate_numbers_in_evidence(prose=framework_text, evidence_corpus=corpus)

    cost = estimate_cost_usd(
        input_tokens=int(usage_acc["input_tokens"]),
        output_tokens=int(usage_acc["output_tokens"]),
    )
    _ = int((time.perf_counter() - started) * 1000)

    history_entry = _regen_history_entry(
        regen_type="full",
        section=None,
        editor_note=(editor_notes or "").strip(),
        input_tokens=int(usage_acc["input_tokens"]),
        output_tokens=int(usage_acc["output_tokens"]),
    )

    new_count = update_card_after_full_regen(
        card_id,
        title=title,
        insight_layer=insight,
        context_layer=context,
        evidence_layer=evidence_layer,
        dissenting_view=dissenting_view,
        framework_behind_this=f"**{pattern_name}**\n\n{framework_text}",
        prompt_version=COMBINED_PROMPT_VERSION,
        signals=signals,
        instrument_assessments=assessments,
        regen_history_entry=history_entry,
        llm_input_tokens=int(usage_acc["input_tokens"]),
        llm_output_tokens=int(usage_acc["output_tokens"]),
        llm_cost_usd=cost,
    )

    refreshed = fetch_card_detail_for_review(card_id)
    if refreshed is None:
        raise RuntimeError("card missing after full regen")
    refreshed["instrument_assessments"] = fetch_instrument_assessments_for_card(card_id)
    post_check = _run_post_checks(refreshed, regen_section=None)

    return FullRegenResult(
        card_id=card_id,
        full_regen_count=new_count,
        post_check=post_check,
    )


__all__ = [
    "CardRegenError",
    "FullRegenBlockedError",
    "FullRegenConfirmRequiredError",
    "FullRegenResult",
    "SectionRegenResult",
    "regenerate_full",
    "regenerate_section",
]
