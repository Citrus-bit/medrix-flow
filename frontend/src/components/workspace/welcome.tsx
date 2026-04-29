"use client";

import {
  ActivityIcon,
  AlertTriangleIcon,
  BrainIcon,
  SearchIcon,
  SettingsIcon,
} from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/core/i18n/hooks";
import { useModels } from "@/core/models/hooks";
import { dispatchOpenSettings } from "@/core/settings/events";
import { cn } from "@/lib/utils";

let waved = false;

function MedrixHexIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M24 4L42 14v20L24 44 6 34V14L24 4z"
        fill="url(#hex-grad)"
        opacity="0.1"
      />
      <path
        d="M24 4L42 14v20L24 44 6 34V14L24 4z"
        stroke="url(#hex-grad)"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M24 16v16M18 24h12"
        stroke="url(#hex-grad)"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <defs>
        <linearGradient id="hex-grad" x1="6" y1="4" x2="42" y2="44">
          <stop stopColor="#0891b2" />
          <stop offset="1" stopColor="#14b8a6" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export function Welcome({
  className,
  mode,
}: {
  className?: string;
  mode?: "ultra" | "pro" | "thinking" | "flash";
}) {
  const { t } = useI18n();
  const searchParams = useSearchParams();
  const { models, isLoading } = useModels();
  const isUltra = useMemo(() => mode === "ultra", [mode]);
  const showModelWarning = !isLoading && models.length === 0;
  useEffect(() => {
    waved = true;
  }, []);
  return (
    <div
      className={cn(
        "mx-auto flex w-full max-w-2xl flex-col items-center justify-center gap-6 px-8 py-8 text-center",
        className,
      )}
    >
      <div className={cn("inline-block", !waved ? "animate-wave" : "")}>
        <MedrixHexIcon className="size-14" />
      </div>
      {searchParams.get("mode") === "skill" ? (
        <>
          <div className="text-xl font-semibold tracking-tight">
            {t.welcome.createYourOwnSkill}
          </div>
          <div className="text-muted-foreground text-sm leading-relaxed">
            {t.welcome.createYourOwnSkillDescription.includes("\n") ? (
              <pre className="font-sans whitespace-pre">
                {t.welcome.createYourOwnSkillDescription}
              </pre>
            ) : (
              <p>{t.welcome.createYourOwnSkillDescription}</p>
            )}
          </div>
        </>
      ) : (
        <>
          <div>
            <h1
              className={cn(
                "text-2xl font-semibold tracking-tight",
                isUltra
                  ? "bg-gradient-to-r from-[#0891b2] via-[#22d3ee] to-[#14b8a6] bg-clip-text text-transparent"
                  : "text-foreground",
              )}
            >
              {t.welcome.greeting}
            </h1>
            <div className="text-muted-foreground mt-2 text-sm leading-relaxed">
              {t.welcome.description.includes("\n") ? (
                <pre className="whitespace-pre">{t.welcome.description}</pre>
              ) : (
                <p>{t.welcome.description}</p>
              )}
            </div>
          </div>
          <div className="mt-2 flex items-center gap-6">
            <div className="flex flex-col items-center gap-1.5">
              <div className="flex size-10 items-center justify-center rounded-xl bg-[#0891b2]/10">
                <SearchIcon className="size-5 text-[#0891b2]" />
              </div>
              <span className="text-muted-foreground text-xs">Research</span>
            </div>
            <div className="flex flex-col items-center gap-1.5">
              <div className="flex size-10 items-center justify-center rounded-xl bg-[#14b8a6]/10">
                <BrainIcon className="size-5 text-[#14b8a6]" />
              </div>
              <span className="text-muted-foreground text-xs">Analyze</span>
            </div>
            <div className="flex flex-col items-center gap-1.5">
              <div className="flex size-10 items-center justify-center rounded-xl bg-[#06b6d4]/10">
                <ActivityIcon className="size-5 text-[#06b6d4]" />
              </div>
              <span className="text-muted-foreground text-xs">Insights</span>
            </div>
          </div>
        </>
      )}
      {showModelWarning && (
        <Alert variant="destructive" className="mt-4 w-full text-left">
          <AlertTriangleIcon className="size-4" />
          <AlertTitle>{t.setup.noModelsConfigured}</AlertTitle>
          <AlertDescription>
            <p>{t.setup.noModelsConfiguredHint}</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => dispatchOpenSettings({ section: "setup" })}
            >
              <SettingsIcon className="mr-1.5 size-3.5" />
              {t.setup.openSettings}
            </Button>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
