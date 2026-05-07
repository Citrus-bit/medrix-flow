import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from "react";

import { useSidebar } from "@/components/ui/sidebar";
import type { ArtifactInventoryEntry } from "@/core/artifacts/utils";
import { env } from "@/env";

function haveSameArtifactPaths(left: string[], right: string[]) {
  if (left.length !== right.length) {
    return false;
  }
  return left.every((filepath, index) => filepath === right[index]);
}

function haveSameArtifactEntries(
  left: Record<string, ArtifactInventoryEntry>,
  right: Record<string, ArtifactInventoryEntry>,
) {
  const leftKeys = Object.keys(left);
  const rightKeys = Object.keys(right);
  if (leftKeys.length !== rightKeys.length) {
    return false;
  }

  return leftKeys.every((key) => {
    const leftEntry = left[key];
    const rightEntry = right[key];
    return (
      rightEntry !== undefined &&
      leftEntry?.filepath === rightEntry.filepath &&
      leftEntry?.size === rightEntry.size &&
      leftEntry?.modifiedAt === rightEntry.modifiedAt &&
      leftEntry?.source === rightEntry.source
    );
  });
}

export interface ArtifactsContextType {
  artifacts: string[];
  setArtifacts: (artifacts: string[]) => void;
  artifactEntries: Record<string, ArtifactInventoryEntry>;
  setArtifactInventory: (entries: ArtifactInventoryEntry[]) => void;
  latestArtifact: string | null;

  selectedArtifact: string | null;
  autoSelect: boolean;
  select: (artifact: string, autoSelect?: boolean) => void;
  deselect: () => void;

  open: boolean;
  autoOpen: boolean;
  setOpen: (open: boolean) => void;
}

const ArtifactsContext = createContext<ArtifactsContextType | undefined>(
  undefined,
);

interface ArtifactsProviderProps {
  children: ReactNode;
}

export function ArtifactsProvider({ children }: ArtifactsProviderProps) {
  const [artifacts, setArtifacts] = useState<string[]>([]);
  const [artifactEntries, setArtifactEntries] = useState<
    Record<string, ArtifactInventoryEntry>
  >({});
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null);
  const [autoSelect, setAutoSelect] = useState(true);
  const [open, setOpen] = useState(
    env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY === "true",
  );
  const [autoOpen, setAutoOpen] = useState(true);
  const { setOpen: setSidebarOpen } = useSidebar();

  const select = useCallback(
    (artifact: string, autoSelect = false) => {
      setSelectedArtifact(artifact);
      if (env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY !== "true") {
        setSidebarOpen(false);
      }
      if (!autoSelect) {
        setAutoSelect(false);
      }
    },
    [setSidebarOpen, setSelectedArtifact, setAutoSelect],
  );

  const deselect = useCallback(() => {
    setSelectedArtifact(null);
    setAutoSelect(true);
    setOpen(false);
  }, []);

  const setArtifactInventory = useCallback((entries: ArtifactInventoryEntry[]) => {
    const nextArtifacts = entries.map((entry) => entry.filepath);
    const nextArtifactEntries = Object.fromEntries(
      entries.map((entry) => [entry.filepath, entry]),
    );

    setArtifacts((currentArtifacts) =>
      haveSameArtifactPaths(currentArtifacts, nextArtifacts)
        ? currentArtifacts
        : nextArtifacts,
    );
    setArtifactEntries((currentEntries) =>
      haveSameArtifactEntries(currentEntries, nextArtifactEntries)
        ? currentEntries
        : nextArtifactEntries,
    );
  }, []);

  const value: ArtifactsContextType = {
    artifacts,
    setArtifacts: (nextArtifacts) => {
      setArtifactInventory(
        nextArtifacts.map((filepath) => ({
          filepath,
          source: "thread",
        })),
      );
    },
    artifactEntries,
    setArtifactInventory,
    latestArtifact: artifacts[0] ?? null,

    open,
    autoOpen,
    autoSelect,
    setOpen: (isOpen: boolean) => {
      if (!isOpen && autoOpen) {
        setAutoOpen(false);
        setAutoSelect(false);
      }
      setOpen(isOpen);
    },

    selectedArtifact,
    select,
    deselect,
  };

  return (
    <ArtifactsContext.Provider value={value}>
      {children}
    </ArtifactsContext.Provider>
  );
}

export function useArtifacts() {
  const context = useContext(ArtifactsContext);
  if (context === undefined) {
    throw new Error("useArtifacts must be used within an ArtifactsProvider");
  }
  return context;
}
