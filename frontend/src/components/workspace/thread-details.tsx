"use client";

import {
  ActivityIcon,
  AlertTriangleIcon,
  BoxIcon,
  BotIcon,
  ChevronDownIcon,
  ClockIcon,
  CodeIcon,
  DownloadIcon,
  FileJsonIcon,
  FileTextIcon,
  FilesIcon,
  GitBranchIcon,
  ListTreeIcon,
  RefreshCwIcon,
  SquareIcon,
  SquareXIcon,
  UserIcon,
  WrenchIcon,
} from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArtifactFileList } from "@/components/workspace/artifacts/artifact-file-list";
import { useArtifacts } from "@/components/workspace/artifacts/context";
import { Tooltip } from "@/components/workspace/tooltip";
import {
  cancelThreadRun,
  type WorkflowNode,
  type WorkflowSnapshot,
} from "@/core/api/runs";
import { useI18n } from "@/core/i18n/hooks";
import { formatTokenCount } from "@/core/messages/usage";
import {
  downloadAsFile,
  exportThreadAsJSON,
  exportThreadAsMarkdown,
} from "@/core/threads/export";
import type { AgentThread } from "@/core/threads/types";
import { useThreadWorkflow } from "@/core/workflow";
import { cn } from "@/lib/utils";

import { useThread } from "./messages/context";
import { StreamingIndicator } from "./streaming-indicator";

type ThreadDetailsTriggerProps = {
  threadId: string;
  currentRunId?: string | null;
  streaming: boolean;
};

