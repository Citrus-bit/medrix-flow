import assert from "node:assert/strict";
import { test } from "node:test";

import { parseTaskToolResult } from "./result-parser";

void test("parseTaskToolResult parses completed result", () => {
  const parsed = parseTaskToolResult("Task Succeeded. Result: done");
  assert.deepEqual(parsed, { status: "completed", result: "done" });
});

void test("parseTaskToolResult parses failed result", () => {
  const parsed = parseTaskToolResult("Task failed. invalid input");
  assert.deepEqual(parsed, { status: "failed", error: "invalid input" });
});

void test("parseTaskToolResult parses timeout as failed", () => {
  const parsed = parseTaskToolResult("Task timed out after 120s");
  assert.deepEqual(parsed, {
    status: "failed",
    error: "Task timed out after 120s",
  });
});

void test("parseTaskToolResult falls back to in_progress", () => {
  assert.deepEqual(parseTaskToolResult(""), { status: "in_progress" });
  assert.deepEqual(parseTaskToolResult("working..."), {
    status: "in_progress",
  });
});

