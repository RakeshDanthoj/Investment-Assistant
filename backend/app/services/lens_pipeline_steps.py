"""PRD §5 Screen 5 — Lens loading pipeline step labels (P2-S7)."""

from __future__ import annotations

from typing import Final

STEP_FACTOR_DB: Final = "Factor DB queried"
STEP_MACRO_SIGNALS: Final = "Macro signals retrieved"
STEP_SYNTHESIS: Final = "Synthesising ICE layers"
STEP_DISSENT: Final = "Generating dissenting view"
STEP_FRAMEWORK: Final = "Articulating framework"
STEP_VALIDATE: Final = "Validating numbers against Evidence"

LENS_PIPELINE_STEPS: Final[tuple[str, ...]] = (
    STEP_FACTOR_DB,
    STEP_MACRO_SIGNALS,
    STEP_SYNTHESIS,
    STEP_DISSENT,
    STEP_FRAMEWORK,
    STEP_VALIDATE,
)

__all__ = [
    "LENS_PIPELINE_STEPS",
    "STEP_DISSENT",
    "STEP_FACTOR_DB",
    "STEP_FRAMEWORK",
    "STEP_MACRO_SIGNALS",
    "STEP_SYNTHESIS",
    "STEP_VALIDATE",
]
