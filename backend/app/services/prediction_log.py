"""Backward-compatible shim — prefer app.services.predictions (P1-S12)."""

from app.services.predictions import (
    DuplicatePredictionError,
    PredictionError as PredictionLogError,
    log as log_prediction,
)

__all__ = ["DuplicatePredictionError", "PredictionLogError", "log_prediction"]
