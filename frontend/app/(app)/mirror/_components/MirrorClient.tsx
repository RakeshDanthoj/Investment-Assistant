"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { MirrorInitialPayload } from "@/lib/api/mirrorServer";
import { getApiBaseUrl, describeFetchFailure } from "@/lib/api";
import type {
  MirrorPredictionsResponse,
  MirrorReasoningGapsResponse,
  MirrorStatsResponse,
  MirrorStreakResponse,
  MirrorUnreadNotification,
  MirrorUnreadNotificationsResponse,
} from "@/lib/mirror/types";
import { createClient } from "@/lib/supabase/client";

import { MirrorTopbar } from "./MirrorTopbar";
import { PredictionCard } from "./PredictionCard";
import { ReadyToGradePanel } from "./ReadyToGradePanel";
import { ReasoningGapPanel } from "./ReasoningGapPanel";
import { ResolvedBadge } from "./ResolvedBadge";
import { StatsStrip } from "./StatsStrip";
import { StreakTrackerPanel } from "./StreakTrackerPanel";

type LoadState = "loading" | "ready" | "error";

function ListSkeleton() {
  return (
    <div className="space-y-4" aria-hidden>
      {[1, 2, 3].map((key) => (
        <Skeleton key={key} className="h-44 w-full rounded-lg" />
      ))}
    </div>
  );
}

type MirrorClientProps = {
  initialPayload?: MirrorInitialPayload | null;
  initialStatusFilter?: string | null;
};

