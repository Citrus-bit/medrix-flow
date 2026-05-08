import { fetchWithTimeout } from "@/core/api/fetch";
import { getBackendBaseURL } from "@/core/config";

import type {
  SaveModelsRequest,
  SetupConfig,
  TestImageProviderRequest,
  TestModelRequest,
  TestResult,
  TestToolKeyRequest,
} from "./types";

const base = () => getBackendBaseURL();

async function buildApiError(res: Response, fallback: string): Promise<Error> {
  try {
    const payload = (await res.json()) as { detail?: string };
    if (payload?.detail) {
      return new Error(payload.detail);
    }
  } catch {
    // Ignore response parsing failures and fall back to the generic message.
  }
  return new Error(fallback);
}

export async function loadSetupConfig(): Promise<SetupConfig> {
  const res = await fetchWithTimeout(`${base()}/api/setup/config`);
  if (!res.ok) throw new Error(`Failed to load setup config: ${res.status}`);
  return res.json() as Promise<SetupConfig>;
}

export async function saveSetupModels(req: SaveModelsRequest): Promise<{ success: boolean; message: string }> {
  const res = await fetchWithTimeout(`${base()}/api/setup/models`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw await buildApiError(res, `Failed to save config: ${res.status}`);
  return res.json() as Promise<{ success: boolean; message: string }>;
}

export async function testModel(req: TestModelRequest): Promise<TestResult> {
  const res = await fetchWithTimeout(`${base()}/api/setup/test-model`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    timeoutMs: 30_000,
  });
  if (!res.ok) throw await buildApiError(res, `Test request failed: ${res.status}`);
  return res.json() as Promise<TestResult>;
}

export async function testToolKey(req: TestToolKeyRequest): Promise<TestResult> {
  const res = await fetchWithTimeout(`${base()}/api/setup/test-tool-key`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    timeoutMs: 30_000,
  });
  if (!res.ok) throw await buildApiError(res, `Test request failed: ${res.status}`);
  return res.json() as Promise<TestResult>;
}

export async function testImageProvider(req: TestImageProviderRequest): Promise<TestResult> {
  const res = await fetchWithTimeout(`${base()}/api/setup/test-image-provider`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    timeoutMs: 30_000,
  });
  if (!res.ok) throw await buildApiError(res, `Test request failed: ${res.status}`);
  return res.json() as Promise<TestResult>;
}
