import type { BaseStream } from "@langchain/langgraph-sdk/react";
import { useEffect } from "react";

import {
  Conversation,
  ConversationContent,
} from "@/components/ai-elements/conversation";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/core/i18n/hooks";
import {
  extractContentFromMessage,
  extractClarificationPayload,
  extractPresentFilesFromMessage,
  extractTextFromMessage,
  groupMessages,
  hasContent,
  hasPresentFiles,
  hasReasoning,
} from "@/core/messages/utils";
import { useRehypeSplitWordsIntoSpans } from "@/core/rehype";
import type { Subtask } from "@/core/tasks";
import { useUpdateSubtask } from "@/core/tasks/context";
import { parseTaskToolResult } from "@/core/tasks/result-parser";
import type { AgentThreadState } from "@/core/threads";
import { cn } from "@/lib/utils";

import { ArtifactFileList } from "../artifacts/artifact-file-list";
import { StreamingIndicator } from "../streaming-indicator";
import { usePromptInputController } from "@/components/ai-elements/prompt-input";
import { useThread } from "./context";

import { MarkdownContent } from "./markdown-content";
import { MessageGroup } from "./message-group";
import { MessageListItem } from "./message-list-item";
import { MessageListSkeleton } from "./skeleton";
import { SubtaskCard } from "./subtask-card";

export function MessageList({
  className,
  threadId,
  thread,
  paddingBottom = 160,
}: {
  className?: string;
  threadId: string;
  thread: BaseStream<AgentThreadState>;
  paddingBottom?: number;
}) {
  const { t } = useI18n();
  const rehypePlugins = useRehypeSplitWordsIntoSpans(thread.isLoading);
  const updateSubtask = useUpdateSubtask();
  const { sendMessage } = useThread();
  const messages = thread.messages;

  useEffect(() => {
    for (const message of messages) {
      if (message.type === "ai") {
        for (const toolCall of message.tool_calls ?? []) {
          if (toolCall.name === "task") {
            updateSubtask({
              id: toolCall.id!,
              subagent_type: toolCall.args.subagent_type,
              description: toolCall.args.description,
              prompt: toolCall.args.prompt,
              status: "in_progress",
            });
          }
        }
      }

      if (message.type !== "tool") {
        continue;
      }

      const taskId = message.tool_call_id;
      if (!taskId) {
        continue;
      }

      const result = extractTextFromMessage(message);
      const parsed = parseTaskToolResult(result);
      updateSubtask({
        id: taskId,
        ...parsed,
      });
    }
  }, [messages, updateSubtask]);

  if (thread.isThreadLoading && messages.length === 0) {
    return <MessageListSkeleton />;
  }
  return (
    <Conversation
      className={cn("flex size-full flex-col justify-center", className)}
    >
      <ConversationContent className="mx-auto w-full max-w-(--container-width-md) gap-8 pt-12">
        {groupMessages(messages, (group) => {
          if (group.type === "human" || group.type === "assistant") {
            return group.messages.map((msg) => {
              return (
                <MessageListItem
                  key={`${group.id}/${msg.id}`}
                  message={msg}
                  isLoading={thread.isLoading}
                />
              );
            });
          } else if (group.type === "assistant:clarification") {
            const message = group.messages[0];
            if (message) {
              const payload = extractClarificationPayload(message);
              return (
                <ClarificationCard
                  key={group.id}
                  payload={payload}
                  fallbackContent={extractContentFromMessage(message)}
                  onSubmit={sendMessage}
                />
              );
            }
            return null;
          } else if (group.type === "assistant:present-files") {
            const files: string[] = [];
            for (const message of group.messages) {
              if (hasPresentFiles(message)) {
                const presentFiles = extractPresentFilesFromMessage(message);
                files.push(...presentFiles);
              }
            }
            return (
              <div className="w-full" key={group.id}>
                {group.messages[0] && hasContent(group.messages[0]) && (
                  <MarkdownContent
                    content={extractContentFromMessage(group.messages[0])}
                    isLoading={thread.isLoading}
                    rehypePlugins={rehypePlugins}
                    className="mb-4"
                  />
                )}
                <ArtifactFileList files={files} threadId={threadId} />
              </div>
            );
          } else if (group.type === "assistant:subagent") {
            const tasks = new Set<Subtask>();
            for (const message of group.messages) {
              if (message.type === "ai") {
                for (const toolCall of message.tool_calls ?? []) {
                  if (toolCall.name === "task") {
                    tasks.add({
                      id: toolCall.id!,
                      subagent_type: toolCall.args.subagent_type,
                      description: toolCall.args.description,
                      prompt: toolCall.args.prompt,
                      status: "in_progress",
                    });
                  }
                }
              }
            }
            const results: React.ReactNode[] = [];
            for (const message of group.messages.filter(
              (message) => message.type === "ai",
            )) {
              if (hasReasoning(message)) {
                results.push(
                  <MessageGroup
                    key={"thinking-group-" + message.id}
                    messages={[message]}
                    isLoading={thread.isLoading}
                  />,
                );
              }
              results.push(
                <div
                  key="subtask-count"
                  className="text-muted-foreground font-norma pt-2 text-sm"
                >
                  {t.subtasks.executing(tasks.size)}
                </div>,
              );
              const taskIds = message.tool_calls
                ?.filter((toolCall) => toolCall.name === "task")
                .map((toolCall) => toolCall.id);
              for (const taskId of taskIds ?? []) {
                results.push(
                  <SubtaskCard
                    key={"task-group-" + taskId}
                    taskId={taskId!}
                    isLoading={thread.isLoading}
                  />,
                );
              }
            }
            return (
              <div
                key={"subtask-group-" + group.id}
                className="relative z-1 flex flex-col gap-2"
              >
                {results}
              </div>
            );
          }
          return (
            <MessageGroup
              key={"group-" + group.id}
              messages={group.messages}
              isLoading={thread.isLoading}
            />
          );
        })}
        {thread.isLoading && <StreamingIndicator className="my-4" />}
        <div style={{ height: `${paddingBottom}px` }} />
      </ConversationContent>
    </Conversation>
  );
}

function ClarificationCard({
  payload,
  fallbackContent,
  onSubmit,
}: {
  payload:
    | {
        question?: string;
        clarification_type?: string;
        context?: string;
        options?: string[];
        allow_custom_input?: boolean;
      }
    | null;
  fallbackContent: string;
  onSubmit?: (text: string) => Promise<void>;
}) {
  const { textInput } = usePromptInputController();
  const options = payload?.options ?? [];
  const question = payload?.question ?? fallbackContent;
  const context = payload?.context;

  const handlePick = async (choice: string) => {
    await onSubmit?.(choice);
  };

  const handleCustom = () => {
    textInput.setInput("");
    requestAnimationFrame(() => {
      document
        .querySelector<HTMLTextAreaElement>("textarea[name='message']")
        ?.focus();
    });
  };

  return (
    <div className="rounded-2xl border bg-background p-4">
      {context && <div className="text-muted-foreground mb-2 text-sm">{context}</div>}
      <div className="mb-3 text-sm font-medium">{question}</div>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <Button key={option} variant="secondary" onClick={() => void handlePick(option)}>
            {option}
          </Button>
        ))}
        <Button variant="outline" onClick={handleCustom}>
          type something
        </Button>
      </div>
    </div>
  );
}
