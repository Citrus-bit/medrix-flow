import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, act, waitFor } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useThreadStream } from "./hooks";

const mocks = vi.hoisted(() => ({
  registerThreadRun: vi.fn(),
  completeThreadRun: vi.fn(),
  createRunEvent: vi.fn(),
  updateSubtask: vi.fn(),
  updateState: vi.fn(),
  toastError: vi.fn(),
  submit: vi.fn(),
  streamValues: { title: "", messages: [], artifacts: [] } as Record<string, unknown>,
}));

let capturedOptions: Record<string, unknown> | null = null;

vi.mock("@langchain/langgraph-sdk/react", () => ({
  useStream: vi.fn((options) => {
    capturedOptions = options;
    return {
      messages: [],
      isLoading: false,
      isThreadLoading: false,
      values: mocks.streamValues,
      stop: vi.fn(),
      submit: mocks.submit,
    };
  }),
}));

vi.mock("@/core/api", () => ({
  getAPIClient: vi.fn(() => ({
    threads: {
      getState: vi.fn(),
      updateState: (...args: unknown[]) => mocks.updateState(...args),
    },
  })),
}));

vi.mock("@/core/api/runs", () => ({
  registerThreadRun: (...args: unknown[]) => mocks.registerThreadRun(...args),
  completeThreadRun: (...args: unknown[]) => mocks.completeThreadRun(...args),
  createRunEvent: (...args: unknown[]) => mocks.createRunEvent(...args),
}));

vi.mock("@/core/i18n/hooks", () => ({
  useI18n: () => ({
    t: {
      setup: {
        noModelsConfigured: "No model",
        noModelsConfiguredHint: "Hint",
        openSettings: "Open settings",
      },
      uploads: { uploadingFiles: "Uploading files" },
      common: { thinking: "Thinking" },
    },
  }),
}));

vi.mock("@/core/tasks/context", () => ({
  useUpdateSubtask: () => mocks.updateSubtask,
}));

vi.mock("sonner", () => ({
  toast: {
    error: mocks.toastError,
  },
}));

vi.mock("@/core/settings/events", () => ({
  dispatchOpenSettings: vi.fn(),
}));

