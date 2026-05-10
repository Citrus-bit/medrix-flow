import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { describe, expect, it, vi } from "vitest";

import { SettingsDialog } from "./settings-dialog";

vi.mock("@/core/i18n/hooks", async () => {
  const { zhCN } = await import("@/core/i18n/locales/zh-CN");
  return {
    useI18n: () => ({
      locale: "zh-CN",
      t: zhCN,
      changeLocale: vi.fn(),
    }),
  };
});

vi.mock("@/components/workspace/settings/setup-settings-page", () => ({
  SetupSettingsPage: () => <div>Setup panel</div>,
}));

vi.mock("@/components/workspace/settings/feature-settings-page", () => ({
  FeatureSettingsPage: () => <div>Features panel</div>,
}));

vi.mock("@/components/workspace/settings/notification-settings-page", () => ({
  NotificationSettingsPage: () => <div>Notification panel</div>,
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

describe("SettingsDialog", () => {
  it("shows configuration, features, and notification only", () => {
    render(<SettingsDialog open onOpenChange={() => undefined} />, { wrapper });

    expect(screen.getByRole("button", { name: "配置" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "功能" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "通知" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "记忆" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "外观" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /关于/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "功能" }));
    expect(screen.getByText("Features panel")).toBeInTheDocument();
  });
});
