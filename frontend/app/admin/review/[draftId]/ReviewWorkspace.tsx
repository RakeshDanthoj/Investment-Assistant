"use client";

import IceCardReader, {
  type InstrumentAssessmentRow,
} from "@/components/thread/IceCardReader";
import ThreadReviewShell from "@/components/thread/ThreadReviewShell";
import { getApiBaseUrl } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import ChecklistPanel from "../_components/ChecklistPanel";

type CardPayload = {
  card_id: string;
  title: string;
  insight_layer: string;
  context_layer: string;
  evidence_layer: Record<string, unknown>;
  dissenting_view: string;
  framework_behind_this: string;
  lifecycle_state: string;
  event_title: string;
  event_category: string;
  event_confidence_score: number;
  instrument_assessments: InstrumentAssessmentRow[];
};

export default function ReviewWorkspace({ draftId }: { draftId: string }) {
  const router = useRouter();
  const [openedAtMs] = useState(() => Date.now());
  const [card, setCard] = useState<CardPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const base = getApiBaseUrl().replace(/\/$/, "");
      const res = await fetch(`${base}/api/admin/cards/${draftId}`, { cache: "no-store" });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `${res.status} ${res.statusText}`);
      }
      const data = (await res.json()) as CardPayload;
      setCard(data);
    } catch (e: unknown) {
      setCard(null);
      setError(e instanceof Error ? e.message : "Failed to load draft.");
    } finally {
      setLoading(false);
    }
  }, [draftId]);

  useEffect(() => {
    void load();
  }, [load]);

  const handlePublish = useCallback(
    async (editorReviewSeconds: number) => {
      setPublishing(true);
      setError(null);
      try {
        const base = getApiBaseUrl().replace(/\/$/, "");
        const res = await fetch(`${base}/api/admin/cards/${draftId}/publish`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ editor_review_seconds: editorReviewSeconds }),
        });
        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new Error(text || `${res.status} ${res.statusText}`);
        }
        await load();
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Publish failed.");
      } finally {
        setPublishing(false);
      }
    },
    [draftId, load],
  );

  const handleRegenerate = useCallback(
    async (notes: string) => {
      setRegenerating(true);
      setError(null);
      try {
        const base = getApiBaseUrl().replace(/\/$/, "");
        const res = await fetch(`${base}/api/admin/cards/${draftId}/regenerate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ editor_notes: notes }),
        });
        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new Error(text || `${res.status} ${res.statusText}`);
        }
        const body = (await res.json()) as { card_id: string };
        router.replace(`/admin/review/${body.card_id}`);
        router.refresh();
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Regeneration failed.");
      } finally {
        setRegenerating(false);
      }
    },
    [draftId, router],
  );

  if (loading && !card) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-finnwise-surface">
        <p className="text-sm text-slate-600">Loading draft…</p>
      </main>
    );
  }

  if (!card) {
    return (
      <main className="mx-auto max-w-lg px-6 py-16">
        <h1 className="font-display text-xl text-slate-900">Draft not available</h1>
        <p className="mt-2 text-sm text-slate-600">{error ?? "Unknown error."}</p>
      </main>
    );
  }

  const readOnly = card.lifecycle_state !== "draft";

  return (
    <ThreadReviewShell
      categoryLabel={card.event_category}
      lifecycleLabel={card.lifecycle_state}
      aside={
        readOnly ? (
          <div className="space-y-4 text-sm text-slate-700">
            <p className="font-semibold text-slate-900">This card is no longer a draft.</p>
            <p>
              Lifecycle state: <code className="font-mono text-xs">{card.lifecycle_state}</code>
            </p>
            <p className="text-xs text-slate-500">
              Publishing and regeneration actions apply only while the card is in{" "}
              <code className="font-mono">draft</code>.
            </p>
          </div>
        ) : (
          <ChecklistPanel
            openedAtMs={openedAtMs}
            onPublish={handlePublish}
            onRegenerate={handleRegenerate}
            publishing={publishing}
            regenerating={regenerating}
          />
        )
      }
    >
      {error ? (
        <div className="mx-8 mt-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
          {error}
        </div>
      ) : null}
      <IceCardReader
        title={card.title}
        eventTitle={card.event_title}
        eventConfidenceScore={card.event_confidence_score}
        insightLayer={card.insight_layer}
        contextLayer={card.context_layer}
        evidenceLayer={card.evidence_layer}
        dissentingView={card.dissenting_view}
        frameworkBehindThis={card.framework_behind_this}
        instrumentAssessments={card.instrument_assessments ?? []}
      />
    </ThreadReviewShell>
  );
}
