"""Editorial checklist orchestrator — four automated checks + one manual (P3-S1j / G-15)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from app.services.factor_db import freshness_for_retrieved_at
from app.services.number_validator import NumberValidationResult
from app.services.number_validator import check_card as check_numbers
from app.services.sebi_compliance_scan import SebiComplianceResult
from app.services.sebi_compliance_scan import scan_card as scan_sebi

DISSENT_MIN_CHARS = 100
EVIDENCE_MAX_AGE_MONTHS = 18

ChecklistStatus = Literal["PASS", "FAIL", "PENDING"]


@dataclass(frozen=True)
class ChecklistItem:
    key: str
    label: str
    automated: bool
    status: ChecklistStatus
    message: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "automated": self.automated,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class EditorialChecklistResult:
    items: list[ChecklistItem] = field(default_factory=list)

    @property
    def all_automated_pass(self) -> bool:
        return all(item.status == "PASS" for item in self.items if item.automated)

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "all_automated_pass": self.all_automated_pass,
        }


class EditorialChecklistFailedError(ValueError):
    """Raised when publish is blocked by an automated editorial checklist item."""

    def __init__(self, result: EditorialChecklistResult) -> None:
        self.result = result
        super().__init__("editorial checklist failed")


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


def _normalize_evidence_layer(card: dict[str, Any]) -> dict[str, Any]:
    evidence = card.get("evidence_layer")
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence) if evidence.strip() else {}
        except json.JSONDecodeError:
            evidence = {}
    if not isinstance(evidence, dict):
        evidence = {}
    return evidence


def _collect_evidence_retrieved_at(evidence_layer: dict[str, Any]) -> list[tuple[str, datetime]]:
    rows: list[tuple[str, datetime]] = []

    sources = evidence_layer.get("sources")
    if isinstance(sources, list):
        for idx, item in enumerate(sources):
            if not isinstance(item, dict):
                continue
            retrieved = _parse_iso_dt(item.get("retrieved_at") or item.get("date_retrieved"))
            if retrieved is not None:
                rows.append((str(item.get("id") or f"source-{idx}"), retrieved))

    matrix = evidence_layer.get("matrix_snapshot") or {}
    sensitivities = matrix.get("sensitivities") if isinstance(matrix, dict) else {}
    if isinstance(sensitivities, dict):
        for ticker, factors in sensitivities.items():
            if not isinstance(factors, dict):
                continue
            for fslug, cell in factors.items():
                if not isinstance(cell, dict):
                    continue
                retrieved = _parse_iso_dt(cell.get("retrieved_at"))
                if retrieved is not None:
                    rows.append((f"matrix:{ticker}:{fslug}", retrieved))

    return rows


def _check_dissent(card: dict[str, Any]) -> ChecklistItem:
    dissent = str(card.get("dissenting_view") or "").strip()
    length = len(dissent)
    if length > DISSENT_MIN_CHARS:
        return ChecklistItem(
            key="dissent",
            label="A specific dissenting mechanism is present — not a generic disclaimer.",
            automated=True,
            status="PASS",
            message=f"Dissent length {length} chars (> {DISSENT_MIN_CHARS}).",
        )
    return ChecklistItem(
        key="dissent",
        label="A specific dissenting mechanism is present — not a generic disclaimer.",
        automated=True,
        status="FAIL",
        message=f"Dissent length {length} chars (need > {DISSENT_MIN_CHARS}).",
        details={"length": length, "min_length": DISSENT_MIN_CHARS},
    )


def _check_evidence_freshness(
    card: dict[str, Any],
    *,
    reference: datetime | None = None,
) -> ChecklistItem:
    label = (
        "Every Evidence source is no older than 18 months "
        "(MEASURED claims must not rely on stale data)."
    )
    evidence_layer = _normalize_evidence_layer(card)
    rows = _collect_evidence_retrieved_at(evidence_layer)
    if not rows:
        return ChecklistItem(
            key="evidence_freshness",
            label=label,
            automated=True,
            status="PASS",
            message="No dated Evidence rows to evaluate.",
        )

    stale: list[dict[str, Any]] = []
    for evidence_id, retrieved in rows:
        freshness = freshness_for_retrieved_at(retrieved, reference=reference)
        if freshness == "red":
            stale.append(
                {
                    "evidence_id": evidence_id,
                    "retrieved_at": retrieved.isoformat(),
                    "freshness": freshness,
                }
            )

    if stale:
        return ChecklistItem(
            key="evidence_freshness",
            label=label,
            automated=True,
            status="FAIL",
            message=f"{len(stale)} Evidence row(s) exceed {EVIDENCE_MAX_AGE_MONTHS}-month max age.",
            details={"stale_rows": stale, "max_age_months": EVIDENCE_MAX_AGE_MONTHS},
        )

    return ChecklistItem(
        key="evidence_freshness",
        label=label,
        automated=True,
        status="PASS",
        message="All dated Evidence rows are within 18 months.",
    )


def _check_numbers(number_result: NumberValidationResult) -> ChecklistItem:
    label = (
        "Every quantitative claim carries [MEASURED], [MODELLED], or [JUDGED] "
        "and ties back to Evidence."
    )
    if number_result.status == "PASS":
        return ChecklistItem(
            key="numbers",
            label=label,
            automated=True,
            status="PASS",
            message="Number validator PASS.",
            details=number_result.to_dict(),
        )
    return ChecklistItem(
        key="numbers",
        label=label,
        automated=True,
        status="FAIL",
        message="Number validator FAIL — ungrounded numbers or missing provenance.",
        details=number_result.to_dict(),
    )


def _check_sebi(sebi_result: SebiComplianceResult) -> ChecklistItem:
    label = "No buy / sell / hold or personalised recommendation language appears on the card."
    if sebi_result.status == "PASS":
        return ChecklistItem(
            key="sebi_compliance",
            label=label,
            automated=True,
            status="PASS",
            message="SEBI language scan PASS.",
        )
    return ChecklistItem(
        key="sebi_compliance",
        label=label,
        automated=True,
        status="FAIL",
        message=f"SEBI language scan found {len(sebi_result.violations)} violation(s).",
        details=sebi_result.to_dict(),
    )


def _plain_english_item() -> ChecklistItem:
    return ChecklistItem(
        key="plain_english",
        label="Language is accessible to a non-expert reader (plain explanations, minimal jargon).",
        automated=False,
        status="PENDING",
        message="Editor must confirm plain English before publishing.",
    )


def check_card(
    card: dict[str, Any],
    *,
    reference: datetime | None = None,
) -> EditorialChecklistResult:
    """Run four automated editorial checks. Plain English remains a manual UI tick."""
    number_result = check_numbers(card)
    sebi_result = scan_sebi(card)
    return EditorialChecklistResult(
        items=[
            _check_numbers(number_result),
            _check_dissent(card),
            _check_evidence_freshness(card, reference=reference),
            _check_sebi(sebi_result),
            _plain_english_item(),
        ]
    )


def assert_automated_pass(card: dict[str, Any], *, reference: datetime | None = None) -> None:
    """Publish helper — raises EditorialChecklistFailedError when any auto item fails."""
    result = check_card(card, reference=reference)
    if not result.all_automated_pass:
        raise EditorialChecklistFailedError(result)


__all__ = [
    "DISSENT_MIN_CHARS",
    "EVIDENCE_MAX_AGE_MONTHS",
    "ChecklistItem",
    "EditorialChecklistFailedError",
    "EditorialChecklistResult",
    "assert_automated_pass",
    "check_card",
]
