"""Fan-out signal-fired emails when a signal transitions to triggered (P2-S10)."""

from __future__ import annotations

import logging
from uuid import UUID, uuid4

from app.services import email_client

_LOG = logging.getLogger(__name__)

_SIGNAL_FIRED_TEMPLATE = "signal_fired.html"
_SIGNAL_FIRED_SUBJECT = "A signal you were watching has fired — FinnWise"


def _table_exists(cur, table_name: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
        LIMIT 1
        """,
        (table_name,),
    )
    return cur.fetchone() is not None


def _stakeholder_user_ids(cur, *, card_id: str) -> set[str]:
    cur.execute(
        """
        SELECT user_id::text
        FROM public.user_predictions
        WHERE card_id = %s::uuid
        """,
        (card_id,),
    )
    user_ids = {str(row[0]) for row in cur.fetchall()}

    if _table_exists(cur, "saved_threads"):
        cur.execute(
            """
            SELECT user_id::text
            FROM public.saved_threads
            WHERE card_id = %s::uuid
            """,
            (card_id,),
        )
        user_ids.update(str(row[0]) for row in cur.fetchall())

    return user_ids


def _ensure_preferences_row(cur, user_id: str) -> None:
    cur.execute(
        """
        INSERT INTO public.user_email_preferences (user_id, signal_fired_enabled)
        VALUES (%s::uuid, true)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id,),
    )


def _is_opted_in(cur, user_id: str) -> bool:
    _ensure_preferences_row(cur, user_id)
    cur.execute(
        """
        SELECT signal_fired_enabled
        FROM public.user_email_preferences
        WHERE user_id = %s::uuid
        """,
        (user_id,),
    )
    row = cur.fetchone()
    return bool(row and row[0])


def _already_sent(cur, *, user_id: str, signal_id: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM public.signal_email_log
        WHERE user_id = %s::uuid AND signal_id = %s::uuid
        LIMIT 1
        """,
        (user_id, signal_id),
    )
    return cur.fetchone() is not None


def _create_unsubscribe_token(cur, user_id: str) -> str:
    token = str(uuid4())
    cur.execute(
        """
        INSERT INTO public.unsubscribe_tokens (token, user_id)
        VALUES (%s::uuid, %s::uuid)
        """,
        (token, user_id),
    )
    return token


def _lookup_email(cur, user_id: str) -> str | None:
    cur.execute(
        """
        SELECT email
        FROM auth.users
        WHERE id = %s::uuid
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    email = row[0]
    if not email or not str(email).strip():
        return None
    return str(email).strip()


def fan_out(cur, *, card_id: str, signal_id: str, card_title: str) -> int:
    """
    Send signal-fired emails to opted-in users with a prediction or saved thread on the card.
    Returns the number of emails successfully sent (or skipped when provider unconfigured).
    """
    stakeholder_ids = _stakeholder_user_ids(cur, card_id=card_id)
    if not stakeholder_ids:
        return 0

    public_base = email_client._resolve_public_url()
    thread_url = f"{public_base}/thread/{card_id}"
    sent_count = 0

    for user_id in stakeholder_ids:
        if not _is_opted_in(cur, user_id):
            continue
        if _already_sent(cur, user_id=user_id, signal_id=signal_id):
            continue

        to_email = _lookup_email(cur, user_id)
        if not to_email:
            _LOG.warning(
                "email_on_signal.skip_no_email",
                extra={"user_id": user_id, "card_id": card_id},
            )
            continue

        token = _create_unsubscribe_token(cur, user_id)
        unsubscribe_url = f"{public_base.rstrip('/')}/backend/unsubscribe?token={token}"

        try:
            delivered = email_client.send(
                template=_SIGNAL_FIRED_TEMPLATE,
                to=to_email,
                subject=_SIGNAL_FIRED_SUBJECT,
                variables={
                    "card_title": card_title or "Event card",
                    "thread_url": thread_url,
                    "unsubscribe_url": unsubscribe_url,
                },
            )
        except email_client.EmailDeliveryError as exc:
            _LOG.error(
                "email_on_signal.send_failed",
                extra={"user_id": user_id, "signal_id": signal_id, "error": str(exc)},
            )
            continue

        if not delivered:
            continue

        cur.execute(
            """
            INSERT INTO public.signal_email_log (user_id, signal_id)
            VALUES (%s::uuid, %s::uuid)
            ON CONFLICT DO NOTHING
            """,
            (user_id, signal_id),
        )
        sent_count += 1

    return sent_count


def fan_out_uuid(cur, *, card_id: UUID, signal_id: UUID, card_title: str) -> int:
    return fan_out(
        cur,
        card_id=str(card_id),
        signal_id=str(signal_id),
        card_title=card_title,
    )


__all__ = ["fan_out", "fan_out_uuid", "_stakeholder_user_ids"]
