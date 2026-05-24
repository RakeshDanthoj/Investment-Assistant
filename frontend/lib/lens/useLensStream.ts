"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getApiBaseUrl } from "@/lib/api";

import {
  applyStreamStep,
  initialPipelineStepStatuses,
  progressPercentFromSteps,
  type LensStreamPayload,
  type PipelineStepStatus,
} from "./streamTypes";

type UseLensStreamOptions = {
  queryId: string | null;
  accessToken: string | null;
  enabled: boolean;
  onComplete: (cardId: string) => void;
  onError: (message: string) => void;
};

type UseLensStreamResult = {
  stepStatuses: PipelineStepStatus[];
  progressPercent: number;
  streaming: boolean;
  streamError: string | null;
};

function parseSseChunk(buffer: string): { payloads: LensStreamPayload[]; rest: string } {
  const payloads: LensStreamPayload[] = [];
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";

  for (const part of parts) {
    const line = part
      .split("\n")
      .find((row) => row.startsWith("data:"));
    if (!line) continue;
    const json = line.replace(/^data:\s*/, "").trim();
    if (!json) continue;
    try {
      payloads.push(JSON.parse(json) as LensStreamPayload);
    } catch {
      // ignore malformed chunks
    }
  }

  return { payloads, rest };
}

export function useLensStream({
  queryId,
  accessToken,
  enabled,
  onComplete,
  onError,
}: UseLensStreamOptions): UseLensStreamResult {
  const [stepStatuses, setStepStatuses] = useState(initialPipelineStepStatuses);
  const [streaming, setStreaming] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
  }, [onComplete, onError]);

  const connect = useCallback(async (signal: AbortSignal) => {
    if (!queryId || !accessToken) return;

    setStreaming(true);
    setStreamError(null);
    setStepStatuses(initialPipelineStepStatuses());

    const base = getApiBaseUrl();
    const url = `${base}/api/lens/queries/${queryId}/stream`;

    try {
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${accessToken}` },
        cache: "no-store",
        signal,
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(text || `Stream failed (${res.status})`);
      }

      if (!res.body) {
        throw new Error("Stream body unavailable");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const { payloads, rest } = parseSseChunk(buffer);
        buffer = rest;

        for (const payload of payloads) {
          if (payload.event === "step") {
            setStepStatuses((prev) => applyStreamStep(prev, payload));
          } else if (payload.event === "complete") {
            setStepStatuses((prev) => prev.map(() => "done" as const));
            onCompleteRef.current(payload.card_id);
          } else if (payload.event === "error") {
            setStreamError(payload.message);
            onErrorRef.current(payload.message);
          }
        }
      }
    } catch (error) {
      if (signal.aborted) return;
      const message =
        error instanceof Error ? error.message : "Lens stream disconnected.";
      setStreamError(message);
      onErrorRef.current(message);
    } finally {
      if (!signal.aborted) {
        setStreaming(false);
      }
    }
  }, [accessToken, queryId]);

  useEffect(() => {
    if (!enabled || !queryId || !accessToken) {
      setStreaming(false);
      return undefined;
    }

    const controller = new AbortController();
    void connect(controller.signal);
    return () => controller.abort();
  }, [accessToken, connect, enabled, queryId]);

  return {
    stepStatuses,
    progressPercent: progressPercentFromSteps(stepStatuses),
    streaming,
    streamError,
  };
}
