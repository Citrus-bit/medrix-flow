import { fetchWithTimeout } from "@/core/api/fetch";
import { getBackendBaseURL } from "@/core/config";

import type { MCPConfig, MCPTestRequest, MCPTestResponse } from "./types";

export async function loadMCPConfig() {
  const response = await fetchWithTimeout(`${getBackendBaseURL()}/api/mcp/config`);
  return response.json() as Promise<MCPConfig>;
}

export async function updateMCPConfig(config: MCPConfig) {
  const response = await fetchWithTimeout(`${getBackendBaseURL()}/api/mcp/config`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(config),
    },
  );
  return response.json();
}

export async function testMCPServer(request: MCPTestRequest): Promise<MCPTestResponse> {
  const response = await fetchWithTimeout(`${getBackendBaseURL()}/api/mcp/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  return response.json() as Promise<MCPTestResponse>;
}
