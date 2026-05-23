"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { PhaseBadge } from "@/components/Topbar/PhaseBadge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { describeFetchFailure } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";
import { TESTER_BRIEFING_SECTIONS } from "@/lib/tester-briefing/content";

const TESTER_BRIEFING_NEXT = "/tester-briefing";

async function parseAcceptError(response: Response): Promise<string> {
  const text = await response.text();
  if (!text) return `Accept failed (${response.status})`;
  try {
    const json = JSON.parse(text) as {
      message?: string;
      detail?: string | { message?: string; code?: string };
    };
    if (typeof json.message === "string" && json.message) return json.message;
    if (typeof json.detail === "string" && json.detail) return json.detail;
    if (json.detail && typeof json.detail === "object" && json.detail.message) {
      return json.detail.message;
    }
  } catch {
    /* plain-text error from backend */
  }
  return text;
}

/** Nearest ancestor that scrolls (e.g. AppShell main), not the briefing pane itself. */
function findScrollParent(node: HTMLElement | null): HTMLElement | null {
  let el = node?.parentElement ?? null;
  while (el) {
    const { overflowY } = getComputedStyle(el);
    if (overflowY === "auto" || overflowY === "scroll" || overflowY === "overlay") {
      return el;
    }
    el = el.parentElement;
  }
  return null;
}

function isScrolledToEnd(root: HTMLElement | null): boolean {
  const slack = 24;
  if (root) {
    return root.scrollTop + root.clientHeight >= root.scrollHeight - slack;
  }
  const doc = document.documentElement;
  return window.scrollY + window.innerHeight >= doc.scrollHeight - slack;
}

export default function TesterBriefingPage() {
  const router = useRouter();
  const endSentinelRef = useRef<HTMLDivElement>(null);
  const [hasScrolledToEnd, setHasScrolledToEnd] = useState(false);
  const [checked, setChecked] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const supabase = createClient();
    void supabase.auth.getUser().then(({ data: { user } }) => {
      if (!user) {
        router.replace(`/sign-in?next=${encodeURIComponent(TESTER_BRIEFING_NEXT)}`);
      }
    });
  }, [router]);

  useEffect(() => {
    const sentinel = endSentinelRef.current;
    if (!sentinel) return;

    const scrollRoot = findScrollParent(sentinel);

    const markIfAtEnd = () => {
      if (isScrolledToEnd(scrollRoot)) {
        setHasScrolledToEnd(true);
      }
    };

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setHasScrolledToEnd(true);
        }
      },
      { root: scrollRoot, threshold: 0, rootMargin: "0px 0px 48px 0px" },
    );

    observer.observe(sentinel);
    markIfAtEnd();

    const scrollTarget: HTMLElement | Window = scrollRoot ?? window;
    scrollTarget.addEventListener("scroll", markIfAtEnd, { passive: true });
    window.addEventListener("resize", markIfAtEnd, { passive: true });

    return () => {
      observer.disconnect();
      scrollTarget.removeEventListener("scroll", markIfAtEnd);
      window.removeEventListener("resize", markIfAtEnd);
    };
  }, []);

  async function onAccept() {
    if (!checked || !hasScrolledToEnd || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/tester/accept", { method: "POST" });
      if (res.status === 401) {
        router.replace(`/sign-in?next=${encodeURIComponent(TESTER_BRIEFING_NEXT)}`);
        return;
      }
      if (!res.ok) {
        throw new Error(await parseAcceptError(res));
      }
      router.replace("/pulse");
      router.refresh();
    } catch (e) {
      const message = describeFetchFailure(e, "record your briefing acceptance");
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

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6">
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
          <div ref={endSentinelRef} className="h-px w-full shrink-0" aria-hidden />
        </div>
      </div>

      <div className="sticky bottom-0 z-10 border-t border-border bg-card px-4 py-4 shadow-[0_-8px_24px_rgba(0,0,0,0.06)]">
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
            <Alert variant="destructive" role="alert">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}

          <Button type="button" disabled={!canAccept} onClick={() => void onAccept()}>
            {submitting ? "Recording acceptance…" : "Accept and enter FinnWise"}
          </Button>
        </div>
      </div>
    </div>
  );
}
