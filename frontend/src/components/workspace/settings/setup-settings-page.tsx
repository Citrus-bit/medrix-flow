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
import { Switch } from "@/components/ui/switch";
import { useI18n } from "@/core/i18n/hooks";
import {
  useSaveSetup,
  useSetupConfig,
  useTestModel,
  useTestToolKey,
} from "@/core/setup/hooks";
import type { ModelSetupItem, ToolKeyItem } from "@/core/setup/types";

import { SettingsSection } from "./settings-section";

const PROVIDER_PRESETS: { label: string; value: string; base_url?: string }[] =
  [
    { label: "OpenAI", value: "langchain_openai:ChatOpenAI" },
    {
      label: "OpenAI (Responses API)",
      value: "langchain_openai:ChatOpenAI",
      base_url: undefined,
    },
    {
      label: "Anthropic",
      value: "langchain_anthropic:ChatAnthropic",
    },
    {
      label: "Google Gemini",
      value: "langchain_google_genai:ChatGoogleGenerativeAI",
    },
    {
      label: "DeepSeek",
      value: "medrix_flow.models.patched_deepseek:PatchedChatDeepSeek",
    },
    {
      label: "OpenAI Compatible",
      value: "langchain_openai:ChatOpenAI",
      base_url: "",
    },
  ];

function emptyModel(): ModelSetupItem {
  return {
    name: "",
    display_name: null,
    provider: "langchain_openai:ChatOpenAI",
    model: "",
    base_url: null,
    api_key: null,
    api_key_env_var: null,
    max_tokens: null,
    temperature: null,
    supports_thinking: false,
    supports_vision: false,
  };
}

export function SetupSettingsPage() {
  const { t } = useI18n();
  const { config, isLoading, error } = useSetupConfig();
  const saveMutation = useSaveSetup();

  const [models, setModels] = useState<ModelSetupItem[]>([]);
  const [toolKeys, setToolKeys] = useState<ToolKeyItem[]>([]);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (config) {
      setModels(config.models);
      setToolKeys(config.tool_keys);
      setDirty(false);
    }
  }, [config]);

  const updateModel = useCallback(
    (idx: number, patch: Partial<ModelSetupItem>) => {
      setModels((prev) => prev.map((m, i) => (i === idx ? { ...m, ...patch } : m)));
      setDirty(true);
    },
    [],
  );

  const removeModel = useCallback((idx: number) => {
    setModels((prev) => prev.filter((_, i) => i !== idx));
    setDirty(true);
  }, []);

  const addModel = useCallback(() => {
    setModels((prev) => [...prev, emptyModel()]);
    setDirty(true);
  }, []);

  const updateToolKey = useCallback(
    (idx: number, value: string) => {
      setToolKeys((prev) =>
        prev.map((tk, i) => (i === idx ? { ...tk, api_key: value } : tk)),
      );
      setDirty(true);
    },
    [],
  );

  const handleSave = useCallback(() => {
    saveMutation.mutate(
      { models, tool_keys: toolKeys },
      {
        onSuccess: () => {
          toast.success(t.setup.saveSuccess);
          setDirty(false);
        },
        onError: (err) => toast.error(err.message),
      },
    );
  }, [models, toolKeys, saveMutation, t]);

  if (isLoading) {
    return (
      <SettingsSection title={t.setup.title} description={t.setup.description}>
        <div className="text-muted-foreground text-sm">{t.common.loading}</div>
      </SettingsSection>
    );
  }

  if (error) {
    return (
      <SettingsSection title={t.setup.title} description={t.setup.description}>
        <div className="text-destructive text-sm">Error: {error.message}</div>
      </SettingsSection>
    );
  }

  return (
    <div className="space-y-8">
      <SettingsSection
        title={t.setup.modelsTitle}
        description={t.setup.modelsDescription}
      >
        <div className="space-y-4">
          {models.map((m, idx) => (
            <ModelCard
              key={idx}
              model={m}
              onChange={(patch) => updateModel(idx, patch)}
              onRemove={() => removeModel(idx)}
            />
          ))}
          <Button variant="outline" size="sm" onClick={addModel}>
            <PlusIcon className="size-4" />
            {t.setup.addModel}
          </Button>
        </div>
      </SettingsSection>

      <SettingsSection
        title={t.setup.toolKeysTitle}
        description={t.setup.toolKeysDescription}
      >
        <div className="space-y-4">
          {toolKeys.map((tk, idx) => (
            <ToolKeyCard
              key={tk.service}
              item={tk}
              onChange={(val) => updateToolKey(idx, val)}
            />
          ))}
        </div>
      </SettingsSection>

      <div className="flex items-center gap-3">
        <Button onClick={handleSave} disabled={!dirty || saveMutation.isPending}>
          {saveMutation.isPending && (
            <Loader2Icon className="size-4 animate-spin" />
          )}
          {t.setup.saveAll}
        </Button>
        {!dirty && (
          <span className="text-muted-foreground text-xs">
            {t.setup.noChanges}
          </span>
        )}
      </div>
    </div>
  );
}

