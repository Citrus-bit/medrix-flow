export type MCPTransportType = "stdio" | "sse" | "http";

export interface MCPServerConfig {
  enabled: boolean;
  type: MCPTransportType;
  command: string | null;
  args: string[];
  env: Record<string, string>;
  url: string | null;
  headers: Record<string, string>;
  description: string;
}

export interface MCPConfig {
  mcp_servers: Record<string, MCPServerConfig>;
}

export interface MCPTestRequest {
  type: MCPTransportType;
  command?: string | null;
  args?: string[];
  env?: Record<string, string>;
  url?: string | null;
  headers?: Record<string, string>;
}

export interface MCPTestResponse {
  success: boolean;
  message: string;
}
