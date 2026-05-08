export interface ModelSetupItem {
  name: string;
  provider: string;
  model: string;
  base_url: string | null;
  api_key: string | null;
  api_key_env_var: string | null;
  max_tokens: number | null;
  temperature: number | null;
  supports_thinking: boolean;
  supports_reasoning_effort: boolean;
  supports_vision: boolean;
}

export interface ToolKeyItem {
  service: string;
  api_key: string | null;
  env_var: string;
}

export type ImageProviderKind = "google-ai-studio" | "openai-compatible";

export interface ImageProviderConfig {
  provider: ImageProviderKind;
  enabled: boolean;
  model: string | null;
  base_url: string | null;
  api_key: string | null;
  api_key_env_var: string;
}

export interface ImageGenerationConfig {
  active_provider: ImageProviderKind;
  google_ai_studio: ImageProviderConfig;
  openai_compatible: ImageProviderConfig;
}

export interface SetupConfig {
  models: ModelSetupItem[];
  tool_keys: ToolKeyItem[];
  image_generation: ImageGenerationConfig;
}

export interface SaveModelsRequest {
  models: ModelSetupItem[];
  tool_keys: ToolKeyItem[] | null;
  image_generation: ImageGenerationConfig | null;
}

export interface TestModelRequest {
  provider: string;
  model: string;
  api_key: string | null;
  base_url: string | null;
}

export interface TestToolKeyRequest {
  service: string;
  api_key: string;
}

export interface TestImageProviderRequest {
  provider: ImageProviderKind;
  model: string;
  api_key: string;
  base_url: string | null;
}

export interface TestResult {
  success: boolean;
  message: string;
}
