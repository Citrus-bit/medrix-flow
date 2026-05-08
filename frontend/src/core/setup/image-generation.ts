import type { ImageGenerationConfig, ImageProviderKind } from "./types";

export type ImageProviderField = "model" | "api_key" | "base_url";

export function normalizeImageProviderBaseUrl(baseUrl: string | null): string | null {
  if (!baseUrl) {
    return null;
  }
  const normalized = baseUrl.trim().replace(/\/+$/, "");
  return normalized || null;
}

export function getActiveImageProviderMissingFields(
  config: ImageGenerationConfig,
): ImageProviderField[] {
  const activeProvider: ImageProviderKind = config.active_provider;
  if (activeProvider === "google-ai-studio") {
    return [
      ...(!config.google_ai_studio.model?.trim() ? ["model" as const] : []),
      ...(!config.google_ai_studio.api_key?.trim() ? ["api_key" as const] : []),
    ];
  }

  return [
    ...(!config.openai_compatible.model?.trim() ? ["model" as const] : []),
    ...(!normalizeImageProviderBaseUrl(config.openai_compatible.base_url) ? ["base_url" as const] : []),
    ...(!config.openai_compatible.api_key?.trim() ? ["api_key" as const] : []),
  ];
}
