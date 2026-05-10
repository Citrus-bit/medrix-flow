"use client";

import { ArrowLeftIcon, BotIcon } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { useI18n } from "@/core/i18n/hooks";

export default function NewAgentPage() {
  const { t } = useI18n();
  const router = useRouter();

  return (
    <div className="flex size-full flex-col">
      <header className="flex shrink-0 items-center gap-3 border-b px-4 py-3">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => router.push("/workspace/agents")}
        >
          <ArrowLeftIcon className="h-4 w-4" />
        </Button>
        <h1 className="text-sm font-semibold">{t.agents.createPageTitle}</h1>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center px-4">
        <div className="w-full max-w-sm space-y-4 text-center">
          <div className="space-y-3">
            <div className="bg-primary/10 mx-auto flex h-14 w-14 items-center justify-center rounded-full">
              <BotIcon className="text-primary h-7 w-7" />
            </div>
            <div className="space-y-1">
              <h2 className="text-xl font-semibold">
                {t.agents.readonlyCreateTitle}
              </h2>
              <p className="text-muted-foreground text-sm">
                {t.agents.readonlyCreateDescription}
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            onClick={() => router.push("/workspace/chats/new")}
          >
            {t.agents.backToGallery}
          </Button>
        </div>
      </main>
    </div>
  );
}
