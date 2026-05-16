from app.models.enums import (
    EVENT_CATEGORY_VALUES,
    LIFECYCLE_STATE_VALUES,
    MMJ_TYPE_VALUES,
    SIGNAL_STATE_VALUES,
    EventCategory,
    LifecycleState,
    MmjType,
    SignalState,
)


def test_mmj_type_matches_prd() -> None:
    assert MMJ_TYPE_VALUES == frozenset({"MEASURED", "MODELLED", "JUDGED"})
    assert set(MmjType) == MMJ_TYPE_VALUES


def test_lifecycle_state_has_eight_prd_states() -> None:
    expected = frozenset(
        {
            "draft",
            "published",
            "active",
            "signal_triggered",
            "thesis_confirmed",
            "thesis_weakened",
            "resolved",
            "archived",
        }
    )
    assert LIFECYCLE_STATE_VALUES == expected
    assert len(LifecycleState) == 8


def test_signal_state_values() -> None:
    assert SIGNAL_STATE_VALUES == frozenset({"pending", "triggered", "resolved"})
    assert set(SignalState) == SIGNAL_STATE_VALUES


def test_event_category_values() -> None:
    expected = frozenset(
        {
            "macro",
            "rbi_policy",
            "regulatory",
            "india_specific",
            "geopolitical",
            "budget",
        }
    )
    assert EVENT_CATEGORY_VALUES == expected
    assert set(EventCategory) == EVENT_CATEGORY_VALUES
