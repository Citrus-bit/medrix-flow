import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { loadMCPConfig, testMCPServer, updateMCPConfig } from "./api";
import type { MCPServerConfig, MCPTestRequest } from "./types";

export const mcpConfigQueryOptions = {
  queryKey: ["mcpConfig"],
  queryFn: () => loadMCPConfig(),
  staleTime: 30_000,
  retry: 2,
  retryDelay: 1_000,
} as const;

export function useMCPConfig() {
  const { data, isLoading, error, refetch } = useQuery(mcpConfigQueryOptions);
  return { config: data, isLoading, error, refetch };
}

export function useEnableMCPServer() {
  const queryClient = useQueryClient();
  const { config } = useMCPConfig();
  return useMutation({
    mutationFn: async ({
      serverName,
      enabled,
    }: {
      serverName: string;
      enabled: boolean;
    }) => {
      if (!config) {
        throw new Error("MCP config not found");
      }
      if (!config.mcp_servers[serverName]) {
        throw new Error(`MCP server ${serverName} not found`);
      }
      await updateMCPConfig({
        mcp_servers: {
          ...config.mcp_servers,
          [serverName]: {
            ...config.mcp_servers[serverName],
            enabled,
          },
        },
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["mcpConfig"] });
    },
  });
}

export function useSaveMCPConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (servers: Record<string, MCPServerConfig>) => {
      await updateMCPConfig({ mcp_servers: servers });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["mcpConfig"] });
    },
  });
}

export function useTestMCPServer() {
  return useMutation({
    mutationFn: (request: MCPTestRequest) => testMCPServer(request),
  });
}
