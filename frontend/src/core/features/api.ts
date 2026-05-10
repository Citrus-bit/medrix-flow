import { fetchWithTimeout } from "@/core/api/fetch";
import { getBackendBaseURL } from "@/core/config";

import type { FeaturesInventory } from "./types";

export async function loadFeatures(): Promise<FeaturesInventory> {
  const response = await fetchWithTimeout(`${getBackendBaseURL()}/api/features`);
  if (!response.ok) {
    throw new Error(`Failed to load features: ${response.status}`);
  }
  return response.json() as Promise<FeaturesInventory>;
}
