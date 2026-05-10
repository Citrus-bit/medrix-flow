import { getBackendBaseURL } from "@/core/config";

import { fetchWithTimeout } from "./fetch";

export type RunData = {
  run_id: string;
  thread_id: string;
  assistant_id?: string | null;
  status: string;
  metadata: Record<string, unknown>;
  kwargs: Record<string, unknown>;
  multitask_strategy: string;
  created_at: string;
  updated_at: string;
};

export type WorkflowNode = {
  id: string;
  kind: "user" | "agent" | "subagent" | "tool" | "artifact" | "checkpoint" | "final" | "error" | "event";
  label: string;
  status: "pending" | "running" | "success" | "error" | "interrupted";
  summary: string;
  caller?: string | null;
  tool_name?: string | null;
  artifact_path?: string | null;
  seq?: number | null;
  created_at?: string | null;
  metadata: Record<string, unknown>;
};

export type WorkflowEdge = {
  id: string;
  source: string;
  target: string;
  label?: string | null;
};

export type WorkflowEvent = {
  seq: number;
  run_id: string;
  thread_id: string;
  event_type: string;
  caller: string;
  summary: string;
  content: Record<string, unknown>;
  created_at: string;
};

export type WorkflowArtifact = {
  filepath: string;
  filename: string;
  size?: number | null;
  modified_at?: string | null;
};

export type WorkflowSnapshot = {
  run: {
    run_id: string;
    thread_id: string;
    assistant_id?: string | null;
    status: string;
    error?: string | null;
    created_at: string;
    updated_at: string;
    last_event_at?: string | null;
  };
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  events: WorkflowEvent[];
  artifacts: WorkflowArtifact[];
  usage: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  has_more: boolean;
};

export async function registerThreadRun(
  threadId: string,
  runId: string,
  options?: {
    assistantId?: string;
    context?: Record<string, unknown>;
  },
): Promise<RunData> {
  const response = await fetchWithTimeout(
    `${getBackendBaseURL()}/api/threads/${encodeURIComponent(threadId)}/runs`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        run_id: runId,
        assistant_id: options?.assistantId,
        context: options?.context,
      }),
    },
  );
  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as {
      detail?: string;
    };
    throw new Error(error.detail ?? "Failed to register run.");
  }
  return response.json() as Promise<RunData>;
}

export async function createRunEvent(
  threadId: string,
  runId: string,
  event: {
    event_type: string;
    caller?: string;
    content?: Record<string, unknown>;
  },
): Promise<WorkflowEvent> {
  const response = await fetchWithTimeout(
    `${getBackendBaseURL()}/api/threads/${encodeURIComponent(threadId)}/runs/${encodeURIComponent(runId)}/events`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_type: event.event_type,
        caller: event.caller ?? "frontend",
        content: event.content ?? {},
      }),
    },
  );
  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as {
      detail?: string;
    };
    throw new Error(error.detail ?? "Failed to record run event.");
  }
  return response.json() as Promise<WorkflowEvent>;
}

export async function getRunWorkflow({
  threadId,
  runId,
  limit = 200,
  afterSeq,
}: {
  threadId: string;
  runId: string;
  limit?: number;
  afterSeq?: number;
}): Promise<WorkflowSnapshot> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (afterSeq !== undefined) {
    params.set("after_seq", String(afterSeq));
  }
  const response = await fetchWithTimeout(
    `${getBackendBaseURL()}/api/threads/${encodeURIComponent(threadId)}/runs/${encodeURIComponent(runId)}/workflow?${params.toString()}`,
    { method: "GET" },
  );
  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as {
      detail?: string;
    };
    throw new Error(error.detail ?? "Failed to load run workflow.");
  }
  return response.json() as Promise<WorkflowSnapshot>;
}

export async function listThreadRuns(threadId: string): Promise<RunData[]> {
  const response = await fetchWithTimeout(
    `${getBackendBaseURL()}/api/threads/${encodeURIComponent(threadId)}/runs`,
    {
      method: "GET",
    },
  );
  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as {
      detail?: string;
    };
    throw new Error(error.detail ?? "Failed to list runs.");
  }
  return response.json() as Promise<RunData[]>;
}

export async function completeThreadRun(
  threadId: string,
  runId: string,
  status: "success" | "interrupted" | "error" = "success",
): Promise<RunData> {
  const response = await fetchWithTimeout(
    `${getBackendBaseURL()}/api/threads/${encodeURIComponent(threadId)}/runs/${encodeURIComponent(runId)}/complete`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    },
  );
  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as {
      detail?: string;
    };
    throw new Error(error.detail ?? "Failed to complete run.");
  }
  return response.json() as Promise<RunData>;
}

export async function cancelThreadRun(
  threadId: string,
  runId: string,
  action: "interrupt" | "rollback" = "interrupt",
): Promise<void> {
  const params = new URLSearchParams({ action });
  const response = await fetchWithTimeout(
    `${getBackendBaseURL()}/api/threads/${encodeURIComponent(threadId)}/runs/${encodeURIComponent(runId)}/cancel?${params.toString()}`,
    {
      method: "POST",
    },
  );
  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as {
      detail?: string;
    };
    throw new Error(error.detail ?? "Failed to cancel run.");
  }
}
