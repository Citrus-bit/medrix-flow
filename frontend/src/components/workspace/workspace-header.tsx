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

function MedrixLogo({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M24 4L42 14v20L24 44 6 34V14L24 4z"
        fill="url(#medrix-grad)"
        opacity="0.1"
      />
      <path
        d="M24 4L42 14v20L24 44 6 34V14L24 4z"
        stroke="url(#medrix-grad)"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M24 16v16M18 24h12"
        stroke="url(#medrix-grad)"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <defs>
        <linearGradient id="medrix-grad" x1="6" y1="4" x2="42" y2="44">
          <stop stopColor="#0891b2" />
          <stop offset="1" stopColor="#14b8a6" />
        </linearGradient>
      </defs>
    </svg>
  );
}

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
              <MedrixLogo className="size-6" />
            </div>
            <SidebarTrigger className="hidden pl-2 group-hover/workspace-header:block" />
          </div>
        ) : (
          <div className="flex items-center justify-between gap-2">
            {env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true" ? (
              <Link href="/" className="ml-2 flex items-center gap-2">
                <MedrixLogo className="size-6" />
                <span className="bg-gradient-to-r from-[#0891b2] to-[#14b8a6] bg-clip-text text-sm font-semibold tracking-tight text-transparent">
                  MedrixFlow
                </span>
              </Link>
            ) : (
              <div className="ml-2 flex cursor-default items-center gap-2">
                <MedrixLogo className="size-6" />
                <span className="bg-gradient-to-r from-[#0891b2] to-[#14b8a6] bg-clip-text text-sm font-semibold tracking-tight text-transparent">
                  MedrixFlow
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
