import type { BaseStream } from "@langchain/langgraph-sdk";
import { useEffect } from "react";

import { useI18n } from "@/core/i18n/hooks";
import type { AgentThreadState } from "@/core/threads";
import { titleOfThreadState } from "@/core/threads/utils";

import { useThreadChat } from "./chats";
import { FlipDisplay } from "./flip-display";

export function ThreadTitle({
  threadId,
  thread,
}: {
  className?: string;
  threadId: string;
  thread: BaseStream<AgentThreadState>;
}) {
  const { t } = useI18n();
  const { isNewThread } = useThreadChat();
  const displayTitle = titleOfThreadState(thread.values);
  useEffect(() => {
    let _title = t.pages.untitled;

    if (displayTitle !== "Untitled") {
      _title = displayTitle;
    } else if (isNewThread) {
      _title = t.pages.newChat;
    }
    if (thread.isThreadLoading) {
      document.title = `Loading... - ${t.pages.appName}`;
    } else {
      document.title = `${_title} - ${t.pages.appName}`;
    }
  }, [
    isNewThread,
    t.pages.newChat,
    t.pages.untitled,
    t.pages.appName,
    thread.isThreadLoading,
    displayTitle,
  ]);

  if (displayTitle === "Untitled") {
    return null;
  }
  return (
    <FlipDisplay uniqueKey={threadId}>
      {displayTitle}
    </FlipDisplay>
  );
}
