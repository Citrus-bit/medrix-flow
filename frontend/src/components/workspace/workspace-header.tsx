"use client";

import { MessageSquarePlus } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import { useI18n } from "@/core/i18n/hooks";
import { env } from "@/env";
import { cn } from "@/lib/utils";

import { AnaxaLogoMark } from "./anaxa-logo";

export function WorkspaceHeader({ className }: { className?: string }) {
  const { t } = useI18n();
  const { state } = useSidebar();
  const pathname = usePathname();
  return (
    <>
      <div
        className={cn(
          "group/workspace-header flex h-14 flex-col justify-center",
          className,
        )}
      >
        {state === "collapsed" ? (
          <div className="group-has-data-[collapsible=icon]/sidebar-wrapper:-translate-y flex w-full cursor-pointer items-center justify-center">
            <div className="block pt-1 group-hover/workspace-header:hidden">
              <AnaxaLogoMark className="rounded-lg" size={28} />
            </div>
            <SidebarTrigger className="hidden pl-2 group-hover/workspace-header:block" />
          </div>
        ) : (
          <div className="flex items-center justify-between gap-2">
            {env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" ? (
              <Link href="/" className="ml-2 flex items-center gap-2">
                <AnaxaLogoMark className="rounded-lg" size={28} />
                <span className="bg-gradient-to-r from-[#0891b2] to-[#14b8a6] bg-clip-text text-sm font-semibold tracking-tight text-transparent">
                  Anaxa
                </span>
              </Link>
            ) : (
              <div className="ml-2 flex cursor-default items-center gap-2">
                <AnaxaLogoMark className="rounded-lg" size={28} />
                <span className="bg-gradient-to-r from-[#0891b2] to-[#14b8a6] bg-clip-text text-sm font-semibold tracking-tight text-transparent">
                  Anaxa
                </span>
              </div>
            )}
            <SidebarTrigger />
          </div>
        )}
      </div>
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton
            isActive={pathname === "/workspace/chats/new"}
            asChild
          >
            <Link className="text-muted-foreground" href="/workspace/chats/new">
              <MessageSquarePlus size={16} />
              <span>{t.sidebar.newChat}</span>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </>
  );
}
