import type { Message } from "@langchain/langgraph-sdk";

import type { AgentThread, AgentThreadState } from "./types";

const THINK_BLOCK_RE = /<think\b[^>]*>[\s\S]*?<\/think>/gi;
const THINK_OPEN_RE = /<think\b[^>]*>/i;
const TITLE_LABEL_RE = /^(?:title|标题)\s*[:：-]\s*/i;
const TITLE_INTRO_RE =
  /^(?:here(?:'s| is)\s+(?:the\s+)?title|the\s+title\s+is)\s*[:：-]\s*/i;
const TITLE_PROMPT_ECHO_RE =
  /generate a concise title|return only the title|user message:|assistant summary:|^the user\b|^the assistant\b/i;
const TITLE_MAX_CHARS = 60;

export function pathOfThread(threadId: string) {
  return `/workspace/chats/${threadId}`;
}

export function textOfMessage(message: Message) {
  if (typeof message.content === "string") {
    return message.content;
  } else if (Array.isArray(message.content)) {
    for (const part of message.content) {
      if (part.type === "text") {
        return part.text;
      }
    }
  }
  return null;
}

function normalizeInlineText(text: string) {
  return text
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^[`"'“”‘’]+|[`"'“”‘’]+$/g, "")
    .trim();
}

function truncateTitle(title: string) {
  const clean = normalizeInlineText(title);
  if (clean.length <= TITLE_MAX_CHARS) return clean;
  return `${clean.slice(0, TITLE_MAX_CHARS).trimEnd()}...`;
}

export function cleanThreadTitle(title: string | null | undefined) {
  if (!title) return "";

  const withoutClosedThinking = title.replace(THINK_BLOCK_RE, "\n");
  if (THINK_OPEN_RE.test(withoutClosedThinking)) {
    return "";
  }

  const lines = withoutClosedThinking
    .split(/\r?\n/)
    .map((line) =>
      normalizeInlineText(
        line
          .replace(TITLE_INTRO_RE, "")
          .replace(TITLE_LABEL_RE, "")
          .replace(/^[*#>\-\s]+/, ""),
      ),
    )
    .filter(Boolean);

  for (const line of lines) {
    if (TITLE_PROMPT_ECHO_RE.test(line) || THINK_OPEN_RE.test(line)) {
      continue;
    }
    return truncateTitle(line);
  }

  return "";
}

function fallbackTitleFromMessages(messages: Message[] | undefined) {
  if (!messages) return "Untitled";
  for (const message of messages) {
    if (message.type !== "human") continue;
    const text = textOfMessage(message);
    if (!text) continue;
    const firstLine = text.split(/\r?\n/).find((line) => line.trim());
    if (firstLine) {
      return truncateTitle(firstLine);
    }
  }
  return "Untitled";
}

export function titleOfThreadState(
  state: Pick<AgentThreadState, "title" | "messages"> | null | undefined,
) {
  if (!state) return "Untitled";
  return cleanThreadTitle(state.title) || fallbackTitleFromMessages(state.messages);
}

export function titleOfThread(thread: AgentThread) {
  if (!thread.values) return "Untitled";
  return titleOfThreadState(thread.values);
}
