import { describe, expect, it } from "vitest";

import {
  getActiveImageProviderMissingFields,
  normalizeImageProviderBaseUrl,
} from "./image-generation";
import type { ImageGenerationConfig } from "./types";

function makeConfig(activeProvider: "google-ai-studio" | "openai-compatible"): ImageGenerationConfig {
  return {
    active_provider: activeProvider,
    google_ai_studio: {
      provider: "google-ai-studio",
      enabled: activeProvider === "google-ai-studio",
      model: "gemini-3-pro-image-preview",
      base_url: null,
      api_key: "google-key",
      api_key_env_var: "GEMINI_API_KEY",
    },
    openai_compatible: {
      provider: "openai-compatible",
      enabled: activeProvider === "openai-compatible",
      model: "gpt-image-1",
      base_url: "https://images.example.com/v1/",
      api_key: "openai-key",
      api_key_env_var: "IMAGE_GEN_OPENAI_API_KEY",
    },
  };
}

describe("image generation setup helpers", () => {
  it("normalizes trailing slashes in base URLs", () => {
    expect(normalizeImageProviderBaseUrl("https://images.example.com/v1/")).toBe(
      "https://images.example.com/v1",
    );
  });

  it("requires model and api key for the active google provider", () => {
    const config = makeConfig("google-ai-studio");
    config.google_ai_studio.model = null;
    config.google_ai_studio.api_key = null;

    expect(getActiveImageProviderMissingFields(config)).toEqual(["model", "api_key"]);
  });

  it("requires model, base URL, and api key for the active openai-compatible provider", () => {
    const config = makeConfig("openai-compatible");
    config.openai_compatible.model = null;
    config.openai_compatible.base_url = "   ";
    config.openai_compatible.api_key = null;

    expect(getActiveImageProviderMissingFields(config)).toEqual([
      "model",
      "base_url",
      "api_key",
    ]);
  });
});
