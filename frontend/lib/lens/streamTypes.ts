export type LensStreamStepPayload = {
  event: "step";
  index: number;
  name: string;
  status: "active" | "done";
};

export type LensStreamCompletePayload = {
  event: "complete";
  card_id: string;
};

export type LensStreamErrorPayload = {
  event: "error";
  message: string;
};

export type LensStreamPayload =
  | LensStreamStepPayload
  | LensStreamCompletePayload
  | LensStreamErrorPayload;

export type PipelineStepStatus = "pending" | "active" | "done";

export function initialPipelineStepStatuses(): PipelineStepStatus[] {
  return ["pending", "pending", "pending", "pending", "pending", "pending"];
}

export function applyStreamStep(
  statuses: PipelineStepStatus[],
  payload: LensStreamStepPayload,
): PipelineStepStatus[] {
  const next = [...statuses];
  if (payload.status === "active") {
    next[payload.index] = "active";
    for (let i = 0; i < payload.index; i += 1) {
      if (next[i] !== "done") next[i] = "done";
    }
    return next;
  }
  next[payload.index] = "done";
  return next;
}

export function progressPercentFromSteps(statuses: PipelineStepStatus[]): number {
  const doneCount = statuses.filter((s) => s === "done").length;
  const hasActive = statuses.some((s) => s === "active");
  const base = (doneCount / statuses.length) * 100;
  return hasActive ? Math.min(99, base + 100 / statuses.length / 2) : base;
}
