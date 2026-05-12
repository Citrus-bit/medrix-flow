import { describe, expect, it } from "vitest";

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
});
