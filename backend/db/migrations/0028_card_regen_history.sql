-- P3-S1k — Targeted section regen audit trail + full regen tier guard (G-09).

ALTER TABLE public.cards
  ADD COLUMN IF NOT EXISTS regen_history jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS full_regen_count integer NOT NULL DEFAULT 0
    CHECK (full_regen_count >= 0),
  ADD COLUMN IF NOT EXISTS po_regen_flag_cleared boolean NOT NULL DEFAULT false;

COMMENT ON COLUMN public.cards.regen_history IS
  'Append-only audit of section/full regen: section, editor_note, timestamp, model, tokens_used.';

COMMENT ON COLUMN public.cards.full_regen_count IS
  'Count of full 3-call regenerations; confirm required at >=1, blocked at >=2 without PO flag.';

COMMENT ON COLUMN public.cards.po_regen_flag_cleared IS
  'Product Owner cleared full regen block after full_regen_count >= 2.';