function wrapper({ children }: PropsWithChildren) {
  const client = new QueryClient();
  return (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

describe("useThreadStream", () => {
  afterEach(() => {
    capturedOptions = null;
    mocks.registerThreadRun.mockReset();
    mocks.completeThreadRun.mockReset();
    mocks.createRunEvent.mockReset();
    mocks.updateSubtask.mockReset();
    mocks.updateState.mockReset();
    mocks.toastError.mockReset();
    mocks.submit.mockReset();
    mocks.streamValues = { title: "", messages: [], artifacts: [] };
  });

  it("captures run_id from useStream metadata and sideband-registers it", async () => {
    mocks.registerThreadRun.mockResolvedValue(undefined);
    mocks.createRunEvent.mockResolvedValue(undefined);

    const { result } = renderHook(
      () =>
        useThreadStream({
          threadId: "thread-1",
          context: {
            mode: "flash",
            model_name: undefined,
            reasoning_effort: undefined,
          },
        }),
      { wrapper },
    );

    expect(capturedOptions).not.toBeNull();

    await act(async () => {
      (capturedOptions?.onCreated as (meta: { thread_id: string; run_id: string }) => void)({
        thread_id: "thread-1",
        run_id: "run-1",
      });
    });

    await waitFor(() => {
      expect(result.current[4]).toBe("run-1");
    });
    expect(mocks.registerThreadRun).toHaveBeenCalledWith("thread-1", "run-1", {
      assistantId: "lead_agent",
      context: {
        mode: "flash",
        model_name: undefined,
        reasoning_effort: undefined,
      },
    });
  });

  it("records tool-start events so workflow can reconstruct decisions", async () => {
    mocks.registerThreadRun.mockResolvedValue(undefined);
    mocks.createRunEvent.mockResolvedValue(undefined);

    renderHook(
      () =>
        useThreadStream({
          threadId: "thread-1",
          context: {
            mode: "flash",
            model_name: undefined,
            reasoning_effort: undefined,
          },
        }),
      { wrapper },
    );

    await act(async () => {
      (capturedOptions?.onCreated as (meta: { thread_id: string; run_id: string }) => void)({
        thread_id: "thread-1",
        run_id: "run-1",
      });
      (
        capturedOptions?.onLangChainEvent as (event: {
          event: string;
          name: string;
          run_id?: string;
          data?: unknown;
        }) => void
      )({
        event: "on_tool_start",
        name: "record_decision",
        run_id: "decision-call-1",
        data: {
          input: {
            title: "Choose benchmark discovery",
            decision_type: "tool_selection",
            rationale: "Need a benchmark map before experiments.",
            next_step: "Run dataset_benchmark_discovery.",
            status: "running",
          },
        },
      });
    });

    await waitFor(() => {
      expect(mocks.createRunEvent).toHaveBeenCalledWith(
        "thread-1",
        "run-1",
        expect.objectContaining({
          event_type: "ai_tool_calls",
          caller: "assistant",
          content: expect.objectContaining({
            tool_calls: [
              expect.objectContaining({
                name: "record_decision",
                id: "decision-call-1",
                args: expect.objectContaining({
                  title: "Choose benchmark discovery",
                }),
              }),
            ],
          }),
        }),
      );
    });
  });

  it("updates subtask heartbeat without persisting empty subagent events", async () => {
    mocks.registerThreadRun.mockResolvedValue(undefined);
    mocks.createRunEvent.mockResolvedValue(undefined);

    renderHook(
      () =>
        useThreadStream({
          threadId: "thread-1",
          context: {
            mode: "flash",
            model_name: undefined,
            reasoning_effort: undefined,
          },
        }),
      { wrapper },
    );

    await act(async () => {
      (capturedOptions?.onCreated as (meta: { thread_id: string; run_id: string }) => void)({
        thread_id: "thread-1",
        run_id: "run-1",
      });
    });
    mocks.createRunEvent.mockClear();

    await act(async () => {
      (
        capturedOptions?.onCustomEvent as (event: {
          type: string;
          task_id: string;
          heartbeat?: boolean;
        }) => void
      )({
        type: "task_running",
        task_id: "task-1",
        heartbeat: true,
      });
    });

    expect(mocks.updateSubtask).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "task-1",
        lastUpdatedAt: expect.any(String),
      }),
    );
    expect(mocks.createRunEvent).not.toHaveBeenCalled();
  });

  it("persists real subagent messages as workflow events", async () => {
    mocks.registerThreadRun.mockResolvedValue(undefined);
    mocks.createRunEvent.mockResolvedValue(undefined);

    renderHook(
      () =>
        useThreadStream({
          threadId: "thread-1",
          context: {
            mode: "flash",
            model_name: undefined,
            reasoning_effort: undefined,
          },
        }),
      { wrapper },
    );

    await act(async () => {
      (capturedOptions?.onCreated as (meta: { thread_id: string; run_id: string }) => void)({
        thread_id: "thread-1",
        run_id: "run-1",
      });
    });
    mocks.createRunEvent.mockClear();

    await act(async () => {
      (
        capturedOptions?.onCustomEvent as (event: {
          type: string;
          task_id: string;
          message?: { id: string; content: string };
          heartbeat?: boolean;
        }) => void
      )({
        type: "task_running",
        task_id: "task-1",
        message: { id: "msg-1", content: "Collected references" },
      });
    });

    expect(mocks.createRunEvent).toHaveBeenCalledWith(
      "thread-1",
      "run-1",
      expect.objectContaining({
        event_type: "subagent_event",
        caller: "task",
        content: expect.objectContaining({
          task_id: "task-1",
          heartbeat: false,
          content: "Collected references",
        }),
      }),
    );
  });

  it("marks ordinary text requests as non-visual", async () => {
    mocks.submit.mockResolvedValue(undefined);

    const { result } = renderHook(
      () =>
        useThreadStream({
          threadId: "thread-1",
          context: {
            mode: "flash",
            model_name: undefined,
            reasoning_effort: undefined,
          },
        }),
      { wrapper },
    );

    await act(async () => {
      await result.current[1]("thread-1", {
        text: "帮我解释一下这个配置为什么报错",
        files: [],
      });
    });

    expect(mocks.submit).toHaveBeenCalledOnce();
    expect(mocks.submit.mock.calls[0]?.[1]?.context.visual_output_intent).toBe(false);
  });

  it("marks explicit visual requests as visual output intent", async () => {
    mocks.submit.mockResolvedValue(undefined);

    const { result } = renderHook(
      () =>
        useThreadStream({
          threadId: "thread-1",
          context: {
            mode: "flash",
            model_name: undefined,
            reasoning_effort: undefined,
          },
        }),
      { wrapper },
    );

    await act(async () => {
      await result.current[1]("thread-1", {
        text: "帮我画一个架构图",
        files: [],
      });
    });

    expect(mocks.submit).toHaveBeenCalledOnce();
    expect(mocks.submit.mock.calls[0]?.[1]?.context.visual_output_intent).toBe(true);
  });

  it("passes synthetic data mode through thread context", async () => {
    mocks.submit.mockResolvedValue(undefined);

    const { result } = renderHook(
      () =>
        useThreadStream({
          threadId: "thread-1",
          context: {
            mode: "flash",
            model_name: undefined,
            reasoning_effort: undefined,
            synthetic_data_mode: true,
          },
        }),
      { wrapper },
    );

    await act(async () => {
      await result.current[1]("thread-1", {
        text: "帮我完成一篇实验论文",
        files: [],
      });
    });

    expect(mocks.submit).toHaveBeenCalledOnce();
    expect(mocks.submit.mock.calls[0]?.[1]?.context.synthetic_data_mode).toBe(true);
  });

  it("approves a pending plan before submitting an explicit approval message", async () => {
    mocks.updateState.mockResolvedValue(undefined);
    mocks.submit.mockResolvedValue(undefined);
    mocks.streamValues = {
      title: "",
      messages: [],
      artifacts: [],
      plan: {
        summary: "Generate manuscript bundle",
        status: "awaiting_approval",
        revision_count: 1,
        revisions: [
          {
            revision_number: 1,
            source: "agent",
            note: "Initial plan",
            status: "awaiting_approval",
            updated_at: "2026-05-09T00:00:10Z",
          },
        ],
      },
    };

    const { result } = renderHook(
      () =>
        useThreadStream({
          threadId: "thread-1",
          context: {
            mode: "pro",
            model_name: undefined,
            reasoning_effort: undefined,
          },
        }),
      { wrapper },
    );

    await act(async () => {
      await result.current[1]("thread-1", {
        text: "我批准当前计划，请按计划执行。",
        files: [],
      });
    });

    expect(mocks.updateState).toHaveBeenCalledWith(
      "thread-1",
      expect.objectContaining({
        values: {
          plan: expect.objectContaining({
            status: "approved",
            revision_count: 2,
          }),
        },
      }),
    );
    expect(mocks.updateState.mock.invocationCallOrder[0]!).toBeLessThan(
      mocks.submit.mock.invocationCallOrder[0]!,
    );
    expect(mocks.submit).toHaveBeenCalledOnce();
  });

  it("does not auto-approve a pending plan for ordinary revision feedback", async () => {
    mocks.updateState.mockResolvedValue(undefined);
    mocks.submit.mockResolvedValue(undefined);
    mocks.streamValues = {
      title: "",
      messages: [],
      artifacts: [],
      plan: {
        summary: "Generate manuscript bundle",
        status: "awaiting_approval",
        revision_count: 1,
        revisions: [],
      },
    };

    const { result } = renderHook(
      () =>
        useThreadStream({
          threadId: "thread-1",
          context: {
            mode: "pro",
            model_name: undefined,
            reasoning_effort: undefined,
          },
        }),
      { wrapper },
    );

    await act(async () => {
      await result.current[1]("thread-1", {
        text: "请先修改第二阶段，不要执行。",
        files: [],
      });
    });

    expect(mocks.updateState).not.toHaveBeenCalled();
    expect(mocks.submit).toHaveBeenCalledOnce();
  });
});
