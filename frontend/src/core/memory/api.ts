import { fetchWithTimeout } from "@/core/api/fetch";
import { getBackendBaseURL } from "@/core/config";

import type { UserMemory } from "./types";

export async function loadMemory() {
  const memory = await fetchWithTimeout(`${getBackendBaseURL()}/api/memory`);
  const json = await memory.json();
  return json as UserMemory;
}
