import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Locale } from "@/core/i18n";
import { I18nProvider } from "@/core/i18n/context";

import { SidebarProvider } from "../ui/sidebar";

import { ArtifactsProvider } from "./artifacts/context";
import { ThreadContext } from "./messages/context";
import { ThreadDetailsTrigger } from "./thread-details";

const mocks = vi.hoisted(() => ({
  cancelThreadRun: vi.fn(),
  listThreadRuns: vi.fn(),
  getRunWorkflow: vi.fn(),
  updateState: vi.fn(),
  sendMessage: vi.fn(),
}));

vi.mock("@/core/api", () => ({
  getAPIClient: vi.fn(() => ({
    threads: {
      updateState: (...args: unknown[]) => mocks.updateState(...args),
    },
  })),
}));

vi.mock("@/core/api/runs", async (importOriginal) => {
  const actual = await importOriginal<Record<string, unknown>>();
  return {
    ...actual,
    cancelThreadRun: (...args: unknown[]) => mocks.cancelThreadRun(...args),
    listThreadRuns: (...args: unknown[]) => mocks.listThreadRuns(...args),
    getRunWorkflow: (...args: unknown[]) => mocks.getRunWorkflow(...args),
  };
});

function makeFakeThread(values: Record<string, unknown> = {}) {
  return {
    messages: [
      { type: "human", id: "h1", content: "Generate paper" },
      {
        type: "ai",
        id: "a1",
        content: "Done",
        usage_metadata: { input_tokens: 10, output_tokens: 20, total_tokens: 30 },
      },
    ],
    values: {
      title: "Paper",
      messages: [],
      artifacts: ["/mnt/user-data/outputs/paper.pdf"],
      ...values,
    },
    isLoading: false,
    error: null,
    stop: vi.fn(),
  };
}

function makeWrapper(
  locale: Locale,
  thread = makeFakeThread(),
  sendMessage = mocks.sendMessage,
) {
  return function TestWrapper({ children }: PropsWithChildren) {
    const client = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    return (
      <QueryClientProvider client={client}>
        <I18nProvider initialLocale={locale}>
          <SidebarProvider>
            <ThreadContext.Provider
              value={{
                thread: thread as never,
                sendMessage,
              }}
            >
              <ArtifactsProvider>{children}</ArtifactsProvider>
            </ThreadContext.Provider>
          </SidebarProvider>
        </I18nProvider>
      </QueryClientProvider>
    );
  };
}

const wrapper = makeWrapper("zh-CN");

function setTestLocale(locale: Locale) {
  document.cookie = `locale=${locale}; path=/; max-age=31536000`;
}

function mockEmptyWorkflow() {
  mocks.cancelThreadRun.mockResolvedValue(undefined);
  mocks.listThreadRuns.mockResolvedValue([
    {
      run_id: "run-1",
      thread_id: "thread-1",
      assistant_id: "lead_agent",
      status: "success",
      metadata: {},
      kwargs: {},
      multitask_strategy: "reject",
      created_at: "2026-05-09T00:00:00Z",
      updated_at: "2026-05-09T00:00:10Z",
    },
  ]);
  mocks.getRunWorkflow.mockResolvedValue({
    run: {
      run_id: "run-1",
      thread_id: "thread-1",
      assistant_id: "lead_agent",
      status: "success",
      created_at: "2026-05-09T00:00:00Z",
      updated_at: "2026-05-09T00:00:10Z",
      last_event_at: null,
    },
    nodes: [],
    edges: [],
    events: [],
    artifacts: [],
    usage: { input_tokens: 0, output_tokens: 0, total_tokens: 0 },
    has_more: false,
  });
}

