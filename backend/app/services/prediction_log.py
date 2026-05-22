"""Backward-compatible shim — prefer app.services.predictions (P1-S12)."""

from app.services.predictions import (
    DuplicatePredictionError,
)
from app.services.predictions import (
    PredictionError as PredictionLogError,
)
from app.services.predictions import (
    log as log_prediction,
)

__all__ = ["DuplicatePredictionError", "PredictionLogError", "log_prediction"]
