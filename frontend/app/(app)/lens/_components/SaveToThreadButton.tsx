"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { getApiBaseUrl, describeFetchFailure } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

type SaveToThreadButtonProps = {
  cardId: string;
  onSaved?: () => void;
};

export function SaveToThreadButton({ cardId, onSaved }: SaveToThreadButtonProps) {
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = window.setTimeout(() => setToast(null), 4000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const save = useCallback(async () => {
    setSaving(true);
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      setToast("Sign in to save cards to Thread.");
      setSaving(false);
      return;
    }

    try {
      const base = getApiBaseUrl();
      const res = await fetch(`${base}/api/saved-threads`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ card_id: cardId }),
        cache: "no-store",
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `Save failed (${res.status})`);
      }
      setSaved(true);
      setToast("Saved to your Thread collection");
      window.dispatchEvent(new CustomEvent("saved-threads-changed"));
      onSaved?.();
    } catch (error) {
      setToast(describeFetchFailure(error, "save to Thread"));
    } finally {
      setSaving(false);
    }
  }, [cardId, onSaved]);

  return (
    <div className="relative">
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={saving || saved}
        onClick={() => void save()}
      >
        {saved ? "Saved to Thread" : "Save to Thread"}
      </Button>
      {toast ? (
        <p
          role="status"
          className="absolute right-0 top-full z-10 mt-2 whitespace-nowrap rounded-md border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 shadow-sm"
        >
          {toast}
        </p>
      ) : null}
    </div>
  );
}
