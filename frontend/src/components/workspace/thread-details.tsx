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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArtifactFileList } from "@/components/workspace/artifacts/artifact-file-list";
import { useArtifacts } from "@/components/workspace/artifacts/context";
import { Tooltip } from "@/components/workspace/tooltip";
import {
  cancelThreadRun,
  type WorkflowEvent,
  type WorkflowNode,
  type WorkflowSnapshot,
} from "@/core/api/runs";
import type { Locale, Translations } from "@/core/i18n";
import { useI18n } from "@/core/i18n/hooks";
import { accumulateUsage, formatTokenCount } from "@/core/messages/usage";
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

type ThreadDetailsCopy = Translations["threadDetails"];

function formatTime(value?: string | null, locale?: Locale) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString(locale, {
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

function formatDateTime(value?: string | null, locale?: Locale) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(locale);
}

function formatMaybeTokens(
  value: number | null | undefined,
  unrecordedLabel: string,
) {
  if (!value || value <= 0) return unrecordedLabel;
  return formatTokenCount(value);
}

function workflowStepName(value: unknown) {
  if (typeof value !== "string" || !value.trim()) return null;
  const raw = value.trim();
  const lowered = raw.toLowerCase();
  if (lowered.includes("academic_research")) return "academic_research";
  if (lowered.includes("dataset_benchmark")) return "dataset_benchmark_discovery";
  if (lowered.includes("experiment_lab")) return "experiment_lab";
  if (lowered.includes("manuscript_export")) return "manuscript_export";
  if (lowered.includes("task") || lowered.includes("subagent")) return "subagent";
  if (["ai", "tool", "human"].includes(lowered)) return null;
  return raw;
}

function workflowToolCallName(content: Record<string, unknown>) {
  const toolCalls = content.tool_calls;
  if (!Array.isArray(toolCalls)) return null;
  for (const toolCall of toolCalls) {
    if (typeof toolCall !== "object" || toolCall === null) continue;
    const name = Reflect.get(toolCall, "name");
    const label = workflowStepName(name);
    if (label) return label;
  }
  return null;
}

function workflowEventStepLabel(event: WorkflowEvent) {
  const content = event.content;
  const candidates = [
    workflowToolCallName(content),
    content.tool_name,
    content.name,
    event.caller,
    event.event_type,
    content.type,
  ];
  for (const candidate of candidates) {
    const label = workflowStepName(candidate);
    if (label) return label;
  }
  return event.summary || event.event_type;
}

function getSlowStepSummary(workflow?: WorkflowSnapshot) {
  const events = workflow?.events.filter((event) => !isEmptySubagentHeartbeat(event)) ?? [];
  if (!workflow || events.length === 0) return [];
  const runEnd =
    workflow.run.status === "pending" || workflow.run.status === "running"
      ? new Date().toISOString()
      : (workflow.run.last_event_at ?? workflow.run.updated_at);
  const totals = new Map<string, { durationMs: number; eventCount: number }>();

  for (let index = 0; index < events.length; index += 1) {
    const event = events[index];
    if (!event) continue;
    const start = Date.parse(event.created_at);
    const nextCreatedAt = events[index + 1]?.created_at ?? runEnd;
    const end = nextCreatedAt ? Date.parse(nextCreatedAt) : Number.NaN;
    if (Number.isNaN(start) || Number.isNaN(end) || end <= start) continue;

    const label = workflowEventStepLabel(event);
    const current = totals.get(label) ?? { durationMs: 0, eventCount: 0 };
    current.durationMs += end - start;
    current.eventCount += 1;
    totals.set(label, current);
  }

  return [...totals.entries()]
    .map(([label, value]) => ({
      label,
      duration: formatDuration(
        new Date(0).toISOString(),
        new Date(value.durationMs).toISOString(),
      ),
      eventCount: value.eventCount,
      durationMs: value.durationMs,
    }))
    .filter((item) => item.durationMs > 0)
    .sort((left, right) => right.durationMs - left.durationMs)
    .slice(0, 5);
}

function isEmptySubagentHeartbeat(event: WorkflowEvent) {
  if (event.event_type !== "subagent_event") return false;
  if (event.content.heartbeat !== true) return false;
  const content = event.content.content;
  return (
    content === undefined ||
    content === null ||
    content === "" ||
    content === '""'
  );
}

function getNodeIcon(kind: WorkflowNode["kind"]) {
  switch (kind) {
    case "user":
      return UserIcon;
    case "decision":
      return GitBranchIcon;
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

function nodeKindLabel(kind: WorkflowNode["kind"], copy: ThreadDetailsCopy) {
  switch (kind) {
    case "decision":
      return copy.nodeKinds.decision;
    case "user":
      return copy.nodeKinds.user;
    case "agent":
      return copy.nodeKinds.agent;
    case "subagent":
      return copy.nodeKinds.subagent;
    case "tool":
      return copy.nodeKinds.tool;
    case "artifact":
      return copy.nodeKinds.artifact;
    case "checkpoint":
      return copy.nodeKinds.checkpoint;
    case "final":
      return copy.nodeKinds.final;
    case "error":
      return copy.nodeKinds.error;
    default:
      return copy.nodeKinds.event;
  }
}

function statusLabel(status: string | undefined, labels: ThreadDetailsCopy["status"]) {
  switch (status) {
    case "pending":
      return labels.pending;
    case "running":
      return labels.running;
    case "success":
      return labels.success;
    case "error":
      return labels.error;
    case "interrupted":
      return labels.interrupted;
    default:
      return status ?? labels.unknown;
  }
}

type TreeNode = WorkflowNode & { children: TreeNode[] };

function metadataString(metadata: Record<string, unknown>, key: string) {
  const value = metadata[key];
  return typeof value === "string" ? value : "";
}

function metadataStringList(metadata: Record<string, unknown>, key: string) {
  const value = metadata[key];
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string" && item.length > 0);
}

function buildWorkflowTree(workflow: WorkflowSnapshot): TreeNode[] {
  if (workflow.nodes.length > 0 && workflow.edges.length === 0) {
    const chain: TreeNode[] = workflow.nodes.map((node) => ({
      ...node,
      children: [],
    }));
    for (let index = 0; index < chain.length - 1; index += 1) {
      chain[index]?.children.push(chain[index + 1]!);
    }
    return chain[0] ? [chain[0]] : [];
  }

  const nodesById = new Map<string, TreeNode>(
    workflow.nodes.map((node) => [node.id, { ...node, children: [] as TreeNode[] }]),
  );
  const childIds = new Set<string>();

  for (const edge of workflow.edges) {
    const source = nodesById.get(edge.source);
    const target = nodesById.get(edge.target);
    if (!source || !target) continue;
    source.children.push(target);
    childIds.add(target.id);
  }

  const roots = [...nodesById.values()].filter((node) => !childIds.has(node.id));
  if (roots.length > 0) {
    return roots;
  }

  const chain: TreeNode[] = workflow.nodes.map((node) => ({ ...node, children: [] }));
  for (let index = 0; index < chain.length - 1; index += 1) {
    chain[index]?.children.push(chain[index + 1]!);
  }
  return chain[0] ? [chain[0]] : [];
}

function WorkflowTreeNode({
  node,
  depth,
  onOpenArtifact,
  copy,
  locale,
}: {
  node: TreeNode;
  depth: number;
  onOpenArtifact: (filepath: string) => void;
  copy: ThreadDetailsCopy;
  locale: Locale;
}) {
  const Icon = getNodeIcon(node.kind);
  const isDecision = node.kind === "decision";
  const rationale = metadataString(node.metadata, "rationale");
  const nextStep = metadataString(node.metadata, "next_step");
  const outcome = metadataString(node.metadata, "outcome");
  const alternatives = metadataStringList(node.metadata, "alternatives");
  return (
    <div className={cn(depth > 0 && "border-l pl-4")}>
      <div className="relative flex min-w-0 gap-3">
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
            <div className="min-w-0 flex-1 overflow-hidden">
              <div className="flex min-w-0 items-center gap-2 overflow-hidden">
                <span className="min-w-0 truncate text-sm font-medium">{node.label}</span>
                <Badge variant="outline" className="shrink-0 text-[10px]">
                  {nodeKindLabel(node.kind, copy)}
                </Badge>
              </div>
              <div className="text-muted-foreground mt-1 line-clamp-2 min-w-0 break-words text-xs">
                {node.summary || copy.noSummary}
              </div>
            </div>
            <div className="text-muted-foreground flex shrink-0 items-center gap-2 text-xs">
              <span>{formatTime(node.created_at, locale)}</span>
              <ChevronDownIcon className="size-3 transition-transform group-data-[state=open]:rotate-180" />
            </div>
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-3 space-y-2 border-t pt-3 text-xs">
            {isDecision ? (
              <>
                <div className="grid grid-cols-2 gap-2">
                  <DetailKV
                    label={copy.labels.status}
                    value={statusLabel(node.status, copy.status)}
                  />
                  <DetailKV
                    label={copy.labels.decisionType}
                    value={metadataString(node.metadata, "decision_type") || "—"}
                  />
                  <DetailKV
                    label={copy.labels.relatedTool}
                    value={metadataString(node.metadata, "related_tool") || "—"}
                  />
                  <DetailKV
                    label={copy.labels.seq}
                    value={node.seq?.toString() ?? "—"}
                  />
                </div>
                <DetailBlock
                  label={copy.labels.rationale}
                  value={rationale || copy.noSummary}
                />
                <DetailBlock
                  label={copy.labels.nextStep}
                  value={nextStep || copy.noSummary}
                />
                {outcome && (
                  <DetailBlock label={copy.labels.outcome} value={outcome} />
                )}
                {alternatives.length > 0 && (
                  <DetailBlock
                    label={copy.labels.alternatives}
                    value={alternatives.join("\n")}
                  />
                )}
              </>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <DetailKV
                  label={copy.labels.status}
                  value={statusLabel(node.status, copy.status)}
                />
                <DetailKV label={copy.labels.caller} value={node.caller ?? "—"} />
                <DetailKV label={copy.labels.seq} value={node.seq?.toString() ?? "—"} />
                <DetailKV
                  label={copy.labels.event}
                  value={
                    typeof node.metadata?.event_type === "string"
                      ? node.metadata.event_type
                      : "—"
                  }
                />
              </div>
            )}
            {node.artifact_path && (
              <button
                type="button"
                className="hover:bg-muted flex w-full min-w-0 items-start gap-2 rounded-md border p-2 text-left"
                onClick={() => onOpenArtifact(node.artifact_path!)}
              >
                <FilesIcon className="mt-0.5 size-4 shrink-0" />
                <span
                  className="min-w-0 break-all font-mono text-xs"
                  data-testid="workflow-artifact-path"
                >
                  {node.artifact_path}
                </span>
              </button>
            )}
          </CollapsibleContent>
        </Collapsible>
      </div>
      {node.children.length > 0 && (
        <div className="mt-3 space-y-3 pl-4">
          {node.children.map((child) => (
            <WorkflowTreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              onOpenArtifact={onOpenArtifact}
              copy={copy}
              locale={locale}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function WorkflowTree({
  workflow,
  onOpenArtifact,
  copy,
  locale,
}: {
  workflow?: WorkflowSnapshot;
  onOpenArtifact: (filepath: string) => void;
  copy: ThreadDetailsCopy;
  locale: Locale;
}) {
  if (!workflow) {
    return (
      <EmptyDetailsState
        icon={<ListTreeIcon />}
        title={copy.noWorkflowEventsTitle}
        description={copy.noWorkflowEventsDescription}
      />
    );
  }

  const tree = buildWorkflowTree(workflow);

  return (
    <div className="space-y-3">
      <div className="rounded-md border bg-muted/20 p-3">
        <div className="flex min-w-0 items-start gap-3">
          <div className="bg-background flex size-8 shrink-0 items-center justify-center rounded-full border">
            <BotIcon className="size-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-medium">{copy.taskRun}</div>
            <div className="text-muted-foreground mt-1 break-all font-mono text-xs">
              {workflow.run.run_id}
            </div>
          </div>
          <Badge variant="outline" className="shrink-0 text-[10px]">
            {statusLabel(workflow.run.status, copy.status)}
          </Badge>
        </div>
      </div>
      {tree.map((node) => (
        <WorkflowTreeNode
          key={node.id}
          node={node}
          depth={0}
          onOpenArtifact={onOpenArtifact}
          copy={copy}
          locale={locale}
        />
      ))}
      {tree.length === 0 && (
        <EmptyDetailsState
          icon={<ListTreeIcon />}
          title={copy.noWorkflowTitle}
          description={copy.noWorkflowDescription}
        />
      )}
    </div>
  );
}

function DetailKV({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-muted/50 p-2">
      <div className="text-muted-foreground text-[10px] uppercase">{label}</div>
      <div className="min-w-0 break-words font-mono text-xs">{value}</div>
    </div>
  );
}

function DetailBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-muted/50 p-2">
      <div className="text-muted-foreground text-[10px] uppercase">{label}</div>
      <div className="mt-1 min-w-0 whitespace-pre-wrap break-words text-xs leading-5">
        {value}
      </div>
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

function StatsSection({
  workflow,
  active,
  streaming,
  threadUsage,
  threadDuration,
  artifactCount,
  eventCount,
  onCancelRun,
}: {
  workflow?: WorkflowSnapshot;
  active: boolean;
  streaming: boolean;
  threadUsage: ReturnType<typeof accumulateUsage>;
  threadDuration: string;
  artifactCount: number;
  eventCount: number;
  onCancelRun: () => void;
}) {
  const { t, locale } = useI18n();
  const copy = t.threadDetails;
  const run = workflow?.run;
  const lastEventAt = run?.last_event_at ?? run?.updated_at;
  const usage = workflow?.usage;
  const slowSteps = useMemo(() => getSlowStepSummary(workflow), [workflow]);
  return (
    <div className="space-y-4">
      <section className="space-y-2">
        <div className="text-sm font-medium">{copy.currentRun}</div>
        <div className="grid grid-cols-2 gap-2">
          <DetailKV
            label={copy.labels.status}
            value={streaming ? copy.streaming : statusLabel(run?.status, copy.status)}
          />
          <DetailKV label={copy.labels.run} value={run?.run_id ?? "—"} />
          <DetailKV
            label={copy.labels.started}
            value={formatDateTime(run?.created_at, locale)}
          />
          <DetailKV
            label={copy.labels.lastEvent}
            value={formatDateTime(lastEventAt, locale)}
          />
          <DetailKV
            label={copy.labels.duration}
            value={formatDuration(run?.created_at, lastEventAt)}
          />
          <DetailKV label={copy.labels.events} value={String(eventCount)} />
          <DetailKV label={copy.labels.artifacts} value={String(artifactCount)} />
          <DetailKV
            label={t.tokenUsage.total}
            value={formatMaybeTokens(usage?.total_tokens, copy.unrecorded)}
          />
          <DetailKV
            label={t.tokenUsage.input}
            value={formatMaybeTokens(usage?.input_tokens, copy.unrecorded)}
          />
          <DetailKV
            label={t.tokenUsage.output}
            value={formatMaybeTokens(usage?.output_tokens, copy.unrecorded)}
          />
        </div>
        {(active || streaming) && (
          <Button
            className="w-full justify-start"
            variant="outline"
            onClick={onCancelRun}
          >
            <SquareXIcon className="size-4" />
            {copy.stopCurrentTask}
          </Button>
        )}
      </section>
      <section className="space-y-2">
        <div className="text-sm font-medium">{copy.slowSteps}</div>
        {slowSteps.length > 0 ? (
          <div className="space-y-2">
            {slowSteps.map((item) => (
              <div
                key={item.label}
                className="grid grid-cols-[minmax(0,1fr)_auto] gap-2 rounded-md bg-muted/50 p-2 text-xs"
              >
                <div className="min-w-0">
                  <div className="text-muted-foreground text-[10px] uppercase">
                    {copy.labels.step}
                  </div>
                  <div className="min-w-0 break-all font-mono">{item.label}</div>
                </div>
                <div className="text-right">
                  <div className="font-mono">{item.duration}</div>
                  <div className="text-muted-foreground">
                    {copy.eventCount(item.eventCount)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-muted-foreground rounded-md bg-muted/50 p-2 text-xs">
            {copy.noSlowSteps}
          </div>
        )}
      </section>
      <section className="space-y-2">
        <div className="text-sm font-medium">{copy.wholeThread}</div>
        <div className="grid grid-cols-2 gap-2">
          <DetailKV
            label={t.tokenUsage.total}
            value={formatMaybeTokens(threadUsage?.totalTokens, copy.unrecorded)}
          />
          <DetailKV
            label={t.tokenUsage.input}
            value={formatMaybeTokens(threadUsage?.inputTokens, copy.unrecorded)}
          />
          <DetailKV
            label={t.tokenUsage.output}
            value={formatMaybeTokens(threadUsage?.outputTokens, copy.unrecorded)}
          />
          <DetailKV label={copy.labels.totalDuration} value={threadDuration} />
        </div>
      </section>
    </div>
  );
}

function ExportMenu({
  workflow,
  onExportThread,
}: {
  workflow?: WorkflowSnapshot;
  onExportThread: (format: "markdown" | "json") => void;
}) {
  const { t } = useI18n();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" aria-label={t.common.export}>
          <DownloadIcon className="size-4" />
          {t.common.export}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onSelect={() => onExportThread("markdown")}>
          <FileTextIcon className="size-4" />
          {t.threadDetails.exportThreadMarkdown}
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => onExportThread("json")}>
          <FileJsonIcon className="size-4" />
          {t.threadDetails.exportThreadJSON}
        </DropdownMenuItem>
        <DropdownMenuItem
          disabled={!workflow}
          onSelect={() => exportWorkflow(workflow)}
        >
          <DownloadIcon className="size-4" />
          {t.threadDetails.exportWorkflowJSON}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
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
  const { t, locale } = useI18n();
  const copy = t.threadDetails;
  const run = workflow?.run;
  const lastEventAt = run?.last_event_at ?? run?.updated_at;
  return (
    <div className="grid grid-cols-2 gap-2">
      <DetailKV
        label={copy.labels.status}
        value={streaming ? copy.streaming : statusLabel(run?.status, copy.status)}
      />
      <DetailKV label={copy.labels.run} value={run?.run_id ?? "—"} />
      <DetailKV label={copy.labels.lastEvent} value={formatTime(lastEventAt, locale)} />
      <DetailKV
        label={copy.labels.duration}
        value={formatDuration(run?.created_at, lastEventAt)}
      />
      {active && !streaming && (
        <div className="bg-primary/5 text-primary col-span-2 flex items-center gap-2 rounded-md border border-primary/20 p-2 text-xs">
          <StreamingIndicator size="sm" />
          {copy.activeRunPolling}
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
  const { t, locale } = useI18n();
  const copy = t.threadDetails;
  const { thread } = useThread();
  const { artifacts, latestArtifact, setOpen: setArtifactsOpen, select } = useArtifacts();
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState("flow");
  const { workflow, run, runs, active, isFetching, refetch } = useThreadWorkflow({
    threadId,
    currentRunId,
    enabled: open,
  });

  const messages = thread.messages;
  const artifactCount =
    workflow?.artifacts.length !== undefined && workflow.artifacts.length > 0
      ? workflow.artifacts.length
      : artifacts.length;
  const threadUsage = useMemo(() => accumulateUsage(messages), [messages]);
  const visibleEvents = useMemo(
    () => workflow?.events.filter((event) => !isEmptySubagentHeartbeat(event)) ?? [],
    [workflow?.events],
  );
  const threadDuration = useMemo(() => {
    if (runs.length === 0) return "—";
    const timestamps = runs
      .flatMap((item) => [Date.parse(item.created_at), Date.parse(item.updated_at)])
      .filter((value) => !Number.isNaN(value));
    if (timestamps.length === 0) return "—";
    return formatDuration(
      new Date(Math.min(...timestamps)).toISOString(),
      new Date(Math.max(...timestamps)).toISOString(),
    );
  }, [runs]);
  const eventCount = visibleEvents.length;

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
      toast.success(copy.stopRequested);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : copy.stopFailed);
    }
  }, [copy.stopFailed, copy.stopRequested, currentRunId, refetch, run?.run_id, threadId]);

  const sheetContentId = "thread-details-panel";

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <Tooltip content={copy.tooltip}>
        <Button
          variant="ghost"
          className="text-muted-foreground hover:text-foreground relative"
          data-testid="thread-details-trigger"
          aria-controls={sheetContentId}
          aria-expanded={open}
          onClick={() => setOpen(true)}
        >
          {(streaming || active) && (
            <span className="bg-primary absolute top-1.5 left-1.5 size-2 rounded-full">
              <span className="bg-primary absolute inset-0 animate-ping rounded-full opacity-50" />
            </span>
          )}
          <ActivityIcon />
          {copy.trigger}
          {artifactCount > 0 && (
            <Badge variant="secondary" className="h-5 min-w-5 px-1.5 text-[10px]">
              {artifactCount}
            </Badge>
          )}
        </Button>
      </Tooltip>
      <SheetContent id={sheetContentId} className="w-[92vw] gap-0 p-0 sm:max-w-xl">
        <SheetHeader className="border-b pr-12">
          <div className="flex items-center justify-between gap-3">
            <div>
              <SheetTitle>{copy.title}</SheetTitle>
              <SheetDescription>
                {copy.description}
              </SheetDescription>
            </div>
            <Button size="icon-sm" variant="ghost" onClick={() => void refetch()}>
              <RefreshCwIcon className={cn("size-4", isFetching && "animate-spin")} />
            </Button>
          </div>
        </SheetHeader>
        <Tabs value={tab} onValueChange={setTab} className="min-h-0 flex-1 gap-0">
          <div className="border-b px-4 py-2">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="flow" onClick={() => setTab("flow")}>
                {copy.flow}
              </TabsTrigger>
              <TabsTrigger value="files" onClick={() => setTab("files")}>
                {copy.files}
              </TabsTrigger>
              <TabsTrigger value="stats" onClick={() => setTab("stats")}>
                {copy.stats}
              </TabsTrigger>
              <TabsTrigger value="logs" onClick={() => setTab("logs")}>
                {copy.logs}
              </TabsTrigger>
            </TabsList>
          </div>

          <ScrollArea className="min-h-0 flex-1">
            <div className="p-4">
              <TabsContent value="flow" className="mt-0 space-y-4">
                <RunSummary workflow={workflow} active={active} streaming={streaming} />
                <WorkflowTree
                  workflow={workflow}
                  onOpenArtifact={openArtifact}
                  copy={copy}
                  locale={locale}
                />
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
                    title={copy.noFilesTitle}
                    description={copy.noFilesDescription}
                  />
                )}
              </TabsContent>

              <TabsContent value="stats" className="mt-0">
                <StatsSection
                  workflow={workflow}
                  active={active}
                  streaming={streaming}
                  threadUsage={threadUsage}
                  threadDuration={threadDuration}
                  artifactCount={artifactCount}
                  eventCount={eventCount}
                  onCancelRun={() => void handleCancelRun()}
                />
              </TabsContent>

              <TabsContent value="logs" className="mt-0 space-y-3">
                <div className="flex justify-end">
                  <ExportMenu
                    workflow={workflow}
                    onExportThread={handleExportThread}
                  />
                </div>
                {visibleEvents.length ? (
                  <div className="space-y-2">
                    {visibleEvents.map((event) => (
                      <Collapsible key={event.seq} className="min-w-0 rounded-md border p-3">
                        <CollapsibleTrigger className="group flex w-full cursor-pointer items-start justify-between gap-3 text-left">
                          <div className="min-w-0 flex-1 overflow-hidden">
                            <div className="flex min-w-0 items-center gap-2 overflow-hidden text-sm font-medium">
                              <CodeIcon className="size-4" />
                              <span>#{event.seq}</span>
                              <span className="min-w-0 truncate">{event.event_type}</span>
                            </div>
                            <div className="text-muted-foreground mt-1 line-clamp-2 break-words text-xs">{event.summary}</div>
                          </div>
                          <div className="text-muted-foreground flex shrink-0 items-center gap-2 text-xs">
                            <ClockIcon className="size-3" />
                            {formatTime(event.created_at, locale)}
                          </div>
                        </CollapsibleTrigger>
                        <CollapsibleContent className="mt-3 overflow-hidden rounded-md bg-muted/50 p-2">
                          <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-all text-xs">
                            {JSON.stringify(event.content, null, 2)}
                          </pre>
                        </CollapsibleContent>
                      </Collapsible>
                    ))}
                  </div>
                ) : (
                  <EmptyDetailsState
                    icon={<CodeIcon />}
                    title={copy.noLogsTitle}
                    description={copy.noLogsDescription}
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
