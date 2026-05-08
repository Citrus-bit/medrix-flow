"use client";

import {
  CheckCircle2Icon,
  EyeIcon,
  EyeOffIcon,
  Loader2Icon,
  PlusIcon,
  RefreshCwIcon,
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
import { useI18n } from "@/core/i18n/hooks";
import {
  getActiveImageProviderMissingFields,
  normalizeImageProviderBaseUrl,
} from "@/core/setup/image-generation";
import {
  useSaveSetup,
  useSetupConfig,
  useTestImageProvider,
  useTestModel,
  useTestToolKey,
} from "@/core/setup/hooks";
import type {
  ImageGenerationConfig,
  ImageProviderConfig,
  ImageProviderKind,
  ModelSetupItem,
  ToolKeyItem,
} from "@/core/setup/types";

import { SettingsSection } from "./settings-section";

const PROVIDER_PRESETS: {
  key: string;
  label: string;
  provider: string;
}[] = [
  { key: "openai", label: "OpenAI", provider: "langchain_openai:ChatOpenAI" },
  {
    key: "anthropic",
    label: "Anthropic",
    provider: "langchain_anthropic:ChatAnthropic",
  },
  {
    key: "google",
    label: "Google Gemini",
    provider: "langchain_google_genai:ChatGoogleGenerativeAI",
  },
  {
    key: "deepseek",
    label: "DeepSeek",
    provider: "medrix_flow.models.patched_deepseek:PatchedChatDeepSeek",
  },
  {
    key: "openai-compatible",
    label: "OpenAI Compatible",
    provider: "langchain_openai:ChatOpenAI",
  },
];

function inferPresetKey(provider: string, baseUrl: string | null): string {
  if (provider === "langchain_openai:ChatOpenAI" && baseUrl) {
    return "openai-compatible";
  }
  const match = PROVIDER_PRESETS.find(
    (p) => p.provider === provider && p.key !== "openai-compatible",
  );
  return match?.key ?? "openai";
}

function emptyModel(): ModelSetupItem {
  return {
    name: "",
    provider: "langchain_openai:ChatOpenAI",
    model: "",
    base_url: null,
    api_key: null,
    api_key_env_var: null,
    max_tokens: null,
    temperature: null,
    supports_thinking: true,
    supports_reasoning_effort: false,
    supports_vision: true,
  };
}

function imageProviderKey(provider: ImageProviderKind): "google_ai_studio" | "openai_compatible" {
  return provider === "google-ai-studio" ? "google_ai_studio" : "openai_compatible";
}

export function SetupSettingsPage() {
  const { t } = useI18n();
  const { config, isLoading, error, refetch } = useSetupConfig();
  const saveMutation = useSaveSetup();

  const [models, setModels] = useState<ModelSetupItem[]>([]);
  const [toolKeys, setToolKeys] = useState<ToolKeyItem[]>([]);
  const [imageGeneration, setImageGeneration] = useState<ImageGenerationConfig | null>(null);
  const [dirty, setDirty] = useState(false);
  const [imageValidationError, setImageValidationError] = useState("");
  const [loadingSlow, setLoadingSlow] = useState(false);

  useEffect(() => {
    if (isLoading) {
      const timer = setTimeout(() => setLoadingSlow(true), 10_000);
      return () => clearTimeout(timer);
    }
    setLoadingSlow(false);
  }, [isLoading]);

  useEffect(() => {
    if (config) {
      setModels(config.models);
      setToolKeys(config.tool_keys);
      setImageGeneration(config.image_generation);
      setDirty(false);
      setImageValidationError("");
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

  const updateActiveImageProvider = useCallback((provider: ImageProviderKind) => {
    setImageGeneration((prev) => {
      if (!prev) {
        return prev;
      }
      return {
        ...prev,
        active_provider: provider,
        google_ai_studio: {
          ...prev.google_ai_studio,
          enabled: provider === "google-ai-studio",
        },
        openai_compatible: {
          ...prev.openai_compatible,
          enabled: provider === "openai-compatible",
        },
      };
    });
    setImageValidationError("");
    setDirty(true);
  }, []);

  const updateImageProvider = useCallback(
    (provider: ImageProviderKind, patch: Partial<ImageProviderConfig>) => {
      setImageGeneration((prev) => {
        if (!prev) {
          return prev;
        }
        const key = imageProviderKey(provider);
        return {
          ...prev,
          [key]: {
            ...prev[key],
            ...patch,
          },
        };
      });
      setImageValidationError("");
      setDirty(true);
    },
    [],
  );

  const handleSave = useCallback(() => {
    if (!imageGeneration) {
      return;
    }
    const missingFields = getActiveImageProviderMissingFields(imageGeneration);
    if (missingFields.length > 0) {
      const fieldLabels = missingFields.map((field) =>
        field === "model"
          ? t.setup.model
          : field === "api_key"
            ? t.setup.apiKey
            : t.setup.baseUrl,
      );
      const message = `${t.setup.imageGenerationMissingFields} ${fieldLabels.join(", ")}`;
      setImageValidationError(message);
      toast.error(message);
      return;
    }
    saveMutation.mutate(
      { models, tool_keys: toolKeys, image_generation: imageGeneration },
      {
        onSuccess: () => {
          toast.success(t.setup.saveSuccess);
          setDirty(false);
          setImageValidationError("");
        },
        onError: (err) => toast.error(err.message),
      },
    );
  }, [imageGeneration, models, toolKeys, saveMutation, t]);

  if (isLoading) {
    return (
      <div className="space-y-8">
        <SettingsSection title={t.setup.modelsTitle} description={t.setup.modelsDescription}>
          <div className="space-y-4">
            {[1, 2].map((i) => (
              <div key={i} className="bg-muted/40 space-y-3 rounded-lg border p-4">
                <div className="grid grid-cols-2 gap-3">
                  <Skeleton className="h-9 w-full rounded-md" />
                  <Skeleton className="h-9 w-full rounded-md" />
                  <Skeleton className="h-9 w-full rounded-md" />
                  <Skeleton className="h-9 w-full rounded-md" />
                </div>
                <Skeleton className="h-8 w-24 rounded-md" />
              </div>
            ))}
          </div>
        </SettingsSection>

        <SettingsSection title={t.setup.toolKeysTitle} description={t.setup.toolKeysDescription}>
          <div className="space-y-4">
            {[1, 2].map((i) => (
              <div key={i} className="bg-muted/40 space-y-3 rounded-lg border p-4">
                <Skeleton className="h-9 w-full rounded-md" />
              </div>
            ))}
          </div>
        </SettingsSection>

        {loadingSlow && (
          <div className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950/30">
            <Loader2Icon className="text-amber-600 dark:text-amber-400 size-4 animate-spin" />
            <div className="flex-1">
              <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                {t.setup.loadingSlow}
              </p>
              <p className="text-muted-foreground text-xs">
                {t.setup.loadingSlowHint}
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCwIcon className="size-3.5" />
              {t.setup.retry}
            </Button>
          </div>
        )}
      </div>
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

      {imageGeneration && (
        <SettingsSection
          title={t.setup.imageGenerationTitle}
          description={t.setup.imageGenerationDescription}
        >
          <ImageGenerationSection
            config={imageGeneration}
            validationError={imageValidationError}
            onActiveProviderChange={updateActiveImageProvider}
            onProviderChange={updateImageProvider}
          />
        </SettingsSection>
      )}

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

function ImageGenerationSection({
  config,
  validationError,
  onActiveProviderChange,
  onProviderChange,
}: {
  config: ImageGenerationConfig;
  validationError: string;
  onActiveProviderChange: (provider: ImageProviderKind) => void;
  onProviderChange: (provider: ImageProviderKind, patch: Partial<ImageProviderConfig>) => void;
}) {
  const { t } = useI18n();

  return (
    <div className="space-y-4">
      <div>
        <label className="text-xs font-medium">{t.setup.activeImageProvider}</label>
        <Select
          value={config.active_provider}
          onValueChange={(value) => onActiveProviderChange(value as ImageProviderKind)}
        >
          <SelectTrigger className="mt-1 w-full sm:w-[320px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="google-ai-studio">{t.setup.googleAiStudio}</SelectItem>
            <SelectItem value="openai-compatible">{t.setup.openaiCompatible}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <ImageProviderCard
        label={t.setup.googleAiStudio}
        config={config.google_ai_studio}
        active={config.active_provider === "google-ai-studio"}
        onChange={(patch) => onProviderChange("google-ai-studio", patch)}
      />
      <ImageProviderCard
        label={t.setup.openaiCompatible}
        config={config.openai_compatible}
        active={config.active_provider === "openai-compatible"}
        onChange={(patch) => onProviderChange("openai-compatible", patch)}
      />

      {validationError && (
        <div className="text-xs text-red-500">{validationError}</div>
      )}
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
  const [showKey, setShowKey] = useState(false);
  const [presetKey, setPresetKey] = useState(() =>
    inferPresetKey(model.provider, model.base_url),
  );

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
            <label className="text-xs font-medium">{t.setup.model}</label>
            <Input
              value={model.model}
              onChange={(e) => onChange({ model: e.target.value, name: e.target.value })}
              placeholder="gpt-4o"
            />
          </div>
          <div>
            <label className="text-xs font-medium">{t.setup.provider}</label>
            <Select
              value={presetKey}
              onValueChange={(key) => {
                setPresetKey(key);
                const preset = PROVIDER_PRESETS.find((p) => p.key === key);
                if (preset) {
                  onChange({ provider: preset.provider });
                }
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PROVIDER_PRESETS.map((p) => (
                  <SelectItem key={p.key} value={p.key}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
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
            <div className="flex items-center gap-1.5">
              <Input
                type={showKey ? "text" : "password"}
                value={model.api_key ?? ""}
                onChange={(e) => onChange({ api_key: e.target.value || null })}
                placeholder="sk-..."
              />
              <button
                type="button"
                onClick={() => setShowKey((v) => !v)}
                className="text-muted-foreground hover:text-foreground shrink-0 p-1 transition-colors"
              >
                {showKey ? (
                  <EyeOffIcon className="size-4" />
                ) : (
                  <EyeIcon className="size-4" />
                )}
              </button>
            </div>
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
  const [showKey, setShowKey] = useState(false);

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

  const serviceMeta =
    item.service === "tavily"
      ? { label: "Tavily", placeholder: "Enter Tavily API key" }
      : item.service === "jina"
        ? { label: "Jina", placeholder: "Enter Jina API key" }
        : item.service === "openalex"
          ? { label: "OpenAlex", placeholder: "Enter OpenAlex API key" }
          : { label: "Semantic Scholar", placeholder: "Enter Semantic Scholar API key" };
  const label = serviceMeta.label;
  const envLabel = item.env_var;

  return (
    <div className="bg-muted/40 space-y-3 rounded-lg border p-4">
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <label className="text-xs font-medium">
            {label} API Key ({envLabel})
          </label>
          <div className="flex items-center gap-1.5">
            <Input
              type={showKey ? "text" : "password"}
              value={item.api_key ?? ""}
              onChange={(e) => onChange(e.target.value)}
              placeholder={serviceMeta.placeholder}
            />
            <button
              type="button"
              onClick={() => setShowKey((v) => !v)}
              className="text-muted-foreground hover:text-foreground shrink-0 p-1 transition-colors"
            >
              {showKey ? (
                <EyeOffIcon className="size-4" />
              ) : (
                <EyeIcon className="size-4" />
              )}
            </button>
          </div>
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

function ImageProviderCard({
  label,
  config,
  active,
  onChange,
}: {
  label: string;
  config: ImageProviderConfig;
  active: boolean;
  onChange: (patch: Partial<ImageProviderConfig>) => void;
}) {
  const { t } = useI18n();
  const testMutation = useTestImageProvider();
  const [testStatus, setTestStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [testMsg, setTestMsg] = useState("");
  const [showKey, setShowKey] = useState(false);

  const handleTest = () => {
    if (!config.api_key || !config.model) return;
    setTestStatus("loading");
    testMutation.mutate(
      {
        provider: config.provider,
        model: config.model,
        api_key: config.api_key,
        base_url: normalizeImageProviderBaseUrl(config.base_url),
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
  const isTestDisabled =
    testStatus === "loading" ||
    !config.api_key ||
    !config.model ||
    (config.provider === "openai-compatible" && !normalizeImageProviderBaseUrl(config.base_url));

  return (
    <div className={`bg-muted/40 space-y-3 rounded-lg border p-4 ${active ? "border-primary/60" : ""}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-medium">{label}</h4>
            {active && (
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-medium text-emerald-700">
                {t.setup.activeProviderBadge}
              </span>
            )}
          </div>
          <p className="text-muted-foreground mt-1 text-xs">{config.api_key_env_var}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {config.provider === "openai-compatible" && (
          <div>
            <label className="text-xs font-medium">{t.setup.baseUrl}</label>
            <Input
              value={config.base_url ?? ""}
              onChange={(e) => onChange({ base_url: e.target.value || null })}
              placeholder="https://api.example.com/v1"
            />
          </div>
        )}
        <div>
          <label className="text-xs font-medium">{t.setup.model}</label>
          <Input
            value={config.model ?? ""}
            onChange={(e) => onChange({ model: e.target.value || null })}
            placeholder={config.provider === "google-ai-studio" ? "gemini-3-pro-image-preview" : "gpt-image-1"}
          />
        </div>
        <div className={config.provider === "google-ai-studio" ? "" : "md:col-span-2"}>
          <label className="text-xs font-medium">{t.setup.apiKey}</label>
          <div className="flex items-center gap-1.5">
            <Input
              type={showKey ? "text" : "password"}
              value={config.api_key ?? ""}
              onChange={(e) => onChange({ api_key: e.target.value || null })}
              placeholder={config.provider === "google-ai-studio" ? "AIza..." : "sk-..."}
            />
            <button
              type="button"
              onClick={() => setShowKey((v) => !v)}
              className="text-muted-foreground hover:text-foreground shrink-0 p-1 transition-colors"
            >
              {showKey ? (
                <EyeOffIcon className="size-4" />
              ) : (
                <EyeIcon className="size-4" />
              )}
            </button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleTest}
              disabled={isTestDisabled}
            >
              {testStatus === "loading" ? (
                <Loader2Icon className="size-3.5 animate-spin" />
              ) : (
                <ZapIcon className="size-3.5" />
              )}
              {t.setup.testConnection}
            </Button>
          </div>
        </div>
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
