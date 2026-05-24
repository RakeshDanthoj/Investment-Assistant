"""Lens card generation with six pipeline milestones (P2-S7)."""

from __future__ import annotations

import queue
import threading
from collections.abc import Iterator
from typing import Any, Literal
from uuid import UUID

from app.services.card_pipeline import draft_card_from_event
from app.services.lens_pipeline_steps import LENS_PIPELINE_STEPS
from app.services.lens_queries import (
    LensQueryRow,
    create_lens_event_for_query,
    get_query_for_user,
    update_query_status,
)

StreamStepStatus = Literal["active", "done"]


def _step_event(*, index: int, name: str, status: StreamStepStatus) -> dict[str, Any]:
    return {"event": "step", "index": index, "name": name, "status": status}


def run(
    query_id: UUID,
    *,
    user_id: UUID,
    llm: object | None = None,
) -> Iterator[dict[str, Any]]:
    """
    Runs the ICE pipeline for a Lens query and yields SSE payloads at real milestones.
    """
    row = get_query_for_user(user_id=user_id, query_id=query_id)
    if row is None:
        raise LookupError(f"lens query not found: {query_id}")

    if row.status == "done" and row.card_id is not None:
        yield {"event": "complete", "card_id": str(row.card_id)}
        return

    if row.status == "failed":
        yield {"event": "error", "message": "This query did not complete."}
        return

    milestone_queue: queue.Queue[str] = queue.Queue()
    result: dict[str, UUID] = {}
    error: list[BaseException] = []

    def on_milestone(name: str) -> None:
        milestone_queue.put(name)

    def worker(target_row: LensQueryRow) -> None:
        try:
            update_query_status(query_id, status="running")
            event_id = create_lens_event_for_query(target_row)
            card_id = draft_card_from_event(
                event_id,
                editor_notes=target_row.query,
                llm=llm,  # type: ignore[arg-type]
                on_milestone=on_milestone,
            )
            update_query_status(query_id, status="done", card_id=card_id)
            result["card_id"] = card_id
        except BaseException as exc:  # noqa: BLE001 — surface pipeline failure to stream
            error.append(exc)
            update_query_status(query_id, status="failed")

    if row.status in ("queued", "running"):
        thread = threading.Thread(target=worker, args=(row,), daemon=True)
        thread.start()

        next_index = 0
        yield _step_event(
            index=next_index,
            name=LENS_PIPELINE_STEPS[next_index],
            status="active",
        )

        while thread.is_alive() or not milestone_queue.empty():
            try:
                name = milestone_queue.get(timeout=0.05)
            except queue.Empty:
                continue
            index = LENS_PIPELINE_STEPS.index(name)
            yield _step_event(index=index, name=name, status="done")
            next_index = index + 1
            if next_index < len(LENS_PIPELINE_STEPS):
                yield _step_event(
                    index=next_index,
                    name=LENS_PIPELINE_STEPS[next_index],
                    status="active",
                )

        thread.join()

        if error:
            yield {"event": "error", "message": str(error[0])}
            return

        card_id = result.get("card_id")
        if card_id is None:
            yield {"event": "error", "message": "Card generation did not return an id."}
            return

        yield {"event": "complete", "card_id": str(card_id)}
        return

    yield {"event": "error", "message": f"Unexpected lens query status: {row.status}"}


__all__ = ["run"]
