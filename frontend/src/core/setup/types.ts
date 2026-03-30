export interface ModelSetupItem {
  name: string;
  display_name: string | null;
  provider: string;
  model: string;
  base_url: string | null;
  api_key: string | null;
  api_key_env_var: string | null;
  max_tokens: number | null;
  temperature: number | null;
  supports_thinking: boolean;
  supports_vision: boolean;
}

export interface ToolKeyItem {
  service: string;
  api_key: string | null;
  env_var: string;
}

export interface SetupConfig {
  models: ModelSetupItem[];
  tool_keys: ToolKeyItem[];
}

export interface SaveModelsRequest {
  models: ModelSetupItem[];
  tool_keys: ToolKeyItem[] | null;
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

export interface TestResult {
  success: boolean;
  message: string;
}
