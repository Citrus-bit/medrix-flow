import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import {
  getRunWorkflow,
  listThreadRuns,
  type RunData,
  type WorkflowSnapshot,
} from "@/core/api/runs";

const ACTIVE_STATUSES = new Set(["pending", "running"]);

function resolveRun(runs: RunData[] | undefined, currentRunId?: string | null) {
  if (!runs || runs.length === 0) return undefined;
  if (currentRunId) {
    return runs.find((run) => run.run_id === currentRunId) ?? runs[0];
  }
  return runs[0];
}

export function isWorkflowRunActive(status?: string | null) {
  return Boolean(status && ACTIVE_STATUSES.has(status));
}

export function useThreadWorkflow({
  threadId,
  currentRunId,
  enabled = true,
}: {
  threadId: string;
  currentRunId?: string | null;
  enabled?: boolean;
}) {
  const [workflow, setWorkflow] = useState<WorkflowSnapshot | undefined>();
  const [lastSeq, setLastSeq] = useState<number | undefined>();

  const runsQuery = useQuery({
    queryKey: ["thread-runs", threadId],
    queryFn: () => listThreadRuns(threadId),
    enabled: enabled && Boolean(threadId),
    refetchInterval: 5000,
    staleTime: 1000,
    retry: 1,
  });

  const run = resolveRun(runsQuery.data, currentRunId);
  const active = isWorkflowRunActive(run?.status);
  const afterSeq = active ? lastSeq : undefined;

  const workflowQuery = useQuery<WorkflowSnapshot>({
    queryKey: ["thread-run-workflow", threadId, run?.run_id, afterSeq],
    queryFn: () =>
      getRunWorkflow({
        threadId,
        runId: run!.run_id,
        limit: 200,
        afterSeq,
      }),
    enabled: enabled && Boolean(threadId && run?.run_id),
    refetchInterval: active ? 2000 : false,
    refetchOnWindowFocus: true,
    staleTime: active ? 0 : 10_000,
    retry: 1,
  });

  useEffect(() => {
    setWorkflow(undefined);
    setLastSeq(undefined);
  }, [threadId, run?.run_id]);

  useEffect(() => {
    const incoming = workflowQuery.data;
    if (!incoming) return;

    setWorkflow((previous) => {
      if (!previous || !afterSeq) {
        return incoming;
      }
      const existingEvents = new Set(previous.events.map((event) => event.seq));
      const existingNodes = new Set(previous.nodes.map((node) => node.id));
      const existingEdges = new Set(previous.edges.map((edge) => edge.id));
      const incomingArtifacts = new Set(
        incoming.artifacts.map((artifact) => artifact.filepath),
      );
      return {
        ...incoming,
        events: [
          ...previous.events,
          ...incoming.events.filter((event) => !existingEvents.has(event.seq)),
        ].slice(-200),
        nodes: [
          ...previous.nodes,
          ...incoming.nodes.filter((node) => !existingNodes.has(node.id)),
        ].slice(-200),
        edges: [
          ...previous.edges,
          ...incoming.edges.filter((edge) => !existingEdges.has(edge.id)),
        ].slice(-240),
        artifacts: [
          ...incoming.artifacts,
          ...previous.artifacts.filter(
            (artifact) => !incomingArtifacts.has(artifact.filepath),
          ),
        ],
        usage: {
          input_tokens: previous.usage.input_tokens + incoming.usage.input_tokens,
          output_tokens: previous.usage.output_tokens + incoming.usage.output_tokens,
          total_tokens: previous.usage.total_tokens + incoming.usage.total_tokens,
        },
      };
    });

    const maxSeq = incoming.events.reduce(
      (max, event) => Math.max(max, event.seq),
      lastSeq ?? 0,
    );
    if (maxSeq > 0) {
      setLastSeq(maxSeq);
    }
  }, [afterSeq, lastSeq, workflowQuery.data]);

  return useMemo(
    () => ({
      run,
      runs: runsQuery.data ?? [],
      workflow,
      active,
      isLoading: runsQuery.isLoading || workflowQuery.isLoading,
      isFetching: runsQuery.isFetching || workflowQuery.isFetching,
      error: runsQuery.error ?? workflowQuery.error,
      refetch: async () => {
        await runsQuery.refetch();
        setLastSeq(undefined);
        await workflowQuery.refetch();
      },
    }),
    [active, runsQuery, workflowQuery, run, workflow],
  );
}