function formatTime(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatDuration(start?: string | null, end?: string | null) {
  if (!start || !end) return "—";
  const startTime = Date.parse(start);
  const endTime = Date.parse(end);
  if (Number.isNaN(startTime) || Number.isNaN(endTime)) return "—";
  const seconds = Math.max(0, Math.round((endTime - startTime) / 1000));
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${seconds % 60}s`;
}

function getNodeIcon(kind: WorkflowNode["kind"]) {
  switch (kind) {
    case "user":
      return UserIcon;
    case "tool":
      return WrenchIcon;
    case "subagent":
      return GitBranchIcon;
    case "artifact":
      return FilesIcon;
    case "checkpoint":
      return BoxIcon;
    case "error":
      return AlertTriangleIcon;
    case "final":
      return SquareIcon;
    case "agent":
      return BotIcon;
    default:
      return ActivityIcon;
  }
}

function statusLabel(status?: string) {
  switch (status) {
    case "pending":
      return "Pending";
    case "running":
      return "Running";
    case "success":
      return "Complete";
    case "error":
      return "Error";
    case "interrupted":
      return "Interrupted";
    default:
      return status ?? "Unknown";
  }
}

function WorkflowTimeline({
  workflow,
  onOpenArtifact,
}: {
  workflow?: WorkflowSnapshot;
  onOpenArtifact: (filepath: string) => void;
}) {
  if (!workflow || workflow.nodes.length === 0) {
    return (
      <EmptyDetailsState
        icon={<ListTreeIcon />}
        title="No workflow events yet"
        description="The run is registered, but no visible agent event has been recorded yet."
      />
    );
  }

  return (
    <div className="space-y-3">
      {workflow.nodes.map((node, index) => {
        const Icon = getNodeIcon(node.kind);
        const isLast = index === workflow.nodes.length - 1;
        return (
          <div key={node.id} className="relative flex gap-3">
            {!isLast && (
              <div className="bg-border absolute top-8 left-4 h-[calc(100%-1rem)] w-px" />
            )}
            <div
              className={cn(
                "bg-background z-1 flex size-8 shrink-0 items-center justify-center rounded-full border",
                node.status === "error" && "border-destructive/50 text-destructive",
                node.status === "running" && "border-primary/50 text-primary",
              )}
            >
              <Icon className="size-4" />
            </div>
            <Collapsible className="min-w-0 flex-1 rounded-md border p-3">
              <CollapsibleTrigger className="group flex w-full min-w-0 cursor-pointer items-start justify-between gap-3 text-left">
                <div className="min-w-0">
                  <div className="flex min-w-0 items-center gap-2">
                    <span className="truncate text-sm font-medium">{node.label}</span>
                    <Badge variant="outline" className="text-[10px]">
                      {node.kind}
                    </Badge>
                  </div>
                  <div className="text-muted-foreground mt-1 line-clamp-2 text-xs">
                    {node.summary || "No summary available."}
                  </div>
                </div>
                <div className="text-muted-foreground flex shrink-0 items-center gap-2 text-xs">
                  <span>{formatTime(node.created_at)}</span>
                  <ChevronDownIcon className="size-3 transition-transform group-data-[state=open]:rotate-180" />
                </div>
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-3 space-y-2 border-t pt-3 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <DetailKV label="Status" value={statusLabel(node.status)} />
                  <DetailKV label="Caller" value={node.caller ?? "—"} />
                  <DetailKV label="Seq" value={node.seq?.toString() ?? "—"} />
                  <DetailKV
                    label="Event"
                    value={
                      typeof node.metadata?.event_type === "string"
                        ? node.metadata.event_type
                        : "—"
                    }
                  />
                </div>
                {node.artifact_path && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => onOpenArtifact(node.artifact_path!)}
                  >
                    <FilesIcon className="size-4" />
                    {node.artifact_path}
                  </Button>
                )}
              </CollapsibleContent>
            </Collapsible>
          </div>
        );
      })}
    </div>
  );
}

function DetailKV({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-muted/50 p-2">
      <div className="text-muted-foreground text-[10px] uppercase">{label}</div>
      <div className="truncate font-mono text-xs">{value}</div>
    </div>
  );
}

function EmptyDetailsState({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="text-muted-foreground flex h-56 flex-col items-center justify-center rounded-lg border border-dashed p-6 text-center">
      <div className="mb-3 [&_svg]:size-8">{icon}</div>
      <div className="text-foreground text-sm font-medium">{title}</div>
      <div className="mt-1 max-w-xs text-xs leading-5">{description}</div>
    </div>
  );
}

function RunSummary({
  workflow,
  active,
  streaming,
}: {
  workflow?: WorkflowSnapshot;
  active: boolean;
  streaming: boolean;
}) {
  const run = workflow?.run;
  const lastEventAt = run?.last_event_at ?? run?.updated_at;
  return (
    <div className="grid grid-cols-2 gap-2">
      <DetailKV label="Status" value={streaming ? "Streaming" : statusLabel(run?.status)} />
      <DetailKV label="Run" value={run?.run_id ?? "—"} />
      <DetailKV label="Last Event" value={formatTime(lastEventAt)} />
      <DetailKV label="Duration" value={formatDuration(run?.created_at, lastEventAt)} />
      {active && !streaming && (
        <div className="bg-primary/5 text-primary col-span-2 flex items-center gap-2 rounded-md border border-primary/20 p-2 text-xs">
          <StreamingIndicator size="sm" />
          Backend run is still active. The details panel is polling for new events.
        </div>
      )}
      {run?.error && (
        <div className="border-destructive/30 bg-destructive/5 text-destructive col-span-2 rounded-md border p-2 text-xs">
          {run.error}
        </div>
      )}
    </div>
  );
}

function exportWorkflow(workflow?: WorkflowSnapshot) {
  if (!workflow) return;
  downloadAsFile(
    JSON.stringify(workflow, null, 2),
    `workflow-${workflow.run.run_id}.json`,
    "application/json;charset=utf-8",
  );
}

export function ThreadDetailsTrigger({
  threadId,
  currentRunId,
  streaming,
}: ThreadDetailsTriggerProps) {
  const { t } = useI18n();
  const { thread } = useThread();
  const { artifacts, latestArtifact, setOpen: setArtifactsOpen, select } = useArtifacts();
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState("flow");
  const { workflow, run, active, isFetching, refetch } = useThreadWorkflow({
    threadId,
    currentRunId,
    enabled: open || streaming,
  });

  const messages = thread.messages;
  const artifactCount =
    workflow?.artifacts.length !== undefined && workflow.artifacts.length > 0
      ? workflow.artifacts.length
      : artifacts.length;
  const usage = workflow?.usage;

  const agentThread = useMemo(
    () =>
      ({
        thread_id: threadId,
        updated_at: new Date().toISOString(),
        values: thread.values,
      }) as AgentThread,
    [thread.values, threadId],
  );

  const openArtifact = useCallback(
    (filepath: string) => {
      select(filepath);
      setArtifactsOpen(true);
    },
    [select, setArtifactsOpen],
  );

  const handleExportThread = useCallback(
    (format: "markdown" | "json") => {
      if (messages.length === 0) {
        toast.error(t.conversation.noMessages);
        return;
      }
      if (format === "markdown") {
        exportThreadAsMarkdown(agentThread, messages);
      } else {
        exportThreadAsJSON(agentThread, messages);
      }
      toast.success(t.common.exportSuccess);
    },
    [agentThread, messages, t],
  );

  const handleCancelRun = useCallback(async () => {
    const runId = run?.run_id ?? currentRunId;
    if (!runId) return;
    try {
      await cancelThreadRun(threadId, runId);
      await refetch();
      toast.success("已请求停止当前任务");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "停止任务失败");
    }
  }, [currentRunId, refetch, run?.run_id, threadId]);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <Tooltip content="查看工作流、文件、导出和运行日志">
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            className="text-muted-foreground hover:text-foreground relative"
            data-testid="thread-details-trigger"
          >
            {(streaming || active) && (
              <span className="bg-primary absolute top-1.5 left-1.5 size-2 rounded-full">
                <span className="bg-primary absolute inset-0 animate-ping rounded-full opacity-50" />
              </span>
            )}
            <ActivityIcon />
            详情
            {artifactCount > 0 && (
              <Badge variant="secondary" className="h-5 min-w-5 px-1.5 text-[10px]">
                {artifactCount}
              </Badge>
            )}
          </Button>
        </SheetTrigger>
      </Tooltip>
      <SheetContent className="w-[92vw] gap-0 p-0 sm:max-w-xl">
        <SheetHeader className="border-b pr-12">
          <div className="flex items-center justify-between gap-3">
            <div>
              <SheetTitle>详情</SheetTitle>
              <SheetDescription>
                Agent 工作流、工具调用、产出文件与运行日志
              </SheetDescription>
            </div>
            <Button size="icon-sm" variant="ghost" onClick={() => void refetch()}>
              <RefreshCwIcon className={cn("size-4", isFetching && "animate-spin")} />
            </Button>
          </div>
        </SheetHeader>
        <Tabs value={tab} onValueChange={setTab} className="min-h-0 flex-1 gap-0">
          <div className="border-b px-4 py-2">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="flow" onClick={() => setTab("flow")}>
                流程
              </TabsTrigger>
              <TabsTrigger value="files" onClick={() => setTab("files")}>
                产出
              </TabsTrigger>
              <TabsTrigger value="stats" onClick={() => setTab("stats")}>
                统计
              </TabsTrigger>
              <TabsTrigger value="export" onClick={() => setTab("export")}>
                导出
              </TabsTrigger>
              <TabsTrigger value="logs" onClick={() => setTab("logs")}>
                日志
              </TabsTrigger>
            </TabsList>
          </div>

          <ScrollArea className="min-h-0 flex-1">
            <div className="p-4">
              <TabsContent value="flow" className="mt-0 space-y-4">
                <RunSummary workflow={workflow} active={active} streaming={streaming} />
                <WorkflowTimeline workflow={workflow} onOpenArtifact={openArtifact} />
              </TabsContent>

              <TabsContent value="files" className="mt-0">
                {artifactCount > 0 ? (
                  <ArtifactFileList
                    files={artifacts.length > 0 ? artifacts : workflow?.artifacts.map((item) => item.filepath) ?? []}
                    threadId={threadId}
                    latestFilepath={latestArtifact ?? workflow?.artifacts[0]?.filepath}
                    onRefresh={() => void refetch()}
                  />
                ) : (
                  <EmptyDetailsState
                    icon={<FilesIcon />}
                    title="暂无产出文件"
                    description="当 agent 生成 PDF、表格、图片或代码文件后，会显示在这里。"
                  />
                )}
              </TabsContent>

              <TabsContent value="stats" className="mt-0 space-y-4">
                <RunSummary workflow={workflow} active={active} streaming={streaming} />
                {(active || streaming) && (
                  <Button
                    className="w-full justify-start"
                    variant="outline"
                    onClick={() => void handleCancelRun()}
                  >
                    <SquareXIcon className="size-4" />
                    停止当前任务
                  </Button>
                )}
                <div className="grid grid-cols-3 gap-2">
                  <DetailKV label={t.tokenUsage.input} value={formatTokenCount(usage?.input_tokens ?? 0)} />
                  <DetailKV label={t.tokenUsage.output} value={formatTokenCount(usage?.output_tokens ?? 0)} />
                  <DetailKV label={t.tokenUsage.total} value={formatTokenCount(usage?.total_tokens ?? 0)} />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <DetailKV label="Events" value={String(workflow?.events.length ?? 0)} />
                  <DetailKV label="Artifacts" value={String(artifactCount)} />
                </div>
              </TabsContent>

              <TabsContent value="export" className="mt-0 space-y-3">
                <Button className="w-full justify-start" variant="outline" onClick={() => handleExportThread("markdown")}>
                  <FileTextIcon className="size-4" />
                  {t.common.exportAsMarkdown}
                </Button>
                <Button className="w-full justify-start" variant="outline" onClick={() => handleExportThread("json")}>
                  <FileJsonIcon className="size-4" />
                  {t.common.exportAsJSON}
                </Button>
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  disabled={!workflow}
                  onClick={() => exportWorkflow(workflow)}
                >
                  <DownloadIcon className="size-4" />
                  导出运行轨迹 JSON
                </Button>
              </TabsContent>

              <TabsContent value="logs" className="mt-0">
                {workflow?.events.length ? (
                  <div className="space-y-2">
                    {workflow.events.map((event) => (
                      <Collapsible key={event.seq} className="rounded-md border p-3">
                        <CollapsibleTrigger className="group flex w-full cursor-pointer items-start justify-between gap-3 text-left">
                          <div className="min-w-0">
                            <div className="flex items-center gap-2 text-sm font-medium">
                              <CodeIcon className="size-4" />
                              <span>#{event.seq}</span>
                              <span>{event.event_type}</span>
                            </div>
                            <div className="text-muted-foreground mt-1 line-clamp-2 text-xs">{event.summary}</div>
                          </div>
                          <div className="text-muted-foreground flex shrink-0 items-center gap-2 text-xs">
                            <ClockIcon className="size-3" />
                            {formatTime(event.created_at)}
                          </div>
                        </CollapsibleTrigger>
                        <CollapsibleContent className="mt-3 overflow-hidden rounded-md bg-muted/50 p-2">
                          <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words text-xs">
                            {JSON.stringify(event.content, null, 2)}
                          </pre>
                        </CollapsibleContent>
                      </Collapsible>
                    ))}
                  </div>
                ) : (
                  <EmptyDetailsState
                    icon={<CodeIcon />}
                    title="暂无运行日志"
                    description="运行开始后，工具调用、子任务、文件产出和状态事件会逐步记录。"
                  />
                )}
              </TabsContent>
            </div>
          </ScrollArea>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}
