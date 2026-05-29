"""P3-T1: static guard — user-facing read modules must apply SyntheticFilterMixin (G-13)."""

from __future__ import annotations

from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parents[1]

# Modules that serve Pulse, Thread, Mirror, or related user-facing reads (P3-S0 / P3-T1).
USER_FACING_READ_MODULES: dict[str, tuple[str, ...]] = {
    "app/services/feed.py": ("events_not_synthetic",),
    "app/services/card_repository.py": ("events_not_synthetic",),
    "app/services/mirror_predictions.py": (
        "predictions_not_synthetic",
        "events_not_synthetic",
    ),
    "app/services/market_facts.py": ("events_not_synthetic",),
}


def _module_path(relative: str) -> Path:
    return _BACKEND_ROOT / relative


@pytest.mark.parametrize(
    ("relative_path", "required_fragments"),
    list(USER_FACING_READ_MODULES.items()),
    ids=list(USER_FACING_READ_MODULES.keys()),
)
def test_user_facing_module_imports_and_applies_synthetic_filter(
    relative_path: str,
    required_fragments: tuple[str, ...],
) -> None:
    path = _module_path(relative_path)
    assert path.is_file(), f"missing user-facing read module: {relative_path}"
    source = path.read_text(encoding="utf-8")
    assert "SyntheticFilterMixin" in source, (
        f"{relative_path} must import SyntheticFilterMixin for synthetic isolation"
    )
    for fragment in required_fragments:
        assert fragment in source, (
            f"{relative_path} must call SyntheticFilterMixin.{fragment} in SQL paths"
        )


def test_synthetic_filter_mixin_documents_pulse_thread_mirror_scope() -> None:
    from app.db.queries.base import SyntheticFilterMixin

    assert SyntheticFilterMixin.__doc__ is not None
    assert "Pulse" in SyntheticFilterMixin.__doc__
    assert SyntheticFilterMixin.events_not_synthetic("e") == "e.is_synthetic IS NOT TRUE"
