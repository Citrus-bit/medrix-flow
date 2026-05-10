import { useQuery } from "@tanstack/react-query";

import { loadFeatures } from "./api";

export const featuresQueryOptions = {
  queryKey: ["features"],
  queryFn: () => loadFeatures(),
  staleTime: 30_000,
  retry: 2,
  retryDelay: 1_000,
} as const;

export function useFeatures() {
  const { data, isLoading, error, refetch } = useQuery(featuresQueryOptions);
  return {
    features: data ?? { agents: [], tools: [], skills: [] },
    isLoading,
    error,
    refetch,
  };
}
