import assert from "node:assert/strict";
import test from "node:test";

const { hasTaskPatchChanges } = await import(
  new URL("./context.tsx", import.meta.url).href,
);

void test("returns true when there is no previous task", () => {
  assert.equal(
    hasTaskPatchChanges(undefined, {
      id: "task-1",
      status: "in_progress",
    }),
    true,
  );
});

void test("returns false when patch does not change any field", () => {
  const previous = {
    id: "task-1",
    status: "in_progress",
    subagent_type: "general-purpose",
    description: "desc",
    prompt: "prompt",
  };

  assert.equal(
    hasTaskPatchChanges(previous, {
      id: "task-1",
      status: "in_progress",
    }),
    false,
  );
});

void test("returns true when patch changes an existing field", () => {
  const previous = {
    id: "task-1",
    status: "in_progress",
    subagent_type: "general-purpose",
    description: "desc",
    prompt: "prompt",
  };

  assert.equal(
    hasTaskPatchChanges(previous, {
      id: "task-1",
      status: "completed",
      result: "done",
    }),
    true,
  );
});
