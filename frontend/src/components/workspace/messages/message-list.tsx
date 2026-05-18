import type { BaseStream } from "@langchain/langgraph-sdk/react";
import { useEffect } from "react";

import {
  Conversation,
  ConversationContent,
} from "@/components/ai-elements/conversation";
import { useI18n } from "@/core/i18n/hooks";
import {
  extractContentFromMessage,
  extractClarificationPayload,
  extractPresentFilesFromMessage,
  extractTextFromMessage,
  findClarificationResponse,
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
import type { ModelRetryStatus } from "@/core/threads/hooks";
import { cn } from "@/lib/utils";

import { ArtifactFileList } from "../artifacts/artifact-file-list";
import { RunStatusIndicator } from "../run-status-indicator";

import { ClarificationCard } from "./clarification-card";
import { useThread } from "./context";
import { MarkdownContent } from "./markdown-content";
import { MessageGroup } from "./message-group";
import { MessageListItem } from "./message-list-item";
import { MessageListSkeleton } from "./skeleton";
import { SubtaskCard } from "./subtask-card";

type TaskToolCall = {
  id?: string;
  name?: string;
  args?: Record<string, unknown>;
};

function subtaskFromToolCall(
  toolCall: TaskToolCall,
  fallbackDescription: string,
): Subtask | null {
  if (toolCall.name !== "task" || !toolCall.id) {
    return null;
  }

  const args = toolCall.args ?? {};
  const description =
    typeof args.description === "string" && args.description.trim()
      ? args.description
      : fallbackDescription;
  const prompt = typeof args.prompt === "string" ? args.prompt : "";
  const subagentType =
    typeof args.subagent_type === "string" && args.subagent_type.trim()
      ? args.subagent_type
      : "general-purpose";

  return {
    id: toolCall.id,
    subagent_type: subagentType,
    description,
    prompt,
    status: "in_progress",
  };
}

export function MessageList({
  className,
  threadId,
  thread,
  runId,
  modelRetryStatus,
  paddingBottom = 160,
}: {
  className?: string;
  threadId: string;
  thread: BaseStream<AgentThreadState>;
  runId?: string | null;
  modelRetryStatus?: ModelRetryStatus | null;
  paddingBottom?: number;
}) {
  const { t } = useI18n();
  const rehypePlugins = useRehypeSplitWordsIntoSpans(thread.isLoading);
  const updateSubtask = useUpdateSubtask();
  const { sendMessage } = useThread();
  const messages = thread.messages;
  const lastAssistantMessageId = [...messages]
    .reverse()
    .find((message) => message.type === "ai")?.id;

  useEffect(() => {
    for (const message of messages) {
      if (message.type === "ai") {
        for (const toolCall of message.tool_calls ?? []) {
          const subtask = subtaskFromToolCall(toolCall, t.subtasks.subtask);
          if (subtask) {
            updateSubtask(subtask);
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
  }, [messages, t.subtasks.subtask, updateSubtask]);

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
                  runId={
                    msg.type === "ai" && msg.id === lastAssistantMessageId
                      ? runId
                      : null
                  }
                  threadId={threadId}
                />
              );
            });
          } else if (group.type === "assistant:clarification") {
            const message = group.messages[0];
            if (message) {
              const payload = extractClarificationPayload(message);
              const resolvedAnswer = findClarificationResponse(messages, message);
              return (
                <ClarificationCard
                  key={group.id}
                  payload={payload}
                  fallbackContent={extractContentFromMessage(message)}
                  onSubmit={sendMessage}
                  resolvedAnswer={resolvedAnswer}
                  isLoading={thread.isLoading}
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
            const tasksById = new Map<string, Subtask>();
            for (const message of group.messages) {
              if (message.type === "ai") {
                for (const toolCall of message.tool_calls ?? []) {
                  const subtask = subtaskFromToolCall(
                    toolCall,
                    t.subtasks.subtask,
                  );
                  if (subtask) {
                    tasksById.set(subtask.id, subtask);
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
                  {t.subtasks.executing(tasksById.size)}
                </div>,
              );
              const subtasks =
                message.tool_calls
                  ?.map((toolCall) =>
                    subtaskFromToolCall(toolCall, t.subtasks.subtask),
                  )
                  .filter((subtask): subtask is Subtask => Boolean(subtask)) ??
                [];
              for (const subtask of subtasks) {
                results.push(
                  <SubtaskCard
                    key={"task-group-" + subtask.id}
                    taskId={subtask.id}
                    initialTask={subtask}
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
        <RunStatusIndicator
          className="my-4"
          threadId={threadId}
          currentRunId={runId}
          streaming={thread.isLoading}
          modelRetryStatus={modelRetryStatus}
        />
        <div style={{ height: `${paddingBottom}px` }} />
      </ConversationContent>
    </Conversation>
  );
}
