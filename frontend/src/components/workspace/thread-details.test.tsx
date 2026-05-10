import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { I18nProvider } from "@/core/i18n/context";

import { SidebarProvider } from "../ui/sidebar";

import { ArtifactsProvider } from "./artifacts/context";
import { ThreadContext } from "./messages/context";
import { ThreadDetailsTrigger } from "./thread-details";

const mocks = vi.hoisted(() => ({
  cancelThreadRun: vi.fn(),
  listThreadRuns: vi.fn(),
  getRunWorkflow: vi.fn(),
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

const fakeThread = {
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
  },
  isLoading: false,
  error: null,
  stop: vi.fn(),
};

function wrapper({ children }: PropsWithChildren) {
  const client = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return (
    <QueryClientProvider client={client}>
      <I18nProvider initialLocale="zh-CN">
        <SidebarProvider>
          <ThreadContext.Provider
            value={{
              thread: fakeThread as never,
              sendMessage: vi.fn(),
            }}
          >
            <ArtifactsProvider>{children}</ArtifactsProvider>
          </ThreadContext.Provider>
        </SidebarProvider>
      </I18nProvider>
    </QueryClientProvider>
  );
}

describe("ThreadDetailsTrigger", () => {
  beforeEach(() => {
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
  });

  it("opens a details panel with workflow, artifacts, stats, export, and logs", async () => {
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
          id: "event-1",
          kind: "tool",
          label: "manuscript_export",
          status: "success",
          summary: "Generated manuscript bundle.",
          caller: "manuscript_export",
          seq: 1,
          created_at: "2026-05-09T00:00:05Z",
          metadata: { event_type: "tool_message" },
        },
      ],
      edges: [],
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
    expect(await screen.findByText("manuscript_export")).toBeInTheDocument();

    const filesTab = screen.getByRole("tab", { name: "产出" });
    fireEvent.pointerDown(filesTab);
    fireEvent.click(filesTab);
    expect(await screen.findByText("paper.pdf")).toBeInTheDocument();

    const statsTab = screen.getByRole("tab", { name: "统计" });
    fireEvent.pointerDown(statsTab);
    fireEvent.click(statsTab);
    expect(screen.getByText("30")).toBeInTheDocument();

    const exportTab = screen.getByRole("tab", { name: "导出" });
    fireEvent.pointerDown(exportTab);
    fireEvent.click(exportTab);
    expect(screen.getByText("导出运行轨迹 JSON")).toBeInTheDocument();

    const logsTab = screen.getByRole("tab", { name: "日志" });
    fireEvent.pointerDown(logsTab);
    fireEvent.click(logsTab);
    expect(screen.getByText("#1")).toBeInTheDocument();
  });
});
