"use client";

import {
  CheckCircle2Icon,
  Loader2Icon,
  PlusIcon,
  Trash2Icon,
  XCircleIcon,
  ZapIcon,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { useI18n } from "@/core/i18n/hooks";
import {
  useMCPConfig,
  useSaveMCPConfig,
  useTestMCPServer,
} from "@/core/mcp/hooks";
import type { MCPServerConfig, MCPTransportType } from "@/core/mcp/types";
import { env } from "@/env";

import { SettingsErrorState } from "./settings-error-state";
import { SettingsSection } from "./settings-section";

function emptyServer(): MCPServerConfig {
  return {
    enabled: true,
    type: "stdio",
    command: null,
    args: [],
    env: {},
    url: null,
    headers: {},
    description: "",
  };
}

function recordToLines(rec: Record<string, string>, sep: string): string {
  return Object.entries(rec)
    .map(([k, v]) => `${k}${sep}${v}`)
    .join("\n");
}

function linesToRecord(text: string, sep: string): Record<string, string> {
  const result: Record<string, string> = {};
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const idx = trimmed.indexOf(sep);
    if (idx > 0) {
      result[trimmed.slice(0, idx).trim()] = trimmed.slice(idx + sep.length).trim();
    }
  }
  return result;
}

export function ToolSettingsPage() {
  const { t } = useI18n();
  const { config, isLoading, error, refetch } = useMCPConfig();
  const saveMutation = useSaveMCPConfig();
  const isStatic = env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true";

  const [servers, setServers] = useState<Record<string, MCPServerConfig>>({});
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (config) {
      setServers(config.mcp_servers);
      setDirty(false);
    }
  }, [config]);

  const updateServer = useCallback(
    (name: string, patch: Partial<MCPServerConfig>) => {
      setServers((prev) => {
        const current = prev[name];
        if (!current) return prev;
        return {
          ...prev,
          [name]: { ...current, ...patch },
        };
      });
      setDirty(true);
    },
    [],
  );

  const deleteServer = useCallback(
    (name: string) => {
      if (!window.confirm(t.settings.tools.deleteConfirm)) return;
      setServers((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
      setDirty(true);
    },
    [t],
  );

  const addServer = useCallback(() => {
    const baseName = "new-server";
    let name = baseName;
    let i = 1;
    while (servers[name]) {
      name = `${baseName}-${i++}`;
    }
    setServers((prev) => ({ ...prev, [name]: emptyServer() }));
    setDirty(true);
  }, [servers]);

  const renameServer = useCallback(
    (oldName: string, newName: string) => {
      if (!newName.trim() || newName === oldName) return;
      if (servers[newName]) return;
      setServers((prev) => {
        const next: Record<string, MCPServerConfig> = {};
        for (const [k, v] of Object.entries(prev)) {
          next[k === oldName ? newName : k] = v;
        }
        return next;
      });
      setDirty(true);
    },
    [servers],
  );

  const handleSave = useCallback(() => {
    saveMutation.mutate(servers, {
      onSuccess: () => {
        toast.success(t.settings.tools.saveSuccess);
        setDirty(false);
      },
      onError: (err) => toast.error(err.message),
    });
  }, [servers, saveMutation, t]);

  if (isLoading) {
    return (
      <SettingsSection
        title={t.settings.tools.title}
        description={t.settings.tools.description}
      >
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-4 rounded-lg border p-4">
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-32 rounded" />
                <Skeleton className="h-3 w-64 rounded" />
              </div>
              <Skeleton className="h-5 w-9 rounded-full" />
            </div>
          ))}
        </div>
      </SettingsSection>
    );
  }

  if (error) {
    return (
      <SettingsSection
        title={t.settings.tools.title}
        description={t.settings.tools.description}
      >
        <SettingsErrorState error={error} onRetry={() => void refetch()} />
      </SettingsSection>
    );
  }

  const entries = Object.entries(servers);

  return (
    <div className="space-y-8">
      <SettingsSection
        title={t.settings.tools.title}
        description={t.settings.tools.description}
      >
        {entries.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed p-8 text-center">
            <h3 className="text-sm font-medium">{t.settings.tools.emptyTitle}</h3>
            <p className="text-muted-foreground text-sm">
              {t.settings.tools.emptyDescription}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {entries.map(([name, cfg]) => (
              <MCPServerCard
                key={name}
                name={name}
                config={cfg}
                disabled={isStatic}
                onChange={(patch) => updateServer(name, patch)}
                onRename={(newName) => renameServer(name, newName)}
                onDelete={() => deleteServer(name)}
              />
            ))}
          </div>
        )}
        {!isStatic && (
          <Button variant="outline" size="sm" className="mt-4" onClick={addServer}>
            <PlusIcon className="size-4" />
            {t.settings.tools.addServer}
          </Button>
        )}
      </SettingsSection>

      {!isStatic && (
        <div className="flex items-center gap-3">
          <Button onClick={handleSave} disabled={!dirty || saveMutation.isPending}>
            {saveMutation.isPending && (
              <Loader2Icon className="size-4 animate-spin" />
            )}
            {t.settings.tools.saveChanges}
          </Button>
          {!dirty && (
            <span className="text-muted-foreground text-xs">
              {t.settings.tools.noChanges}
            </span>
          )}
        </div>
      )}
    </div>
  );
}


