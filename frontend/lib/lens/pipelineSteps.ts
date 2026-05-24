/** PRD §5 Screen 5 — six Lens pipeline step labels (must match backend). */

export const LENS_PIPELINE_STEPS = [
  "Factor DB queried",
  "Macro signals retrieved",
  "Synthesising ICE layers",
  "Generating dissenting view",
  "Articulating framework",
  "Validating numbers against Evidence",
] as const;

export type LensPipelineStepName = (typeof LENS_PIPELINE_STEPS)[number];

export const LENS_DISCLAIMER =
  "Every number is validated against the Evidence layer before display.";