describe("ThreadDetailsTrigger", () => {
  beforeEach(() => {
    setTestLocale("zh-CN");
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  afterEach(() => {
    mocks.cancelThreadRun.mockReset();
    mocks.listThreadRuns.mockReset();
    mocks.getRunWorkflow.mockReset();
    mocks.updateState.mockReset();
    mocks.sendMessage.mockReset();
    document.cookie = "locale=; max-age=0; path=/";
  });

  it("opens a details panel with workflow tree, artifacts, stats, and logs export menu", async () => {
    mocks.cancelThreadRun.mockResolvedValue(undefined);
    mocks.listThreadRuns.mockResolvedValue([
      {
        run_id: "run-1",
        thread_id: "thread-1",
        assistant_id: "lead_agent",
        status: "success",
        metadata: {},
        kwargs: {},
        multitask_strategy: "reject",
        created_at: "2026-05-09T00:00:00Z",
        updated_at: "2026-05-09T00:00:10Z",
      },
    ]);
    mocks.getRunWorkflow.mockResolvedValue({
      run: {
        run_id: "run-1",
        thread_id: "thread-1",
        assistant_id: "lead_agent",
        status: "success",
        created_at: "2026-05-09T00:00:00Z",
        updated_at: "2026-05-09T00:00:10Z",
        last_event_at: "2026-05-09T00:00:10Z",
      },
      nodes: [
        {
          id: "decision-1",
          kind: "decision",
          label: "选择论文导出路径",
          status: "success",
          summary: "需要生成可交付论文文件，因此使用 manuscript_export。",
          caller: "assistant",
          tool_name: "record_decision",
          seq: 1,
          created_at: "2026-05-09T00:00:04Z",
          metadata: {
            event_type: "ai_tool_calls",
            decision_type: "tool_selection",
            rationale: "需要生成可交付论文文件，因此使用 manuscript_export。",
            next_step: "调用 manuscript_export 生成 LaTeX 与 PDF。",
            outcome: "论文文件已生成。",
            alternatives: ["手动写入文件后再调用 present_files"],
            related_tool: "manuscript_export",
          },
        },
        {
          id: "event-2",
          kind: "tool",
          label: "manuscript_export",
          status: "success",
          summary: "Generated manuscript bundle.",
          caller: "manuscript_export",
          seq: 2,
          created_at: "2026-05-09T00:00:05Z",
          metadata: { event_type: "tool_message" },
        },
        {
          id: "artifact-1",
          kind: "artifact",
          label: "paper.pdf",
          status: "success",
          summary:
            "/mnt/user-data/outputs/really-long-directory-name-that-should-wrap-instead-of-overflowing-the-panel/paper.pdf",
          artifact_path:
            "/mnt/user-data/outputs/really-long-directory-name-that-should-wrap-instead-of-overflowing-the-panel/paper.pdf",
          seq: 2,
          created_at: "2026-05-09T00:00:06Z",
          metadata: {},
        },
      ],
      edges: [
        {
          id: "edge-decision-1-event-2",
          source: "decision-1",
          target: "event-2",
        },
        {
          id: "edge-event-2-artifact-1",
          source: "event-2",
          target: "artifact-1",
          label: "created",
        },
      ],
      events: [
        {
          seq: 1,
          run_id: "run-1",
          thread_id: "thread-1",
          event_type: "tool_message",
          caller: "manuscript_export",
          summary: "Generated manuscript bundle.",
          content: { type: "tool", content: "Generated manuscript bundle." },
          created_at: "2026-05-09T00:00:05Z",
        },
        {
          seq: 2,
          run_id: "run-1",
          thread_id: "thread-1",
          event_type: "subagent_event",
          caller: "task",
          summary: '""',
          content: {
            type: "task",
            task_id: "task-1",
            heartbeat: true,
            content: '""',
          },
          created_at: "2026-05-09T00:00:06Z",
        },
      ],
      artifacts: [
        {
          filepath: "/mnt/user-data/outputs/paper.pdf",
          filename: "paper.pdf",
          size: 123,
          modified_at: "2026-05-09T00:00:10Z",
        },
      ],
      usage: { input_tokens: 10, output_tokens: 20, total_tokens: 30 },
      has_more: false,
    });

    render(
      <ThreadDetailsTrigger threadId="thread-1" currentRunId="run-1" streaming={false} />,
      { wrapper },
    );

    fireEvent.click(screen.getByTestId("thread-details-trigger"));

    expect(await screen.findByText("Agent 工作流、工具调用、产出文件与运行日志")).toBeInTheDocument();
    expect(screen.getAllByRole("tab")).toHaveLength(4);
    expect(screen.queryByRole("tab", { name: "计划" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "导出" })).not.toBeInTheDocument();

    const flowTab = screen.getByRole("tab", { name: "流程" });
    fireEvent.pointerDown(flowTab);
    fireEvent.click(flowTab);
    expect(await screen.findByText("用户目标 / Run")).toBeInTheDocument();
    expect(await screen.findByText("选择论文导出路径")).toBeInTheDocument();
    expect(screen.getByText("决策")).toBeInTheDocument();
    fireEvent.click(screen.getByText("选择论文导出路径"));
    expect(await screen.findByText("依据")).toBeInTheDocument();
    expect(screen.getByText("调用 manuscript_export 生成 LaTeX 与 PDF。")).toBeInTheDocument();
    expect(screen.getByText("论文文件已生成。")).toBeInTheDocument();
    expect(screen.getAllByText("manuscript_export").length).toBeGreaterThan(0);
    fireEvent.click(await screen.findByText("paper.pdf"));
    expect(await screen.findByTestId("workflow-artifact-path")).toHaveTextContent(
      "/mnt/user-data/outputs/really-long-directory-name-that-should-wrap-instead-of-overflowing-the-panel/paper.pdf",
    );

    const filesTab = screen.getByRole("tab", { name: "产出" });
    fireEvent.pointerDown(filesTab);
    fireEvent.click(filesTab);
    expect(await screen.findByText("paper.pdf")).toBeInTheDocument();

    const statsTab = screen.getByRole("tab", { name: "统计" });
    fireEvent.pointerDown(statsTab);
    fireEvent.click(statsTab);
    expect(screen.getByText("当前 Run")).toBeInTheDocument();
    expect(screen.getByText("整个对话")).toBeInTheDocument();
    expect(screen.getAllByText("30").length).toBeGreaterThanOrEqual(2);

    const logsTab = screen.getByRole("tab", { name: "日志" });
    fireEvent.pointerDown(logsTab);
    fireEvent.click(logsTab);
    const exportButton = screen.getByRole("button", { name: "导出" });
    fireEvent.keyDown(exportButton, { key: "Enter" });
    const menu = await screen.findByRole("menu");
    expect(within(menu).getByText("导出对话 Markdown")).toBeInTheDocument();
    expect(within(menu).getByText("导出对话 JSON")).toBeInTheDocument();
    expect(within(menu).getByText("导出运行轨迹 JSON")).toBeInTheDocument();
    expect(screen.getByText("#1")).toBeInTheDocument();
    expect(screen.queryByText("#2")).not.toBeInTheDocument();
    expect(screen.queryByText("subagent_event")).not.toBeInTheDocument();
  });

  it("keeps scanned-only artifacts out of the workflow tab", async () => {
    mocks.cancelThreadRun.mockResolvedValue(undefined);
    mocks.listThreadRuns.mockResolvedValue([
      {
        run_id: "run-1",
        thread_id: "thread-1",
        assistant_id: "lead_agent",
        status: "success",
        metadata: {},
        kwargs: {},
        multitask_strategy: "reject",
        created_at: "2026-05-09T00:00:00Z",
        updated_at: "2026-05-09T00:00:10Z",
      },
    ]);
    mocks.getRunWorkflow.mockResolvedValue({
      run: {
        run_id: "run-1",
        thread_id: "thread-1",
        assistant_id: "lead_agent",
        status: "success",
        created_at: "2026-05-09T00:00:00Z",
        updated_at: "2026-05-09T00:00:10Z",
        last_event_at: null,
      },
      nodes: [],
      edges: [],
      events: [],
      artifacts: [
        {
          filepath: "/mnt/user-data/outputs/scanned-only.txt",
          filename: "scanned-only.txt",
          size: 123,
          modified_at: "2026-05-09T00:00:10Z",
        },
      ],
      usage: { input_tokens: 0, output_tokens: 0, total_tokens: 0 },
      has_more: false,
    });

    render(
      <ThreadDetailsTrigger threadId="thread-1" currentRunId="run-1" streaming={false} />,
      { wrapper },
    );

    fireEvent.click(screen.getByTestId("thread-details-trigger"));

    const flowTab = screen.getByRole("tab", { name: "流程" });
    fireEvent.pointerDown(flowTab);
    fireEvent.click(flowTab);
    expect(await screen.findByText("用户目标 / Run")).toBeInTheDocument();
    expect(screen.queryByText("历史产出")).not.toBeInTheDocument();
    expect(screen.queryByText("scanned-only.txt")).not.toBeInTheDocument();

    const filesTab = screen.getByRole("tab", { name: "产出" });
    fireEvent.pointerDown(filesTab);
    fireEvent.click(filesTab);
    expect(await screen.findByText("scanned-only.txt")).toBeInTheDocument();
  });

  it("attributes slow-step timing to tool calls and keeps single-event runs visible", async () => {
    mocks.cancelThreadRun.mockResolvedValue(undefined);
    mocks.listThreadRuns.mockResolvedValue([
      {
        run_id: "run-slow",
        thread_id: "thread-1",
        assistant_id: "lead_agent",
        status: "success",
        metadata: {},
        kwargs: {},
        multitask_strategy: "reject",
        created_at: "2026-05-09T00:00:00Z",
        updated_at: "2026-05-09T00:00:12Z",
      },
    ]);
    mocks.getRunWorkflow.mockResolvedValue({
      run: {
        run_id: "run-slow",
        thread_id: "thread-1",
        assistant_id: "lead_agent",
        status: "success",
        created_at: "2026-05-09T00:00:00Z",
        updated_at: "2026-05-09T00:00:12Z",
        last_event_at: "2026-05-09T00:00:12Z",
      },
      nodes: [],
      edges: [],
      events: [
        {
          seq: 1,
          run_id: "run-slow",
          thread_id: "thread-1",
          event_type: "ai_tool_calls",
          caller: "assistant",
          summary: "Starting experiment",
          content: {
            type: "ai",
            tool_calls: [
              {
                name: "experiment_lab",
                args: {},
                id: "tool-start",
              },
            ],
          },
          created_at: "2026-05-09T00:00:00Z",
        },
        {
          seq: 2,
          run_id: "run-slow",
          thread_id: "thread-1",
          event_type: "subagent_event",
          caller: "task",
          summary: '""',
          content: {
            type: "task",
            task_id: "task-1",
            heartbeat: true,
            content: '""',
          },
          created_at: "2026-05-09T00:00:05Z",
        },
      ],
      artifacts: [],
      usage: { input_tokens: 0, output_tokens: 0, total_tokens: 0 },
      has_more: false,
    });

    render(
      <ThreadDetailsTrigger threadId="thread-1" currentRunId="run-slow" streaming={false} />,
      { wrapper },
    );

    fireEvent.click(screen.getByTestId("thread-details-trigger"));
    expect(await screen.findByText("Agent 工作流、工具调用、产出文件与运行日志")).toBeInTheDocument();
    expect(await screen.findByText("用户目标 / Run")).toBeInTheDocument();

    const statsTab = screen.getByRole("tab", { name: "统计" });
    fireEvent.pointerDown(statsTab);
    fireEvent.click(statsTab);

    expect(await screen.findByText("慢步骤来源")).toBeInTheDocument();
    const slowStepRow = screen.getByText("experiment_lab").closest(".grid");
    if (!(slowStepRow instanceof HTMLElement)) {
      throw new Error("Expected experiment_lab slow-step row");
    }
    expect(within(slowStepRow).getByText("12s")).toBeInTheDocument();
    expect(within(slowStepRow).getByText("1 个事件")).toBeInTheDocument();

    const logsTab = screen.getByRole("tab", { name: "日志" });
    fireEvent.pointerDown(logsTab);
    fireEvent.click(logsTab);
    expect(screen.getByText("#1")).toBeInTheDocument();
    expect(screen.queryByText("#2")).not.toBeInTheDocument();
  });

  it("renders the details panel fully in English when English locale is active", async () => {
    setTestLocale("en-US");
    mockEmptyWorkflow();

    render(
      <ThreadDetailsTrigger threadId="thread-1" currentRunId="run-1" streaming={false} />,
      { wrapper: makeWrapper("en-US") },
    );

    fireEvent.click(screen.getByTestId("thread-details-trigger"));

    expect(await screen.findByRole("heading", { name: "Details" })).toBeInTheDocument();
    expect(screen.getByText("Agent workflow, tool calls, output files, and run logs")).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Plan" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("tab")).toHaveLength(4);
    expect(screen.getByRole("tab", { name: "Flow" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Files" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Stats" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Logs" })).toBeInTheDocument();

    const flowTab = screen.getByRole("tab", { name: "Flow" });
    fireEvent.pointerDown(flowTab);
    fireEvent.click(flowTab);
    expect(await screen.findByText("User Goal / Run")).toBeInTheDocument();
    expect(screen.getByText("No visual decision flow yet")).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent(/[详情流程产出统计日志暂无未记录当前整个导出]/);
  });

  it("opens reliably while a run is actively streaming", async () => {
    const now = new Date().toISOString();
    mocks.cancelThreadRun.mockResolvedValue(undefined);
    mocks.listThreadRuns.mockResolvedValue([
      {
        run_id: "run-active",
        thread_id: "thread-1",
        assistant_id: "lead_agent",
        status: "running",
        metadata: {},
        kwargs: {},
        multitask_strategy: "reject",
        created_at: now,
        updated_at: now,
      },
    ]);
    mocks.getRunWorkflow.mockResolvedValue({
      run: {
        run_id: "run-active",
        thread_id: "thread-1",
        assistant_id: "lead_agent",
        status: "running",
        created_at: now,
        updated_at: now,
        last_event_at: now,
      },
      nodes: [],
      edges: [],
      events: [],
      artifacts: [],
      usage: { input_tokens: 0, output_tokens: 0, total_tokens: 0 },
      has_more: false,
    });

    render(
      <ThreadDetailsTrigger
        threadId="thread-1"
        currentRunId="run-active"
        streaming
      />,
      { wrapper },
    );

    const trigger = await screen.findByTestId("thread-details-trigger");
    expect(trigger.querySelector(".animate-ping")).toBeInTheDocument();
    expect(mocks.getRunWorkflow).not.toHaveBeenCalled();

    fireEvent.click(trigger);

    expect(await screen.findByText("Agent 工作流、工具调用、产出文件与运行日志")).toBeInTheDocument();
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    await waitFor(() => expect(mocks.getRunWorkflow).toHaveBeenCalled());
  });

  it("does not show an active badge for stale pending runs", async () => {
    mocks.cancelThreadRun.mockResolvedValue(undefined);
    mocks.listThreadRuns.mockResolvedValue([
      {
        run_id: "run-stale",
        thread_id: "thread-1",
        assistant_id: "lead_agent",
        status: "pending",
        metadata: {},
        kwargs: {},
        multitask_strategy: "reject",
        created_at: "2020-01-01T00:00:00Z",
        updated_at: "2020-01-01T00:01:00Z",
      },
    ]);
    mocks.getRunWorkflow.mockResolvedValue({
      run: {
        run_id: "run-stale",
        thread_id: "thread-1",
        assistant_id: "lead_agent",
        status: "pending",
        created_at: "2020-01-01T00:00:00Z",
        updated_at: "2020-01-01T00:01:00Z",
        last_event_at: null,
      },
      nodes: [],
      edges: [],
      events: [],
      artifacts: [],
      usage: { input_tokens: 0, output_tokens: 0, total_tokens: 0 },
      has_more: false,
    });

    render(
      <ThreadDetailsTrigger threadId="thread-1" currentRunId={null} streaming={false} />,
      { wrapper },
    );

    await screen.findByTestId("thread-details-trigger");
    await vi.waitFor(() => {
      expect(
        screen.getByTestId("thread-details-trigger").querySelector(".animate-ping"),
      ).not.toBeInTheDocument();
    });
  });
});
