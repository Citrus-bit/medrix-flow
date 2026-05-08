import { afterEach, describe, expect, it, vi } from "vitest";

import {
  saveSetupModels,
  testImageProvider,
} from "./api";

const fetchWithTimeoutMock = vi.fn();

vi.mock("@/core/api/fetch", () => ({
  fetchWithTimeout: (...args: unknown[]) => fetchWithTimeoutMock(...args),
}));

vi.mock("@/core/config", () => ({
  getBackendBaseURL: () => "",
}));

describe("setup api", () => {
  afterEach(() => {
    fetchWithTimeoutMock.mockReset();
  });

  it("surfaces backend detail when save fails", async () => {
    fetchWithTimeoutMock.mockResolvedValue(
      new Response(JSON.stringify({ detail: "Active image provider requires a model." }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(
      saveSetupModels({
        models: [],
        tool_keys: [],
        image_generation: null,
      }),
    ).rejects.toThrow("Active image provider requires a model.");
  });

  it("sends the expected payload for image provider tests", async () => {
    fetchWithTimeoutMock.mockResolvedValue(
      new Response(JSON.stringify({ success: true, message: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await testImageProvider({
      provider: "openai-compatible",
      model: "gpt-image-1",
      api_key: "sk-test",
      base_url: "https://images.example.com/v1",
    });

    expect(fetchWithTimeoutMock).toHaveBeenCalledWith(
      "/api/setup/test-image-provider",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: "openai-compatible",
          model: "gpt-image-1",
          api_key: "sk-test",
          base_url: "https://images.example.com/v1",
        }),
        timeoutMs: 30_000,
      }),
    );
  });
});
