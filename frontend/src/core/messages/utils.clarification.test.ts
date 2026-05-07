import { describe, expect, it } from "vitest";

import { findClarificationResponse } from "./utils";

describe("findClarificationResponse", () => {
  it("returns the first human response after a clarification message", () => {
    const clarificationMessage = {
      id: "tool-1",
      type: "tool",
      name: "ask_clarification",
      tool_call_id: "tool-1",
      content: "Which template?",
      additional_kwargs: {
        clarification: {
          question: "Which template?",
          options: ["Option A", "Option B"],
        },
      },
    } as const;

    const response = findClarificationResponse(
      [
        { id: "ai-1", type: "ai", content: "Need clarification." },
        clarificationMessage,
        { id: "human-1", type: "human", content: "Option A" },
        { id: "ai-2", type: "ai", content: "Continuing..." },
      ],
      clarificationMessage,
    );

    expect(response).toBe("Option A");
  });

  it("stops scanning at the next clarification message", () => {
    const firstClarification = {
      id: "tool-1",
      type: "tool",
      name: "ask_clarification",
      tool_call_id: "tool-1",
      content: "First question",
    } as const;
    const secondClarification = {
      id: "tool-2",
      type: "tool",
      name: "ask_clarification",
      tool_call_id: "tool-2",
      content: "Second question",
    } as const;

    const response = findClarificationResponse(
      [
        firstClarification,
        { id: "ai-1", type: "ai", content: "Still pending" },
        secondClarification,
        { id: "human-1", type: "human", content: "Reply to second" },
      ],
      firstClarification,
    );

    expect(response).toBeNull();
  });
});
