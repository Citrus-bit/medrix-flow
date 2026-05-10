"use client";

import {
  ChevronsUpDown,
  LanguagesIcon,
  Settings2Icon,
  SettingsIcon,
} from "lucide-react";
import { useEffect, useState } from "react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { Tooltip } from "@/components/workspace/tooltip";
import type { Locale } from "@/core/i18n";
import { useI18n } from "@/core/i18n/hooks";
import {
  OPEN_SETTINGS_EVENT,
  type OpenSettingsDetail,
} from "@/core/settings/events";

import { GithubIcon } from "./github-icon";
import { SettingsDialog } from "./settings";

function NavMenuButtonContent({
  isSidebarOpen,
  t,
}: {
  isSidebarOpen: boolean;
  t: ReturnType<typeof useI18n>["t"];
}) {
  return isSidebarOpen ? (
    <div className="text-muted-foreground flex w-full items-center gap-2 text-left text-sm">
      <SettingsIcon className="size-4" />
      <span>{t.workspace.settingsAndMore}</span>
      <ChevronsUpDown className="text-muted-foreground ml-auto size-4" />
    </div>
  ) : (
    <div className="flex size-full items-center justify-center">
      <SettingsIcon className="text-muted-foreground size-4" />
    </div>
  );
}

const SETUP_PROMPT_SESSION_KEY = "medrix_flow.setup-prompted";
const nextLocale: Record<Locale, Locale> = {
  "en-US": "zh-CN",
  "zh-CN": "en-US",
};

export function WorkspaceNavMenu() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsDefaultSection, setSettingsDefaultSection] = useState<
    "setup" | "features" | "notification"
  >("setup");
  const [mounted, setMounted] = useState(false);
  const { open: isSidebarOpen } = useSidebar();
  const { t, locale, changeLocale } = useI18n();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<OpenSettingsDetail>).detail;
      setSettingsDefaultSection(detail?.section ?? "setup");
      setSettingsOpen(true);
    };
    window.addEventListener(OPEN_SETTINGS_EVENT, handler);
    return () => window.removeEventListener(OPEN_SETTINGS_EVENT, handler);
  }, []);

  // Auto-open settings on "setup" tab to remind users to configure model/API
  // Triggers once per browser session (tracked via sessionStorage)
  // Delayed by 600ms so users see the main UI first (less jarring)
  useEffect(() => {
    if (!mounted) return;
    const alreadyPrompted = sessionStorage.getItem(SETUP_PROMPT_SESSION_KEY);
    if (!alreadyPrompted) {
      const timer = setTimeout(() => {
        sessionStorage.setItem(SETUP_PROMPT_SESSION_KEY, "1");
        setSettingsDefaultSection("setup");
        setSettingsOpen(true);
      }, 600);
      return () => clearTimeout(timer);
    }
  }, [mounted]);

  return (
    <>
      <SettingsDialog
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        defaultSection={settingsDefaultSection}
      />
      <SidebarMenu className="w-full">
        <SidebarMenuItem>
          <Tooltip
            content={
              locale === "zh-CN"
                ? "Switch to English"
                : "切换到中文"
            }
          >
            <SidebarMenuButton
              type="button"
              onClick={() => changeLocale(nextLocale[locale])}
              className="text-muted-foreground"
            >
              <LanguagesIcon className="size-4" />
              {isSidebarOpen && (
                <span>{locale === "zh-CN" ? "English" : "中文"}</span>
              )}
            </SidebarMenuButton>
          </Tooltip>
        </SidebarMenuItem>
        <SidebarMenuItem>
          {mounted ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  size="lg"
                  className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                >
                  <NavMenuButtonContent isSidebarOpen={isSidebarOpen} t={t} />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
                align="end"
                sideOffset={4}
              >
                <DropdownMenuGroup>
                  <DropdownMenuItem
                    onClick={() => {
                      setSettingsDefaultSection("setup");
                      setSettingsOpen(true);
                    }}
                  >
                    <Settings2Icon />
                    {t.common.settings}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <a
                    href="https://github.com/Citrus-bit/medrix-flow"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <DropdownMenuItem>
                      <GithubIcon />
                      {t.workspace.visitGithub}
                    </DropdownMenuItem>
                  </a>
                </DropdownMenuGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <SidebarMenuButton size="lg" className="pointer-events-none">
              <NavMenuButtonContent isSidebarOpen={isSidebarOpen} t={t} />
            </SidebarMenuButton>
          )}
        </SidebarMenuItem>
      </SidebarMenu>
    </>
  );
}
