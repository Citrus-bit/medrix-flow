import type { Message } from "@langchain/langgraph-sdk";
import type { BaseStream } from "@langchain/langgraph-sdk/react";
import { render, screen, waitFor } from "@testing-library/react";
import type { PropsWithChildren, ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

import { I18nProvider } from "@/core/i18n/context";
import { SubtasksProvider } from "@/core/tasks/context";
import type { AgentThreadState } from "@/core/threads";

import { ThreadContext } from "./context";
import { MessageList } from "./message-list";

vi.mock("@/components/ai-elements/conversation", () => ({
  Conversation: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  ConversationContent: ({ children }: { children: ReactNode }) => (
    <div>{children}</div>
  ),
}));

vi.mock("streamdown", () => ({
  Streamdown: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/core/streamdown", () => ({
  streamdownPluginsWithWordAnimation: {},
  streamdownPlugins: { remarkPlugins: [], rehypePlugins: [] },
  humanMessagePlugins: {},
}));

vi.mock("./markdown-content", () => ({
  MarkdownContent: ({ content }: { content: string }) => <div>{content}</div>,
}));

vi.mock("../run-status-indicator", () => ({
  RunStatusIndicator: () => null,
}));

function makeThread(messages: Message[]): BaseStream<AgentThreadState> {
  return {
    messages,
    isLoading: false,
    isThreadLoading: false,
    values: {},
  } as BaseStream<AgentThreadState>;
}

function wrapper({ children }: PropsWithChildren) {
  return (
    <I18nProvider initialLocale="en-US">
      <SubtasksProvider>
        <ThreadContext.Provider
          value={{ thread: makeThread([]), sendMessage: vi.fn() }}
        >
          {children}
        </ThreadContext.Provider>
      </SubtasksProvider>
    </I18nProvider>
  );
}

describe("MessageList subtask rendering", () => {
  it("renders a historical task tool call before task context initialization", () => {
    const messages = [
      {
        id: "ai-1",
        type: "ai",
        content: "",
        tool_calls: [
          {
            id: "task-1",
            name: "task",
            args: {
              subagent_type: "academic-researcher",
              description: "Review related work",
              prompt: "Collect papers",
            },
          },
        ],
      },
    ] as Message[];

    render(
      <MessageList
        threadId="thread-1"
        thread={makeThread(messages)}
        paddingBottom={0}
      />,
      { wrapper },
    );

    expect(screen.getByText("Review related work")).toBeInTheDocument();
    expect(screen.getByText("Running subtask")).toBeInTheDocument();
  });

  it("updates task status from the tool result", async () => {
    const messages = [
      {
        id: "ai-1",
        type: "ai",
        content: "",
        tool_calls: [
          {
            id: "task-1",
            name: "task",
            args: {
              subagent_type: "general-purpose",
              description: "Summarize evidence",
              prompt: "Summarize",
            },
          },
        ],
      },
      {
        id: "tool-1",
        type: "tool",
        tool_call_id: "task-1",
        content: "Task Succeeded. Result: Evidence summary complete",
      },
    ] as Message[];

    render(
      <MessageList
        threadId="thread-1"
        thread={makeThread(messages)}
        paddingBottom={0}
      />,
      { wrapper },
    );

    await waitFor(() => {
      expect(screen.getByText("Subtask completed")).toBeInTheDocument();
    });
  });
});
