import { fireEvent, render, screen } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SidebarProvider } from "@/components/ui/sidebar";
import { I18nProvider } from "@/core/i18n/context";

import { WorkspaceNavMenu } from "./workspace-nav-menu";

vi.mock("./settings", () => ({
  SettingsDialog: () => null,
}));

function wrapper({ children }: PropsWithChildren) {
  return (
    <I18nProvider initialLocale="zh-CN">
      <SidebarProvider>{children}</SidebarProvider>
    </I18nProvider>
  );
}

describe("WorkspaceNavMenu", () => {
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
    document.cookie = "locale=; max-age=0; path=/";
    sessionStorage.clear();
  });

  it("shows the language toggle above settings and switches locale", async () => {
    render(<WorkspaceNavMenu />, { wrapper });

    const languageButton = screen.getByRole("button", { name: /中文|English/i });
    expect(languageButton).toBeInTheDocument();
    fireEvent.click(languageButton);

    expect(await screen.findByText(/中文|English/)).toBeInTheDocument();
  });

  it("opens the settings menu without about or appearance entries", async () => {
    sessionStorage.setItem("medrix_flow.setup-prompted", "1");

    render(<WorkspaceNavMenu />, { wrapper });

    fireEvent.click(screen.getByRole("button", { name: /设置和更多|Settings and more/i }));

    expect(await screen.findByText(/设置|Settings/)).toBeInTheDocument();
    expect(screen.queryByText("外观")).not.toBeInTheDocument();
    expect(screen.queryByText(/关于/i)).not.toBeInTheDocument();
  });
});
