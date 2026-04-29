export type ParsedTaskToolResult =
  | { status: "completed"; result?: string }
  | { status: "failed"; error?: string }
  | { status: "in_progress" };

export function parseTaskToolResult(text: string): ParsedTaskToolResult {
  const normalized = text.trim();

  if (!normalized) {
    return { status: "in_progress" };
  }

  if (normalized.startsWith("Task Succeeded. Result:")) {
    const result = normalized.split("Task Succeeded. Result:")[1]?.trim();
    return {
      status: "completed",
      ...(result ? { result } : {}),
    };
  }

  if (normalized.startsWith("Task failed.")) {
    const error = normalized.split("Task failed.")[1]?.trim();
    return {
      status: "failed",
      ...(error ? { error } : {}),
    };
  }

  if (normalized.startsWith("Task timed out")) {
    return {
      status: "failed",
      error: normalized,
    };
  }

  return { status: "in_progress" };
}
