import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import {
  getRunWorkflow,
  listThreadRuns,
  type WorkflowSnapshot,
} from "@/core/api/runs";
import { isRunActive, resolveThreadRun } from "@/core/runs/status";

export function isWorkflowRunActive(status?: string | null) {
  return status === "pending" || status === "running";
}

function sameRun(left: WorkflowSnapshot["run"], right: WorkflowSnapshot["run"]) {
  return (
    left.run_id === right.run_id &&
    left.status === right.status &&
    left.updated_at === right.updated_at &&
    left.last_event_at === right.last_event_at
  );
}

export function mergeWorkflowSnapshots(
  previous: WorkflowSnapshot | undefined,
  incoming: WorkflowSnapshot,
  afterSeq: number | undefined,
) {
  if (!previous || !afterSeq) {
    return incoming;
  }

  const existingEvents = new Set(previous.events.map((event) => event.seq));
  const existingNodes = new Set(previous.nodes.map((node) => node.id));
  const existingEdges = new Set(previous.edges.map((edge) => edge.id));
  const existingArtifacts = new Set(
    previous.artifacts.map((artifact) => artifact.filepath),
  );
  const incomingArtifacts = new Set(
    incoming.artifacts.map((artifact) => artifact.filepath),
  );
  const newEvents = incoming.events.filter(
    (event) => !existingEvents.has(event.seq),
  );
  const newNodes = incoming.nodes.filter((node) => !existingNodes.has(node.id));
  const newEdges = incoming.edges.filter((edge) => !existingEdges.has(edge.id));
  const newArtifacts = incoming.artifacts.filter(
    (artifact) => !existingArtifacts.has(artifact.filepath),
  );

  if (
    newEvents.length === 0 &&
    newNodes.length === 0 &&
    newEdges.length === 0 &&
    newArtifacts.length === 0 &&
    sameRun(previous.run, incoming.run)
  ) {
    return previous;
  }

  return {
    ...incoming,
    events: [...previous.events, ...newEvents].slice(-200),
    nodes: [...previous.nodes, ...newNodes].slice(-200),
    edges: [...previous.edges, ...newEdges].slice(-240),
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

  const run = resolveThreadRun(runsQuery.data, currentRunId);
  const active = isRunActive(run);
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
    refetchInterval: active ? 5000 : false,
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

    setWorkflow((previous) =>
      mergeWorkflowSnapshots(previous, incoming, afterSeq),
    );

    const maxSeq = incoming.events.reduce(
      (max, event) => Math.max(max, event.seq),
      lastSeq ?? 0,
    );
    if (maxSeq > 0 && maxSeq !== lastSeq) {
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
