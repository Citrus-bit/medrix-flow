import { createContext, useCallback, useContext, useState } from "react";

import type { Subtask } from "./types";

export interface SubtaskContextValue {
  tasks: Record<string, Subtask>;
  setTasks: (tasks: Record<string, Subtask>) => void;
}

export const SubtaskContext = createContext<SubtaskContextValue>({
  tasks: {},
  setTasks: () => {
    /* noop */
  },
});

export function SubtasksProvider({ children }: { children: React.ReactNode }) {
  const [tasks, setTasks] = useState<Record<string, Subtask>>({});
  return (
    <SubtaskContext.Provider value={{ tasks, setTasks }}>
      {children}
    </SubtaskContext.Provider>
  );
}

export function useSubtaskContext() {
  const context = useContext(SubtaskContext);
  if (context === undefined) {
    throw new Error(
      "useSubtaskContext must be used within a SubtaskContext.Provider",
    );
  }
  return context;
}

export function useSubtask(id: string) {
  const { tasks } = useSubtaskContext();
  return tasks[id];
}

export function hasTaskPatchChanges(
  previous: Subtask | undefined,
  patch: Partial<Subtask> & { id: string },
) {
  if (!previous) {
    return true;
  }
  for (const [key, value] of Object.entries(patch)) {
    if (!Object.is(previous[key as keyof Subtask], value)) {
      return true;
    }
  }
  return false;
}

export function useUpdateSubtask() {
  const { setTasks } = useSubtaskContext();
  const updateSubtask = useCallback(
    (task: Partial<Subtask> & { id: string }) => {
      setTasks((previousTasks) => {
        const previousTask = previousTasks[task.id];
        if (!hasTaskPatchChanges(previousTask, task)) {
          return previousTasks;
        }
        return {
          ...previousTasks,
          [task.id]: { ...previousTask, ...task } as Subtask,
        };
      });
    },
    [setTasks],
  );
  return updateSubtask;
}
