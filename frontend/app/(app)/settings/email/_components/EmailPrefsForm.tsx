"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { describeFetchFailure, describeHttpFailure, getApiBaseUrl } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

type PrefsResponse = {
  signal_fired_enabled: boolean;
};

type LoadState = "loading" | "ready" | "error" | "saving";

export function EmailPrefsForm() {
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [signalFiredEnabled, setSignalFiredEnabled] = useState(true);

  const loadPrefs = useCallback(async () => {
    setLoadState("loading");
    setErrorMessage(null);
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) {
      setErrorMessage("Sign in to manage email preferences.");
      setLoadState("error");
      return;
    }

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/email/preferences`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
        cache: "no-store",
      });
      if (!response.ok) {
        const text = await response.text().catch(() => "");
        throw new Error(describeHttpFailure(response.status, text, "load email preferences"));
      }
      const data = (await response.json()) as PrefsResponse;
      setSignalFiredEnabled(data.signal_fired_enabled);
      setLoadState("ready");
    } catch (error) {
      setErrorMessage(describeFetchFailure(error, "load email preferences"));
      setLoadState("error");
    }
  }, []);

  useEffect(() => {
    void loadPrefs();
  }, [loadPrefs]);

  async function handleToggle(checked: boolean) {
    setLoadState("saving");
    setErrorMessage(null);
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) {
      setErrorMessage("Sign in to save preferences.");
      setLoadState("error");
      return;
    }

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/email/preferences`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ signal_fired_enabled: checked }),
        cache: "no-store",
      });
      if (!response.ok) {
        const text = await response.text().catch(() => "");
        throw new Error(describeHttpFailure(response.status, text, "save email preferences"));
      }
      const data = (await response.json()) as PrefsResponse;
      setSignalFiredEnabled(data.signal_fired_enabled);
      setLoadState("ready");
    } catch (error) {
      setErrorMessage(describeFetchFailure(error, "save email preferences"));
      setLoadState("error");
    }
  }

  if (loadState === "loading") {
    return <p className="text-sm text-muted-foreground">Loading preferences…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 rounded-lg border border-border p-4">
        <div className="space-y-1">
          <Label htmlFor="signal-fired-email" className="text-sm font-medium">
            Signal fired alerts
          </Label>
          <p className="text-sm text-muted-foreground" id="signal-fired-email-desc">
            Email when a signal fires on a card where you logged a prediction or saved the thread.
          </p>
        </div>
        <Checkbox
          id="signal-fired-email"
          aria-describedby="signal-fired-email-desc"
          checked={signalFiredEnabled}
          disabled={loadState === "saving"}
          onCheckedChange={(checked) => void handleToggle(checked === true)}
        />
      </div>

      {errorMessage ? (
        <div className="space-y-2">
          <p className="text-sm text-destructive" role="alert">
            {errorMessage}
          </p>
          <Button type="button" variant="outline" size="sm" onClick={() => void loadPrefs()}>
            Retry
          </Button>
        </div>
      ) : null}

      {loadState === "ready" ? (
        <p className="font-mono text-[10px] text-muted-foreground">
          Each email includes a one-click unsubscribe link.
        </p>
      ) : null}
    </div>
  );
}
