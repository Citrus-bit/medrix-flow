"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangleIcon, CircleStopIcon } from "lucide-react";

import { listThreadRuns } from "@/core/api/runs";
import { useI18n } from "@/core/i18n/hooks";
import { isRunActive, resolveThreadRun } from "@/core/runs/status";
import type { ModelRetryStatus } from "@/core/threads/hooks";
import { cn } from "@/lib/utils";

import { StreamingIndicator } from "./streaming-indicator";

function formatUpdatedAt(value?: string): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function RunStatusIndicator({
  className,
  threadId,
  currentRunId,
  streaming,
  modelRetryStatus,
}: {
  className?: string;
  threadId: string;
  currentRunId?: string | null;
  streaming: boolean;
  modelRetryStatus?: ModelRetryStatus | null;
}) {
  const { t } = useI18n();
  const { data: runs } = useQuery({
    queryKey: ["thread-runs", threadId],
    queryFn: () => listThreadRuns(threadId),
    enabled: Boolean(threadId),
    refetchInterval: 5000,
    staleTime: 1000,
    retry: 1,
  });

  const run = resolveThreadRun(runs, currentRunId);
  const status = run?.status;
  const active = isRunActive(run);
  const showRetry = streaming && Boolean(modelRetryStatus);
  const showError = Boolean(currentRunId) && !streaming && status === "error";
  const showInterrupted = Boolean(currentRunId) && !streaming && status === "interrupted";

  if (!streaming && !active && !showError && !showInterrupted && !showRetry) {
    return null;
  }

  const label = showRetry && modelRetryStatus
    ? t.runStatus.modelRetrying(
        modelRetryStatus.attempt,
        Math.ceil(modelRetryStatus.delaySeconds),
      )
    : streaming
    ? t.runStatus.running
    : active
      ? t.runStatus.reconnecting
      : showError
        ? t.runStatus.error
        : t.runStatus.interrupted;
  const updatedAt = formatUpdatedAt(run?.updated_at);

  return (
    <div
      className={cn(
        "text-muted-foreground flex items-center gap-2 text-xs",
        className,
      )}
      data-testid="run-status-indicator"
    >
      {showError ? (
        <AlertTriangleIcon className="size-3.5 text-amber-500" />
      ) : showInterrupted ? (
        <CircleStopIcon className="size-3.5" />
      ) : (
        <StreamingIndicator size="sm" />
      )}
      <span>{label}</span>
      {updatedAt && <span className="opacity-70">{t.runStatus.lastEvent(updatedAt)}</span>}
    </div>
  );
}
