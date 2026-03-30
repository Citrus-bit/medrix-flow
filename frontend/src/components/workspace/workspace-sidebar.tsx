"use client";

import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar";

import { RecentChatList } from "./recent-chat-list";
import { WorkspaceHeader } from "./workspace-header";
import { WorkspaceNavChatList } from "./workspace-nav-chat-list";
import { WorkspaceNavMenu } from "./workspace-nav-menu";

export function WorkspaceSidebar({
  ...props
}: React.ComponentProps<typeof Sidebar>) {
  const { open: isSidebarOpen } = useSidebar();
  return (
    <>
      <Sidebar variant="sidebar" collapsible="icon" {...props}>
        <SidebarHeader className="border-b border-[var(--sidebar-border)] py-0">
          <WorkspaceHeader />
        </SidebarHeader>
        <SidebarContent className="px-1">
          <WorkspaceNavChatList />
          {isSidebarOpen && <RecentChatList />}
        </SidebarContent>
        <SidebarFooter className="border-t border-[var(--sidebar-border)]">
          <WorkspaceNavMenu />
        </SidebarFooter>
        <SidebarRail />
      </Sidebar>
    </>
  );
}
