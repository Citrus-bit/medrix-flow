import { DownloadIcon, LoaderIcon, PackageIcon, RefreshCwIcon } from "lucide-react";
import { useCallback, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { urlOfArtifact } from "@/core/artifacts/utils";
import { useI18n } from "@/core/i18n/hooks";
import { installSkill } from "@/core/skills/api";
import {
  getFileExtensionDisplayName,
  getFileIcon,
  getFileName,
} from "@/core/utils/files";
import { cn } from "@/lib/utils";

import { useArtifacts } from "./context";

export function ArtifactFileList({
  className,
  files,
  threadId,
  latestFilepath,
  onRefresh,
}: {
  className?: string;
  files: string[];
  threadId: string;
  latestFilepath?: string | null;
  onRefresh?: () => void | Promise<unknown>;
}) {
  const { t } = useI18n();
  const { select: selectArtifact, setOpen } = useArtifacts();
  const [installingFile, setInstallingFile] = useState<string | null>(null);
  const [refreshFeedbackActive, setRefreshFeedbackActive] = useState(false);
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);

  const handleClick = useCallback(
    (filepath: string) => {
      selectArtifact(filepath);
      setOpen(true);
    },
    [selectArtifact, setOpen],
  );

  const handleInstallSkill = useCallback(
    async (e: React.MouseEvent, filepath: string) => {
      e.stopPropagation();
      e.preventDefault();

      if (installingFile) return;

      setInstallingFile(filepath);
      try {
        const result = await installSkill({
          thread_id: threadId,
          path: filepath,
        });
        if (result.success) {
          toast.success(result.message);
        } else {
          toast.error(result.message || "Failed to install skill");
        }
      } catch (error) {
        console.error("Failed to install skill:", error);
        toast.error("Failed to install skill");
      } finally {
        setInstallingFile(null);
      }
    },
    [threadId, installingFile],
  );

  const handleRefreshClick = useCallback(async () => {
    if (!onRefresh || isManualRefreshing) {
      return;
    }

    setRefreshFeedbackActive(true);
    setIsManualRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsManualRefreshing(false);
      window.setTimeout(() => {
        setRefreshFeedbackActive(false);
      }, 220);
    }
  }, [isManualRefreshing, onRefresh]);

  return (
    <ul className={cn("flex w-full flex-col gap-4", className)}>
      <li className="flex justify-end">
        <Button
          className={cn(
            "transition-all duration-150 active:scale-95",
            refreshFeedbackActive &&
              "border-primary/35 bg-primary/8 text-primary shadow-[0_0_0_3px_rgba(8,145,178,0.08)]",
          )}
          variant="outline"
          size="sm"
          onClick={handleRefreshClick}
          disabled={!onRefresh || isManualRefreshing}
        >
          <RefreshCwIcon
            className={cn(
              "size-4 transition-transform duration-150",
              refreshFeedbackActive && "scale-90",
              isManualRefreshing && "animate-spin",
            )}
          />
          {t.common.refresh}
        </Button>
      </li>
      {files.map((file) => (
        <Card
          key={file}
          className={cn(
            "relative cursor-pointer p-3",
            file === latestFilepath &&
              "ring-primary/40 bg-primary/5 border-primary/30 ring-1",
          )}
          onClick={() => handleClick(file)}
        >
          <CardHeader className="pr-2 pl-1">
            <CardTitle className="relative pl-8">
              <div className="flex items-center gap-2">
                <span>{getFileName(file)}</span>
                {file === latestFilepath && (
                  <span className="bg-primary/10 text-primary rounded-full px-2 py-0.5 text-[10px] font-medium">
                    {t.common.latest}
                  </span>
                )}
              </div>
              <div className="absolute top-2 -left-0.5">
                {getFileIcon(file, "size-6")}
              </div>
            </CardTitle>
            <CardDescription className="pl-8 text-xs">
              {getFileExtensionDisplayName(file)} file
            </CardDescription>
            <CardAction className="flex items-center gap-1 self-center">
              {file.endsWith(".skill") && (
                <Button
                  variant="ghost"
                  disabled={installingFile === file}
                  onClick={(e) => handleInstallSkill(e, file)}
                >
                  {installingFile === file ? (
                    <LoaderIcon className="size-4 animate-spin" />
                  ) : (
                    <PackageIcon className="size-4" />
                  )}
                  {t.common.install}
                </Button>
              )}
              <Button
                asChild
                variant="ghost"
                size="icon-sm"
                className="text-muted-foreground hover:text-foreground rounded-full"
              >
                <a
                  href={urlOfArtifact({
                    filepath: file,
                    threadId: threadId,
                    download: true,
                  })}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={t.common.download}
                  title={t.common.download}
                  onClick={(e) => e.stopPropagation()}
                >
                  <DownloadIcon className="size-4" />
                </a>
              </Button>
            </CardAction>
          </CardHeader>
        </Card>
      ))}
    </ul>
  );
}
