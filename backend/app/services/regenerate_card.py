"""Editorial regenerate path — new draft + archive superseded draft (P1-S8)."""

from __future__ import annotations

from uuid import UUID

from app.services.card_pipeline import draft_card_from_event
from app.services.card_repository import archive_card, fetch_card_detail_for_review


class RegenerateCardError(ValueError):
    """Business-rule rejection before the LLM pipeline runs."""


def regenerate_draft_with_notes(card_id: UUID, editor_notes: str) -> UUID:
    detail = fetch_card_detail_for_review(card_id)
    if detail is None:
        raise LookupError(f"card not found: {card_id}")
    if str(detail["lifecycle_state"]) != "draft":
        raise RegenerateCardError("only draft cards can be regenerated")

    event_id = UUID(str(detail["event_id"]))
    notes = editor_notes.strip() or None
    new_id = draft_card_from_event(event_id, editor_notes=notes)
    archive_card(card_id)
    return new_id


__all__ = ["RegenerateCardError", "regenerate_draft_with_notes"]
