import { render, screen } from "@testing-library/react";
import type { PropsWithChildren, ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { I18nProvider } from "@/core/i18n/context";
import { SubtasksProvider } from "@/core/tasks/context";

import { SubtaskCard } from "./subtask-card";

vi.mock("streamdown", () => ({
  Streamdown: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/core/streamdown", () => ({
  streamdownPluginsWithWordAnimation: {},
  streamdownPlugins: { remarkPlugins: [], rehypePlugins: [] },
}));

vi.mock("./markdown-content", () => ({
  MarkdownContent: ({ content }: { content: string }) => <div>{content}</div>,
}));

function wrapper({ children }: PropsWithChildren) {
  return (
    <I18nProvider initialLocale="en-US">
      <SubtasksProvider>{children}</SubtasksProvider>
    </I18nProvider>
  );
}

describe("SubtaskCard", () => {
  it("renders initial task data before the task context catches up", () => {
    render(
      <SubtaskCard
        taskId="task-1"
        initialTask={{
          id: "task-1",
          status: "in_progress",
          subagent_type: "general-purpose",
          description: "Collect benchmark evidence",
          prompt: "Find benchmark papers",
        }}
        isLoading={false}
      />,
      { wrapper },
    );

    expect(screen.getByText("Collect benchmark evidence")).toBeInTheDocument();
    expect(screen.getByText("Running subtask")).toBeInTheDocument();
  });

  it("does not crash when task data is missing", () => {
    const { container } = render(
      <SubtaskCard taskId="missing-task" isLoading={false} />,
      { wrapper },
    );

    expect(container).toBeEmptyDOMElement();
  });
});
