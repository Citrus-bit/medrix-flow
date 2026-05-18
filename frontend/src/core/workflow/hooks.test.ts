import { describe, expect, it, vi } from "vitest";

import type { WorkflowSnapshot } from "@/core/api/runs";

import { mergeWorkflowSnapshots } from "./hooks";

function makeWorkflowSnapshot(
  events: WorkflowSnapshot["events"],
  usage: WorkflowSnapshot["usage"] = {
    input_tokens: 0,
    output_tokens: 0,
    total_tokens: 0,
  },
): WorkflowSnapshot {
  return {
    run: {
      run_id: "run-1",
      thread_id: "thread-1",
      assistant_id: "lead_agent",
      status: "running",
      created_at: "2026-05-12T00:00:00Z",
      updated_at: "2026-05-12T00:00:00Z",
      last_event_at: "2026-05-12T00:00:00Z",
    },
    nodes: [],
    edges: [],
    events,
    artifacts: [],
    usage,
    has_more: false,
  };
}

describe("mergeWorkflowSnapshots", () => {
  it("returns previous snapshot for empty duplicate active-run deltas", () => {
    const previous = makeWorkflowSnapshot([
      {
        seq: 1,
        run_id: "run-1",
        thread_id: "thread-1",
        event_type: "tool_message",
        caller: "task",
        summary: "Started",
        content: { type: "tool" },
        created_at: "2026-05-12T00:00:00Z",
      },
    ]);
    const incoming = makeWorkflowSnapshot([]);

    const merged = mergeWorkflowSnapshots(previous, incoming, 1);

    expect(merged).toBe(previous);
  });

  it("does not double-count usage for duplicate active-run deltas", () => {
    const previous = makeWorkflowSnapshot(
      [
        {
          seq: 1,
          run_id: "run-1",
          thread_id: "thread-1",
          event_type: "tool_message",
          caller: "task",
          summary: "Started",
          content: { type: "tool" },
          created_at: "2026-05-12T00:00:00Z",
        },
      ],
      { input_tokens: 10, output_tokens: 5, total_tokens: 15 },
    );
    const incoming = makeWorkflowSnapshot(
      [],
      { input_tokens: 10, output_tokens: 5, total_tokens: 15 },
    );

    const merged = mergeWorkflowSnapshots(previous, incoming, 1);

    expect(merged).toBe(previous);
    expect(merged.usage.total_tokens).toBe(15);
  });

  it("appends only new workflow events for active-run deltas", () => {
    const previous = makeWorkflowSnapshot([
      {
        seq: 1,
        run_id: "run-1",
        thread_id: "thread-1",
        event_type: "tool_message",
        caller: "task",
        summary: "Started",
        content: { type: "tool" },
        created_at: "2026-05-12T00:00:00Z",
      },
    ]);
    const incoming = makeWorkflowSnapshot([
      {
        seq: 1,
        run_id: "run-1",
        thread_id: "thread-1",
        event_type: "tool_message",
        caller: "task",
        summary: "Duplicate",
        content: { type: "tool" },
        created_at: "2026-05-12T00:00:00Z",
      },
      {
        seq: 2,
        run_id: "run-1",
        thread_id: "thread-1",
        event_type: "ai_message",
        caller: "assistant",
        summary: "Done",
        content: { type: "ai" },
        created_at: "2026-05-12T00:00:01Z",
      },
    ]);

    const merged = mergeWorkflowSnapshots(previous, incoming, 1);

    expect(merged).not.toBe(previous);
    expect(merged.events.map((event) => event.seq)).toEqual([1, 2]);
  });

  it("accumulates usage only when a delta contains new workflow data", () => {
    const previous = makeWorkflowSnapshot(
      [
        {
          seq: 1,
          run_id: "run-1",
          thread_id: "thread-1",
          event_type: "tool_message",
          caller: "task",
          summary: "Started",
          content: { type: "tool" },
          created_at: "2026-05-12T00:00:00Z",
        },
      ],
      { input_tokens: 10, output_tokens: 5, total_tokens: 15 },
    );
    const incoming = makeWorkflowSnapshot(
      [
        {
          seq: 2,
          run_id: "run-1",
          thread_id: "thread-1",
          event_type: "ai_message",
          caller: "assistant",
          summary: "Done",
          content: { type: "ai" },
          created_at: "2026-05-12T00:00:01Z",
        },
      ],
      { input_tokens: 7, output_tokens: 3, total_tokens: 10 },
    );

    const merged = mergeWorkflowSnapshots(previous, incoming, 1);

    expect(merged).not.toBe(previous);
    expect(merged.usage).toEqual({
      input_tokens: 17,
      output_tokens: 8,
      total_tokens: 25,
    });
  });
});

describe("useThreadWorkflow polling", () => {
  it("uses a 5s workflow polling interval for active runs", async () => {
    vi.resetModules();
    const now = new Date().toISOString();
    const queryOptions: Array<Record<string, unknown>> = [];
    vi.doMock("@tanstack/react-query", () => ({
      useQuery: (options: Record<string, unknown>) => {
        queryOptions.push(options);
        if (
          Array.isArray(options.queryKey) &&
          options.queryKey[0] === "thread-runs"
        ) {
          return {
            data: [
              {
                run_id: "run-1",
                thread_id: "thread-1",
                status: "running",
                metadata: {},
                kwargs: {},
                multitask_strategy: "reject",
                created_at: now,
                updated_at: now,
              },
            ],
            isLoading: false,
            isFetching: false,
            refetch: vi.fn(),
          };
        }
        return {
          data: undefined,
          isLoading: false,
          isFetching: false,
          refetch: vi.fn(),
        };
      },
    }));

    const { renderHook } = await import("@testing-library/react");
    const { useThreadWorkflow } = await import("./hooks");

    renderHook(() =>
      useThreadWorkflow({
        threadId: "thread-1",
        currentRunId: "run-1",
        enabled: true,
      }),
    );

    const workflowOptions = queryOptions.find(
      (options) =>
        Array.isArray(options.queryKey) &&
        options.queryKey[0] === "thread-run-workflow",
    );
    expect(workflowOptions?.refetchInterval).toBe(5000);
  });
});
