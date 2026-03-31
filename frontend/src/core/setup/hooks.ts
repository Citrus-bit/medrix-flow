import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  loadSetupConfig,
  saveSetupModels,
  testModel,
  testToolKey,
} from "./api";
import type {
  SaveModelsRequest,
  TestModelRequest,
  TestToolKeyRequest,
} from "./types";

const SETUP_QUERY_KEY = ["setupConfig"] as const;

export const setupQueryOptions = {
  queryKey: SETUP_QUERY_KEY,
  queryFn: loadSetupConfig,
  staleTime: 30_000,
  refetchOnWindowFocus: false,
  retry: 2,
  retryDelay: 1_000,
} as const;

export function useSetupConfig() {
  const { data, isLoading, error, refetch } = useQuery(setupQueryOptions);
  return { config: data, isLoading, error, refetch };
}

export function useSaveSetup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (req: SaveModelsRequest) => saveSetupModels(req),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: SETUP_QUERY_KEY });
      void queryClient.invalidateQueries({ queryKey: ["models"] });
    },
  });
}

export function useTestModel() {
  return useMutation({
    mutationFn: (req: TestModelRequest) => testModel(req),
  });
}

export function useTestToolKey() {
  return useMutation({
    mutationFn: (req: TestToolKeyRequest) => testToolKey(req),
  });
}
