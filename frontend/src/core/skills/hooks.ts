import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { enableSkill } from "./api";

import { loadSkills } from ".";

export const skillsQueryOptions = {
  queryKey: ["skills"],
  queryFn: () => loadSkills(),
  staleTime: 30_000,
  retry: 2,
  retryDelay: 1_000,
} as const;

export function useSkills() {
  const { data, isLoading, error, refetch } = useQuery(skillsQueryOptions);
  return { skills: data ?? [], isLoading, error, refetch };
}

export function useEnableSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      skillName,
      enabled,
    }: {
      skillName: string;
      enabled: boolean;
    }) => {
      await enableSkill(skillName, enabled);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["skills"] });
    },
  });
}