function MCPServerCard({
  name,
  config,
  disabled,
  onChange,
  onRename,
  onDelete,
}: {
  name: string;
  config: MCPServerConfig;
  disabled: boolean;
  onChange: (patch: Partial<MCPServerConfig>) => void;
  onRename: (newName: string) => void;
  onDelete: () => void;
}) {
  const { t } = useI18n();
  const testMutation = useTestMCPServer();
  const [testStatus, setTestStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [testMsg, setTestMsg] = useState("");
  const [editingName, setEditingName] = useState(name);

  const handleTest = () => {
    setTestStatus("loading");
    testMutation.mutate(
      {
        type: config.type,
        command: config.command,
        args: config.args,
        env: config.env,
        url: config.url,
        headers: config.headers,
      },
      {
        onSuccess: (r) => {
          setTestStatus(r.success ? "success" : "error");
          setTestMsg(r.message);
        },
        onError: (err) => {
          setTestStatus("error");
          setTestMsg(err.message);
        },
      },
    );
  };

  const isStdio = config.type === "stdio";
  const isRemote = config.type === "sse" || config.type === "http";

  return (
    <div className="bg-muted/40 space-y-3 rounded-lg border p-4">
      <div className="flex items-start justify-between">
        <div className="grid flex-1 grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium">
              {t.settings.tools.serverName}
            </label>
            <Input
              value={editingName}
              disabled={disabled}
              onChange={(e) => setEditingName(e.target.value)}
              onBlur={() => onRename(editingName)}
              placeholder={t.settings.tools.serverNamePlaceholder}
            />
          </div>
          <div>
            <label className="text-xs font-medium">
              {t.settings.tools.transportType}
            </label>
            <Select
              value={config.type}
              disabled={disabled}
              onValueChange={(v) =>
                onChange({ type: v as MCPTransportType })
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="stdio">stdio</SelectItem>
                <SelectItem value="sse">sse</SelectItem>
                <SelectItem value="http">http</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {isStdio && (
            <>
              <div>
                <label className="text-xs font-medium">
                  {t.settings.tools.command}
                </label>
                <Input
                  value={config.command ?? ""}
                  disabled={disabled}
                  onChange={(e) =>
                    onChange({ command: e.target.value || null })
                  }
                  placeholder={t.settings.tools.commandPlaceholder}
                />
              </div>
              <div>
                <label className="text-xs font-medium">
                  {t.settings.tools.arguments}
                </label>
                <Textarea
                  className="min-h-[60px] font-mono text-xs"
                  value={config.args.join("\n")}
                  disabled={disabled}
                  onChange={(e) =>
                    onChange({
                      args: e.target.value
                        .split("\n")
                        .filter((a) => a.length > 0),
                    })
                  }
                  placeholder={t.settings.tools.argumentsPlaceholder}
                />
              </div>
            </>
          )}

          {isRemote && (
            <div className="col-span-2">
              <label className="text-xs font-medium">
                {t.settings.tools.serverUrl}
              </label>
              <Input
                value={config.url ?? ""}
                disabled={disabled}
                onChange={(e) =>
                  onChange({ url: e.target.value || null })
                }
                placeholder={t.settings.tools.serverUrlPlaceholder}
              />
            </div>
          )}

          <div className={isRemote ? "col-span-1" : ""}>
            <label className="text-xs font-medium">
              {t.settings.tools.envVars}
            </label>
            <Textarea
              className="min-h-[60px] font-mono text-xs"
              value={recordToLines(config.env, "=")}
              disabled={disabled}
              onChange={(e) =>
                onChange({ env: linesToRecord(e.target.value, "=") })
              }
              placeholder={t.settings.tools.envVarsPlaceholder}
            />
          </div>

          {isRemote && (
            <div>
              <label className="text-xs font-medium">
                {t.settings.tools.httpHeaders}
              </label>
              <Textarea
                className="min-h-[60px] font-mono text-xs"
                value={recordToLines(config.headers, ": ")}
                disabled={disabled}
                onChange={(e) =>
                  onChange({
                    headers: linesToRecord(e.target.value, ": "),
                  })
                }
                placeholder={t.settings.tools.headersPlaceholder}
              />
            </div>
          )}

          <div className="col-span-2">
            <label className="text-xs font-medium">
              {t.settings.tools.descriptionLabel}
            </label>
            <Input
              value={config.description}
              disabled={disabled}
              onChange={(e) => onChange({ description: e.target.value })}
              placeholder={t.settings.tools.descriptionPlaceholder}
            />
          </div>
        </div>

        <div className="ml-2 flex shrink-0 flex-col items-center gap-2">
          <Switch
            checked={config.enabled}
            disabled={disabled}
            onCheckedChange={(v) => onChange({ enabled: v })}
          />
          <Button
            variant="ghost"
            size="icon-sm"
            className="text-muted-foreground hover:text-destructive"
            disabled={disabled}
            onClick={onDelete}
          >
            <Trash2Icon className="size-4" />
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleTest}
          disabled={disabled || testStatus === "loading"}
        >
          {testStatus === "loading" ? (
            <Loader2Icon className="size-3.5 animate-spin" />
          ) : (
            <ZapIcon className="size-3.5" />
          )}
          {t.settings.tools.testConnection}
        </Button>
        {testStatus === "success" && (
          <span className="flex items-center gap-1 text-xs text-green-600">
            <CheckCircle2Icon className="size-3.5" /> {testMsg}
          </span>
        )}
        {testStatus === "error" && (
          <span className="flex items-center gap-1 text-xs text-red-500">
            <XCircleIcon className="size-3.5" /> {testMsg}
          </span>
        )}
      </div>
    </div>
  );
}
