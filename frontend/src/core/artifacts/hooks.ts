import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";

import { useThread } from "@/components/workspace/messages/context";
import { getBackendBaseURL } from "@/core/config";

import { fetchWithTimeout } from "../api/fetch";

import { loadArtifactContent, loadArtifactContentFromToolCall } from "./loader";
import {
  mergeArtifactEntries,
  type ArtifactInventoryEntry,
  type ThreadArtifactRecord,
} from "./utils";

async function listThreadArtifacts(threadId: string) {
  const response = await fetchWithTimeout(
    `${getBackendBaseURL()}/api/threads/${encodeURIComponent(threadId)}/artifacts`,
  );

  if (!response.ok) {
    return [] as ThreadArtifactRecord[];
  }

  const payload = (await response.json()) as {
    files?: ThreadArtifactRecord[];
  };
  return payload.files ?? [];
}

export function useThreadArtifactInventory({
  threadId,
  seededArtifacts,
  enabled = true,
  refetchInterval = 5000,
}: {
  threadId: string;
  seededArtifacts: string[];
  enabled?: boolean;
  refetchInterval?: number | false;
}) {
  const query = useQuery({
    queryKey: ["thread-artifacts", threadId],
    queryFn: () => listThreadArtifacts(threadId),
    enabled: enabled && Boolean(threadId),
    refetchInterval,
    refetchOnWindowFocus: true,
    staleTime: 0,
    retry: 1,
  });

  const artifacts = useMemo<ArtifactInventoryEntry[]>(
    () => mergeArtifactEntries(seededArtifacts, query.data ?? []),
    [seededArtifacts, query.data],
  );

  return {
    artifacts,
    refetch: query.refetch,
    isFetching: query.isFetching,
  };
}

export function useArtifactContent({
  filepath,
  threadId,
  enabled,
  versionKey,
}: {
  filepath: string;
  threadId: string;
  enabled?: boolean;
  versionKey?: string;
}) {
  const isWriteFile = useMemo(() => {
    return filepath.startsWith("write-file:");
  }, [filepath]);
  const { thread, isMock } = useThread();
  const content = useMemo(() => {
    if (isWriteFile) {
      return loadArtifactContentFromToolCall({ url: filepath, thread });
    }
    return null;
  }, [filepath, isWriteFile, thread]);

  const { data, isLoading, error } = useQuery({
    queryKey: ["artifact", filepath, threadId, isMock, versionKey],
    queryFn: () => {
      return loadArtifactContent({ filepath, threadId, isMock, versionKey });
    },
    enabled,
    // Cache artifact content for 5 minutes to avoid repeated fetches (especially for .skill ZIP extraction)
    staleTime: 5 * 60 * 1000,
  });
  return { content: isWriteFile ? content : data, isLoading, error };
}