export default function MirrorClient({
  initialPayload = null,
  initialStatusFilter = null,
}: MirrorClientProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const statusFilter = useMemo(() => {
    const raw = searchParams.get("status");
    if (!raw || raw === "all") return null;
    return raw;
  }, [searchParams]);

  const hydratedFromServer =
    initialPayload != null && (initialStatusFilter ?? null) === statusFilter;

  const [loadState, setLoadState] = useState<LoadState>(() =>
    hydratedFromServer ? "ready" : "loading",
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [stats, setStats] = useState<MirrorStatsResponse | null>(
    () => initialPayload?.stats ?? null,
  );
  const [predictions, setPredictions] = useState<MirrorPredictionsResponse | null>(
    () => initialPayload?.predictions ?? null,
  );
  const [streak, setStreak] = useState<MirrorStreakResponse | null>(
    () => initialPayload?.streak ?? null,
  );
  const [gaps, setGaps] = useState<MirrorReasoningGapsResponse | null>(
    () => initialPayload?.gaps ?? null,
  );
  const [gapsRefreshing, setGapsRefreshing] = useState(false);
  const [unreadNotifications, setUnreadNotifications] = useState<MirrorUnreadNotification[]>(
    () => initialPayload?.unreadNotifications ?? [],
  );
  const [expandedPredictionIds, setExpandedPredictionIds] = useState<Set<string>>(() => new Set());
  const [listLoading, setListLoading] = useState(false);

  const cardRefs = useRef<Map<string, HTMLElement>>(new Map());
  const markedReadRef = useRef<Set<string>>(new Set());
  const accessTokenRef = useRef<string | null>(null);
  const skipInitialLoadRef = useRef(hydratedFromServer);
  const initialLoadDoneRef = useRef(hydratedFromServer);
  const prevStatusFilterRef = useRef(statusFilter);

  const loadUnread = useCallback(async (token: string) => {
    const base = getApiBaseUrl();
    const res = await fetch(`${base}/api/mirror/notifications/unread`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return;
    const body = (await res.json()) as MirrorUnreadNotificationsResponse;
    setUnreadNotifications(body.items ?? []);
  }, []);

  const markNotificationRead = useCallback(async (notificationId: string, token: string) => {
    if (markedReadRef.current.has(notificationId)) return;
    markedReadRef.current.add(notificationId);

    const base = getApiBaseUrl();
    const res = await fetch(`${base}/api/mirror/notifications/${notificationId}/read`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      markedReadRef.current.delete(notificationId);
      return;
    }
    setUnreadNotifications((prev) => prev.filter((n) => n.id !== notificationId));
  }, []);

  const loadGaps = useCallback(async (token: string, refresh = false) => {
    const base = getApiBaseUrl();
    const path = refresh ? "/api/mirror/gaps/refresh" : "/api/mirror/gaps";
    const res = await fetch(`${base}${path}`, {
      method: refresh ? "POST" : "GET",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return;
    const body = (await res.json()) as MirrorReasoningGapsResponse;
    setGaps(body);
  }, []);

  const loadPredictionsOnly = useCallback(async () => {
    setListLoading(true);
    setErrorMessage(null);

    const token = accessTokenRef.current;
    if (!token) {
      setListLoading(false);
      return;
    }

    const base = getApiBaseUrl();
    const headers = { Authorization: `Bearer ${token}` };
    const statusQuery = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";

    try {
      const predictionsRes = await fetch(`${base}/api/mirror/predictions${statusQuery}`, {
        headers,
        cache: "no-store",
      });
      if (!predictionsRes.ok) {
        const text = await predictionsRes.text().catch(() => "");
        throw new Error(text || `Request failed (${predictionsRes.status})`);
      }
      const predictionsJson = (await predictionsRes.json()) as MirrorPredictionsResponse;
      setPredictions(predictionsJson);
    } catch (error) {
      setErrorMessage(describeFetchFailure(error, "load predictions"));
    } finally {
      setListLoading(false);
    }
  }, [statusFilter]);

  const loadData = useCallback(async () => {
    setLoadState("loading");
    setErrorMessage(null);

    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) {
      accessTokenRef.current = null;
      setLoadState("error");
      setErrorMessage("Sign in to view your prediction history.");
      return;
    }

    accessTokenRef.current = session.access_token;
    const base = getApiBaseUrl();
    const headers = { Authorization: `Bearer ${session.access_token}` };
    const statusQuery = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";

    try {
      const [statsRes, predictionsRes, streakRes, gapsRes] = await Promise.all([
        fetch(`${base}/api/mirror/stats`, { headers, cache: "no-store" }),
        fetch(`${base}/api/mirror/predictions${statusQuery}`, { headers, cache: "no-store" }),
        fetch(`${base}/api/mirror/streak`, { headers, cache: "no-store" }),
        fetch(`${base}/api/mirror/gaps`, { headers, cache: "no-store" }),
        loadUnread(session.access_token),
      ]);

      if (!statsRes.ok || !predictionsRes.ok || !streakRes.ok || !gapsRes.ok) {
        const failed = !statsRes.ok
          ? statsRes
          : !predictionsRes.ok
            ? predictionsRes
            : !streakRes.ok
              ? streakRes
              : gapsRes;
        const text = await failed.text().catch(() => "");
        throw new Error(text || `Request failed (${failed.status})`);
      }

      const statsJson = (await statsRes.json()) as MirrorStatsResponse;
      const predictionsJson = (await predictionsRes.json()) as MirrorPredictionsResponse;
      const streakJson = (await streakRes.json()) as MirrorStreakResponse;
      const gapsJson = (await gapsRes.json()) as MirrorReasoningGapsResponse;
      setStats(statsJson);
      setPredictions(predictionsJson);
      setStreak(streakJson);
      setGaps(gapsJson);
      setLoadState("ready");
    } catch (error) {
      setLoadState("error");
      setErrorMessage(describeFetchFailure(error, "load The Mirror"));
    }
  }, [loadUnread, statusFilter]);

  useEffect(() => {
    if (skipInitialLoadRef.current) {
      skipInitialLoadRef.current = false;
      initialLoadDoneRef.current = true;
      void (async () => {
        const supabase = createClient();
        const {
          data: { session },
        } = await supabase.auth.getSession();
        accessTokenRef.current = session?.access_token ?? null;
      })();
      return;
    }
    if (!initialLoadDoneRef.current) {
      void loadData().finally(() => {
        initialLoadDoneRef.current = true;
      });
    }
  }, [loadData]);

  useEffect(() => {
    if (!initialLoadDoneRef.current) return;
    if (prevStatusFilterRef.current === statusFilter) return;
    prevStatusFilterRef.current = statusFilter;
    if (stats != null && streak != null) {
      void loadPredictionsOnly();
    } else {
      void loadData();
    }
  }, [loadData, loadPredictionsOnly, stats, streak, statusFilter]);

  const unreadByPredictionId = useMemo(() => {
    const map = new Map<string, MirrorUnreadNotification>();
    for (const item of unreadNotifications) {
      map.set(item.prediction_id, item);
    }
    return map;
  }, [unreadNotifications]);

  const focusPrediction = useCallback((predictionId: string) => {
    setExpandedPredictionIds((prev) => new Set(prev).add(predictionId));
    const el = cardRefs.current.get(predictionId) ?? document.getElementById(`prediction-${predictionId}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, []);

  const handleReadyToGradeSelect = useCallback(
    (item: MirrorUnreadNotification) => {
      focusPrediction(item.prediction_id);
    },
    [focusPrediction],
  );

  const handleBadgeClick = useCallback(() => {
    const first = unreadNotifications[0];
    if (first) focusPrediction(first.prediction_id);
  }, [focusPrediction, unreadNotifications]);

  useEffect(() => {
    if (loadState !== "ready" || unreadNotifications.length === 0) return undefined;

    const token = accessTokenRef.current;
    if (!token) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting || entry.intersectionRatio < 0.5) continue;
          const predictionId = (entry.target as HTMLElement).dataset.predictionId;
          if (!predictionId) continue;
          const notification = unreadByPredictionId.get(predictionId);
          if (!notification) continue;
          void markNotificationRead(notification.id, token);
        }
      },
      { threshold: [0.5] },
    );

    for (const item of unreadNotifications) {
      const el = cardRefs.current.get(item.prediction_id);
      if (el) observer.observe(el);
    }

    return () => observer.disconnect();
  }, [loadState, markNotificationRead, unreadByPredictionId, unreadNotifications]);

  const handleRefreshGaps = useCallback(async () => {
    const token = accessTokenRef.current;
    if (!token) return;
    setGapsRefreshing(true);
    try {
      await loadGaps(token, true);
    } finally {
      setGapsRefreshing(false);
    }
  }, [loadGaps]);

  function onStatusChange(next: string | null) {
    const params = new URLSearchParams(searchParams.toString());
    if (next) params.set("status", next);
    else params.delete("status");
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
      <MirrorTopbar
        status={statusFilter}
        onStatusChange={onStatusChange}
        notificationSlot={<ResolvedBadge count={unreadNotifications.length} onClick={handleBadgeClick} />}
      />
      <StatsStrip stats={stats} loading={loadState === "loading" && !stats} />

      <div className="mx-auto flex w-full max-w-6xl flex-1 gap-6 px-4 py-6 min-[960px]:flex-row">
        <div className="min-w-0 flex-1">
          {loadState === "loading" || listLoading ? <ListSkeleton /> : null}

          {loadState === "error" ? (
            <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
              <p className="text-sm text-destructive">{errorMessage}</p>
              <Button type="button" variant="outline" className="mt-4" onClick={() => void loadData()}>
                Try again
              </Button>
            </div>
          ) : null}

          {loadState === "ready" && predictions?.items.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border bg-muted/20 p-10 text-center">
              <p className="font-display text-lg text-foreground">No predictions yet</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Log your view on a Thread card before opening Context. Your history will appear here.
              </p>
              <Button asChild className="mt-4">
                <Link href="/pulse">Browse The Pulse</Link>
              </Button>
            </div>
          ) : null}

          {loadState === "ready" && predictions && predictions.items.length > 0 ? (
            <ul className="space-y-4">
              {predictions.items.map((item) => (
                <li key={item.id}>
                  <PredictionCard
                    ref={(node) => {
                      if (node) cardRefs.current.set(item.id, node);
                      else cardRefs.current.delete(item.id);
                    }}
                    prediction={item}
                    expanded={expandedPredictionIds.has(item.id)}
                    onExpandedChange={(open) => {
                      setExpandedPredictionIds((prev) => {
                        const next = new Set(prev);
                        if (open) next.add(item.id);
                        else next.delete(item.id);
                        return next;
                      });
                    }}
                  />
                </li>
              ))}
            </ul>
          ) : null}
        </div>

        <aside className="w-full shrink-0 space-y-4 min-[960px]:w-[280px] min-[960px]:max-w-[35%]">
          <ReadyToGradePanel items={unreadNotifications} onSelect={handleReadyToGradeSelect} />
          <ReasoningGapPanel
            gaps={gaps}
            loading={loadState === "loading" && !gaps}
            refreshing={gapsRefreshing}
            onRefresh={() => void handleRefreshGaps()}
          />
          <StreakTrackerPanel streak={streak} loading={loadState === "loading" && !streak} />
        </aside>
      </div>
    </div>
  );
}
