import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { I18nProvider } from "@/core/i18n/context";

import { FeatureSettingsPage } from "./feature-settings-page";

const mocks = vi.hoisted(() => ({
  loadFeatures: vi.fn(),
}));

vi.mock("@/core/features/api", () => ({
  loadFeatures: () => mocks.loadFeatures(),
}));

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
      <I18nProvider initialLocale="en-US">{children}</I18nProvider>
    </QueryClientProvider>
  );
}

describe("FeatureSettingsPage", () => {
  afterEach(() => {
    mocks.loadFeatures.mockReset();
  });

  it("renders agents, tools, and skills as a read-only inventory", async () => {
    mocks.loadFeatures.mockResolvedValue({
      agents: [
        {
          name: "academic-researcher",
          description: "Runs evidence-grounded research workflows.",
          model: "gpt-5.5",
          tool_groups: ["academic"],
          kind: "system",
          readonly: true,
        },
      ],
      tools: [
        {
          name: "paper-search",
          enabled: true,
          transport: "http",
          description: "Academic search MCP server.",
          command: null,
          url: "https://mcp.example.com/sse",
          args: [],
          env_keys: [{ key: "API_KEY", configured: true }],
          header_keys: [{ key: "Authorization", configured: true }],
          oauth_enabled: false,
        },
      ],
      skills: [
        {
          name: "literature-finder",
          description: "Find relevant papers.",
          license: "MIT",
          category: "public",
          enabled: true,
        },
      ],
    });

    render(<FeatureSettingsPage />, { wrapper });

    expect(await screen.findByText("academic-researcher")).toBeInTheDocument();
    expect(screen.getByText("paper-search")).toBeInTheDocument();
    expect(screen.getByText("literature-finder")).toBeInTheDocument();
    expect(screen.getByText("API_KEY")).toBeInTheDocument();
    expect(screen.getByText("Authorization")).toBeInTheDocument();

    const controls = screen.queryAllByRole("button").filter((button) =>
      /add|create|delete|edit|save|test|enable|disable|新增|创建|删除|编辑|保存|测试|启用|停用/i.test(
        button.textContent ?? "",
      ),
    );
    expect(controls).toHaveLength(0);

    expect(screen.queryByRole("switch")).not.toBeInTheDocument();
  });
});
