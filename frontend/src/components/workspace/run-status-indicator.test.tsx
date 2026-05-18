import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RunStatusIndicator } from "./run-status-indicator";

const mocks = vi.hoisted(() => ({
  listThreadRuns: vi.fn(),
}));

vi.mock("@/core/api/runs", () => ({
  listThreadRuns: (...args: unknown[]) => mocks.listThreadRuns(...args),
}));

vi.mock("@/core/i18n/hooks", () => ({
  useI18n: () => ({
    t: {
      runStatus: {
        running: "Running",
        reconnecting: "Backend run is still active. Reconnecting stream...",
        error: "Run ended with an error",
        interrupted: "Run interrupted",
        modelRetrying: (attempt: number, seconds: number) =>
          `Model temporarily unavailable. Retry ${attempt} in about ${seconds}s`,
        lastEvent: (time: string) => `Last event ${time}`,
      },
    },
  }),
}));

function wrapper({ children }: PropsWithChildren) {
  const client = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("RunStatusIndicator", () => {
  afterEach(() => {
    mocks.listThreadRuns.mockReset();
  });

  it("shows streaming state immediately", () => {
    mocks.listThreadRuns.mockResolvedValue([]);

    render(
      <RunStatusIndicator threadId="thread-1" currentRunId="run-1" streaming />,
      { wrapper },
    );

    expect(screen.getByText("Running")).toBeInTheDocument();
  });

  it("shows model retry status before generic streaming state", () => {
    mocks.listThreadRuns.mockResolvedValue([]);

    render(
      <RunStatusIndicator
        threadId="thread-1"
        currentRunId="run-1"
        streaming
        modelRetryStatus={{ attempt: 2, delaySeconds: 4.2 }}
      />,
      { wrapper },
    );

    expect(
      screen.getByText("Model temporarily unavailable. Retry 2 in about 5s"),
    ).toBeInTheDocument();
    expect(screen.queryByText("Running")).not.toBeInTheDocument();
  });

  it("shows reconnecting state when backend run remains active", async () => {
    const now = new Date().toISOString();
    mocks.listThreadRuns.mockResolvedValue([
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
    ]);

    render(
      <RunStatusIndicator
        threadId="thread-1"
        currentRunId="run-1"
        streaming={false}
      />,
      { wrapper },
    );

    expect(
      await screen.findByText("Backend run is still active. Reconnecting stream..."),
    ).toBeInTheDocument();
    expect(screen.getByTestId("run-status-indicator")).toHaveTextContent("Last event");
  });

  it("hides stale active runs when the stream is no longer active", async () => {
    mocks.listThreadRuns.mockResolvedValue([
      {
        run_id: "run-stale",
        thread_id: "thread-1",
        status: "pending",
        metadata: {},
        kwargs: {},
        multitask_strategy: "reject",
        created_at: "2020-01-01T00:00:00Z",
        updated_at: "2020-01-01T00:01:00Z",
      },
    ]);

    render(
      <RunStatusIndicator
        threadId="thread-1"
        currentRunId={null}
        streaming={false}
      />,
      { wrapper },
    );

    await waitFor(() => {
      expect(screen.queryByTestId("run-status-indicator")).not.toBeInTheDocument();
    });
  });

  it("shows terminal error and interrupted states but hides successful runs", async () => {
    mocks.listThreadRuns.mockResolvedValueOnce([
      {
        run_id: "run-1",
        thread_id: "thread-1",
        status: "error",
        metadata: {},
        kwargs: {},
        multitask_strategy: "reject",
        created_at: "2026-05-09T00:00:00Z",
        updated_at: "2026-05-09T00:01:00Z",
      },
    ]);

    const { unmount } = render(
      <RunStatusIndicator
        threadId="thread-1"
        currentRunId="run-1"
        streaming={false}
      />,
      { wrapper },
    );

    expect(await screen.findByText("Run ended with an error")).toBeInTheDocument();
    unmount();

    mocks.listThreadRuns.mockResolvedValueOnce([
      {
        run_id: "run-2",
        thread_id: "thread-2",
        status: "interrupted",
        metadata: {},
        kwargs: {},
        multitask_strategy: "reject",
        created_at: "2026-05-09T00:02:00Z",
        updated_at: "2026-05-09T00:03:00Z",
      },
    ]);

    const interrupted = render(
      <RunStatusIndicator
        threadId="thread-2"
        currentRunId="run-2"
        streaming={false}
      />,
      { wrapper },
    );

    expect(await screen.findByText("Run interrupted")).toBeInTheDocument();
    interrupted.unmount();

    mocks.listThreadRuns.mockResolvedValueOnce([
      {
        run_id: "run-3",
        thread_id: "thread-3",
        status: "success",
        metadata: {},
        kwargs: {},
        multitask_strategy: "reject",
        created_at: "2026-05-09T00:04:00Z",
        updated_at: "2026-05-09T00:05:00Z",
      },
    ]);

    render(
      <RunStatusIndicator
        threadId="thread-3"
        currentRunId="run-3"
        streaming={false}
      />,
      { wrapper },
    );

    await waitFor(() => {
      expect(screen.queryByTestId("run-status-indicator")).not.toBeInTheDocument();
    });
  });
});
