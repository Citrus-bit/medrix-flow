import { afterEach, describe, expect, it, vi } from "vitest";

import { cancelThreadRun, completeThreadRun, listThreadRuns, registerThreadRun } from "./runs";

const fetchMock = vi.fn();

vi.stubGlobal("fetch", fetchMock);

describe("runs api", () => {
  afterEach(() => {
    fetchMock.mockReset();
  });

  it("registers an external run with run_id and context", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          run_id: "run-1",
          thread_id: "thread-1",
          status: "pending",
          metadata: {},
          kwargs: {},
          multitask_strategy: "reject",
          created_at: "now",
          updated_at: "now",
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await registerThreadRun("thread-1", "run-1", {
      assistantId: "lead_agent",
      context: { mode: "flash" },
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/threads/thread-1/runs",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          run_id: "run-1",
          assistant_id: "lead_agent",
          context: { mode: "flash" },
        }),
        signal: expect.any(AbortSignal),
      }),
    );
  });

  it("finalizes a run with completion status", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          run_id: "run-1",
          thread_id: "thread-1",
          status: "success",
          metadata: {},
          kwargs: {},
          multitask_strategy: "reject",
          created_at: "now",
          updated_at: "now",
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await completeThreadRun("thread-1", "run-1", "success");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/threads/thread-1/runs/run-1/complete",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "success" }),
        signal: expect.any(AbortSignal),
      }),
    );
  });

  it("cancels an active run", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 202 }));

    await cancelThreadRun("thread-1", "run-1");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/threads/thread-1/runs/run-1/cancel?action=interrupt",
      expect.objectContaining({
        method: "POST",
        signal: expect.any(AbortSignal),
      }),
    );
  });

  it("lists runs for a thread", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify([
          {
            run_id: "run-1",
            thread_id: "thread-1",
            status: "running",
            metadata: {},
            kwargs: {},
            multitask_strategy: "reject",
            created_at: "now",
            updated_at: "later",
          },
        ]),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    const runs = await listThreadRuns("thread-1");

    expect(runs[0]?.status).toBe("running");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/threads/thread-1/runs",
      expect.objectContaining({
        method: "GET",
        signal: expect.any(AbortSignal),
      }),
    );
  });
});
