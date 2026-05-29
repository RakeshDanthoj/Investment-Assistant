"""Shared SQL fragments for user-facing read queries (PRD2 G-13)."""


class SyntheticFilterMixin:
    """Exclude `is_synthetic = TRUE` rows from Pulse, Thread, and Mirror read paths."""

    @staticmethod
    def events_not_synthetic(alias: str = "e") -> str:
        # IS NOT TRUE matches partial indexes on (is_synthetic IS NOT TRUE).
        return f"{alias}.is_synthetic IS NOT TRUE"

    @staticmethod
    def predictions_not_synthetic(alias: str = "up") -> str:
        return f"{alias}.is_synthetic IS NOT TRUE"

    @staticmethod
    def track_record_not_synthetic(alias: str = "tr") -> str:
        return f"{alias}.is_synthetic IS NOT TRUE"

    @staticmethod
    def signals_not_synthetic(alias: str = "s") -> str:
        return f"{alias}.is_synthetic IS NOT TRUE"
