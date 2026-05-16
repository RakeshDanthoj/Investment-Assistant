from enum import StrEnum


class MmjType(StrEnum):
    MEASURED = "MEASURED"
    MODELLED = "MODELLED"
    JUDGED = "JUDGED"


class LifecycleState(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    SIGNAL_TRIGGERED = "signal_triggered"
    THESIS_CONFIRMED = "thesis_confirmed"
    THESIS_WEAKENED = "thesis_weakened"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class SignalState(StrEnum):
    PENDING = "pending"
    TRIGGERED = "triggered"
    RESOLVED = "resolved"


class EventCategory(StrEnum):
    MACRO = "macro"
    RBI_POLICY = "rbi_policy"
    REGULATORY = "regulatory"
    INDIA_SPECIFIC = "india_specific"
    GEOPOLITICAL = "geopolitical"
    BUDGET = "budget"


MMJ_TYPE_VALUES: frozenset[str] = frozenset(m.value for m in MmjType)
LIFECYCLE_STATE_VALUES: frozenset[str] = frozenset(s.value for s in LifecycleState)
SIGNAL_STATE_VALUES: frozenset[str] = frozenset(s.value for s in SignalState)
EVENT_CATEGORY_VALUES: frozenset[str] = frozenset(c.value for c in EventCategory)
