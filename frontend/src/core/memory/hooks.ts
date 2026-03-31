import { useQuery } from "@tanstack/react-query";

import { loadMemory } from "./api";

export const memoryQueryOptions = {
  queryKey: ["memory"],
  queryFn: () => loadMemory(),
  staleTime: 30_000,
  retry: 2,
  retryDelay: 1_000,
} as const;

export function useMemory() {
  const { data, isLoading, error, refetch } = useQuery(memoryQueryOptions);
  return { memory: data ?? null, isLoading, error, refetch };
}