function ModelCard({
  model,
  onChange,
  onRemove,
}: {
  model: ModelSetupItem;
  onChange: (patch: Partial<ModelSetupItem>) => void;
  onRemove: () => void;
}) {
  const { t } = useI18n();
  const testMutation = useTestModel();
  const [testStatus, setTestStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [testMsg, setTestMsg] = useState("");

  const handleTest = () => {
    setTestStatus("loading");
    testMutation.mutate(
      {
        provider: model.provider,
        model: model.model,
        api_key: model.api_key,
        base_url: model.base_url,
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

  return (
    <div className="bg-muted/40 space-y-3 rounded-lg border p-4">
      <div className="flex items-start justify-between">
        <div className="grid flex-1 grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium">{t.setup.modelName}</label>
            <Input
              value={model.name}
              onChange={(e) => onChange({ name: e.target.value })}
              placeholder="my-model"
            />
          </div>
          <div>
            <label className="text-xs font-medium">
              {t.setup.displayName}
            </label>
            <Input
              value={model.display_name ?? ""}
              onChange={(e) => onChange({ display_name: e.target.value || null })}
              placeholder="My Model"
            />
          </div>
          <div>
            <label className="text-xs font-medium">{t.setup.provider}</label>
            <Select
              value={model.provider}
              onValueChange={(v) => onChange({ provider: v })}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PROVIDER_PRESETS.map((p) => (
                  <SelectItem key={p.label} value={p.value}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs font-medium">{t.setup.modelId}</label>
            <Input
              value={model.model}
              onChange={(e) => onChange({ model: e.target.value })}
              placeholder="gpt-4"
            />
          </div>
          <div>
            <label className="text-xs font-medium">Base URL</label>
            <Input
              value={model.base_url ?? ""}
              onChange={(e) => onChange({ base_url: e.target.value || null })}
              placeholder="https://api.openai.com/v1"
            />
          </div>
          <div>
            <label className="text-xs font-medium">API Key</label>
            <Input
              type="password"
              value={model.api_key ?? ""}
              onChange={(e) => onChange({ api_key: e.target.value || null })}
              placeholder="sk-..."
            />
          </div>
          <div>
            <label className="text-xs font-medium">Max Tokens</label>
            <Input
              type="number"
              value={model.max_tokens ?? ""}
              onChange={(e) =>
                onChange({
                  max_tokens: e.target.value ? Number(e.target.value) : null,
                })
              }
              placeholder="4096"
            />
          </div>
          <div>
            <label className="text-xs font-medium">Temperature</label>
            <Input
              type="number"
              step="0.1"
              min="0"
              max="2"
              value={model.temperature ?? ""}
              onChange={(e) =>
                onChange({
                  temperature: e.target.value ? Number(e.target.value) : null,
                })
              }
              placeholder="0.7"
            />
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          className="text-muted-foreground hover:text-destructive ml-2 shrink-0"
          onClick={onRemove}
        >
          <Trash2Icon className="size-4" />
        </Button>
      </div>

      <div className="flex items-center gap-4 text-xs">
        <label className="flex items-center gap-1.5">
          <Switch
            checked={model.supports_thinking}
            onCheckedChange={(v) => onChange({ supports_thinking: v })}
          />
          Thinking
        </label>
        <label className="flex items-center gap-1.5">
          <Switch
            checked={model.supports_vision}
            onCheckedChange={(v) => onChange({ supports_vision: v })}
          />
          Vision
        </label>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleTest}
          disabled={testStatus === "loading" || !model.model}
        >
          {testStatus === "loading" ? (
            <Loader2Icon className="size-3.5 animate-spin" />
          ) : (
            <ZapIcon className="size-3.5" />
          )}
          {t.setup.testConnection}
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

function ToolKeyCard({
  item,
  onChange,
}: {
  item: ToolKeyItem;
  onChange: (val: string) => void;
}) {
  const { t } = useI18n();
  const testMutation = useTestToolKey();
  const [testStatus, setTestStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [testMsg, setTestMsg] = useState("");

  const handleTest = () => {
    if (!item.api_key) return;
    setTestStatus("loading");
    testMutation.mutate(
      { service: item.service, api_key: item.api_key },
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

  const label = item.service === "tavily" ? "Tavily" : "Jina";

  return (
    <div className="bg-muted/40 space-y-3 rounded-lg border p-4">
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <label className="text-xs font-medium">
            {label} API Key ({item.env_var})
          </label>
          <Input
            type="password"
            value={item.api_key ?? ""}
            onChange={(e) => onChange(e.target.value)}
            placeholder={`Enter ${label} API key`}
          />
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleTest}
          disabled={testStatus === "loading" || !item.api_key}
        >
          {testStatus === "loading" ? (
            <Loader2Icon className="size-3.5 animate-spin" />
          ) : (
            <ZapIcon className="size-3.5" />
          )}
          {t.setup.testConnection}
        </Button>
      </div>
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
  );
}
