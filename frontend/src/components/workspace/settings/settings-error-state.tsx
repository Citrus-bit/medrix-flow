"use client";

import { AlertTriangleIcon, RefreshCwIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useI18n } from "@/core/i18n/hooks";

export function SettingsErrorState({
  error,
  onRetry,
}: {
  error: Error;
  onRetry?: () => void;
}) {
  const { t } = useI18n();
  const isTimeout = error.message.includes("timed out") || error.message.includes("Failed to fetch");

  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-900 dark:bg-red-950/30">
      <AlertTriangleIcon className="size-8 text-red-500" />
      <p className="text-sm font-medium text-red-800 dark:text-red-300">
        {isTimeout ? t.common.backendUnavailable : error.message}
      </p>
      <p className="text-muted-foreground max-w-md text-center text-xs">
        {isTimeout ? t.common.backendUnavailableHint : t.common.backendUnavailableHint}
      </p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCwIcon className="size-3.5" />
          {t.common.retryNow}
        </Button>
      )}
    </div>
  );
}
