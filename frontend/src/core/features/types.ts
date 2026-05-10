export interface FeatureAgent {
  name: string;
  description: string;
  model: string | null;
  tool_groups: string[] | null;
  kind: "system" | "custom" | string;
  readonly: boolean;
}

export interface RedactedConfigKey {
  key: string;
  configured: boolean;
}

export interface FeatureTool {
  name: string;
  enabled: boolean;
  transport: string;
  description: string;
  command: string | null;
  url: string | null;
  args: string[];
  env_keys: RedactedConfigKey[];
  header_keys: RedactedConfigKey[];
  oauth_enabled: boolean;
}

export interface FeatureSkill {
  name: string;
  description: string;
  license: string | null;
  category: "public" | "custom" | string;
  enabled: boolean;
}

export interface FeaturesInventory {
  agents: FeatureAgent[];
  tools: FeatureTool[];
  skills: FeatureSkill[];
}
