"use client";

import { useRouter } from "next/navigation";
import { useCallback, useRef, useState } from "react";

import { SebiFooter } from "@/components/SebiFooter";
import { PhaseBadge } from "@/components/Topbar/PhaseBadge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { getApiBaseUrl } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import { TESTER_BRIEFING_SECTIONS } from "@/lib/tester-briefing/content";

export default function TesterBriefingPage() {
  const router = useRouter();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [hasScrolledToEnd, setHasScrolledToEnd] = useState(false);
  const [checked, setChecked] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const atEnd = el.scrollTop + el.clientHeight >= el.scrollHeight - 24;
    if (atEnd) setHasScrolledToEnd(true);
  }, []);

  async function onAccept() {
    if (!checked || !hasScrolledToEnd) return;
    setSubmitting(true);
    setError(null);
    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session?.access_token) {
        setError("Sign in with your invite link before accepting the briefing.");
        return;
      }
      const base = getApiBaseUrl().replace(/\/$/, "");
      const res = await fetch(`${base}/api/tester/accept`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) {
        const body = await res.text();
        throw new Error(body || `Accept failed (${res.status})`);
      }
      router.replace("/pulse");
      router.refresh();
    } catch (e) {
      const message =
        e instanceof Error ? e.message : "Could not record acceptance. Please try again.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  const canAccept = hasScrolledToEnd && checked && !submitting;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <header className="border-b border-border bg-card px-4 py-3">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="font-display text-xl font-semibold text-foreground">
              Phase 1 tester briefing
            </h1>
            <p className="mt-1 font-mono text-[10px] text-muted-foreground">
              Read in full, then accept to continue
            </p>
          </div>
          <PhaseBadge />
        </div>
      </header>

      <div
        ref={scrollRef}
        onScroll={onScroll}
        className="min-h-0 flex-1 overflow-y-auto px-4 py-6"
      >
        <div className="mx-auto max-w-3xl space-y-4">
          {TESTER_BRIEFING_SECTIONS.map((section) => (
            <Card key={section.title}>
              <CardHeader className="pb-2">
                <CardTitle className="font-display text-base">{section.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm leading-relaxed text-foreground">
                {section.paragraphs.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
                {section.bullets ? (
                  <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
                    {section.bullets.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <div className="border-t border-border bg-card px-4 py-4">
        <div className="mx-auto flex max-w-3xl flex-col gap-4">
          {!hasScrolledToEnd ? (
            <p className="font-mono text-[10px] text-muted-foreground">
              Scroll through the full briefing to enable acceptance.
            </p>
          ) : null}

          <div className="flex items-start gap-3">
            <Checkbox
              id="tester-accept"
              checked={checked}
              onCheckedChange={(value) => setChecked(value === true)}
              disabled={!hasScrolledToEnd || submitting}
            />
            <Label htmlFor="tester-accept" className="text-sm leading-snug">
              I have read this briefing, understand FinnWise is educational analysis only, and
              will not make real-money investment decisions based on the app during this test.
            </Label>
          </div>

          {error ? (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}

          <Button type="button" disabled={!canAccept} onClick={() => void onAccept()}>
            {submitting ? "Recording acceptance…" : "Accept and enter FinnWise"}
          </Button>
        </div>
      </div>

      <SebiFooter />
    </div>
  );
}
