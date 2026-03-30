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
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M12 2L3 7v10l9 5 9-5V7l-9-5z"
        fill="url(#medrix-grad)"
        opacity="0.15"
      />
      <path
        d="M12 2L3 7v10l9 5 9-5V7l-9-5z"
        stroke="url(#medrix-grad)"
        strokeWidth="1.5"
        fill="none"
      />
      <path
        d="M12 8v8M9 11h6M8 14h8"
        stroke="url(#medrix-grad)"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <defs>
        <linearGradient id="medrix-grad" x1="3" y1="2" x2="21" y2="22">
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
