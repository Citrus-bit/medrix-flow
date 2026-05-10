from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from hashlib import sha1
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from medrix_flow.config.paths import VIRTUAL_PATH_PREFIX, get_paths
from medrix_flow.runtime.runs import RunRecord
from medrix_flow.runtime.serialization import extract_text

MAX_SUMMARY_CHARS = 320
MAX_DETAIL_CHARS = 4000
SENSITIVE_KEY_RE = re.compile(
    r"(^token$|api[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token|secret|password|authorization|credential)",
    re.IGNORECASE,
)
HIDDEN_REASONING_KEY_RE = re.compile(
    r"(^reasoning_content$|^reasoning_details$|^thinking$|^thoughts?$|chain[_-]?of[_-]?thought)",
    re.IGNORECASE,
)
THINK_TAG_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)

NodeKind = Literal["user", "agent", "subagent", "tool", "artifact", "checkpoint", "final", "error", "event"]
NodeStatus = Literal["pending", "running", "success", "error", "interrupted"]


class WorkflowRun(BaseModel):
    run_id: str
    thread_id: str
    assistant_id: str | None = None
    status: str
    error: str | None = None
    created_at: str
    updated_at: str
    last_event_at: str | None = None


class WorkflowNode(BaseModel):
    id: str
    kind: NodeKind
    label: str
    status: NodeStatus = "success"
    summary: str = ""
    caller: str | None = None
    tool_name: str | None = None
    artifact_path: str | None = None
    seq: int | None = None
    created_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None


class WorkflowEvent(BaseModel):
    seq: int
    run_id: str
    thread_id: str
    event_type: str
    caller: str
    summary: str
    content: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class WorkflowArtifact(BaseModel):
    filepath: str
    filename: str
    size: int | None = None
    modified_at: str | None = None


class WorkflowUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class WorkflowSnapshot(BaseModel):
    run: WorkflowRun
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]
    events: list[WorkflowEvent]
    artifacts: list[WorkflowArtifact]
    usage: WorkflowUsage
    has_more: bool = False


def _truncate(value: str, limit: int = MAX_SUMMARY_CHARS) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _safe_json(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except TypeError:
        return str(value)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if HIDDEN_REASONING_KEY_RE.search(str(key)):
                redacted[str(key)] = "[hidden]"
            elif SENSITIVE_KEY_RE.search(str(key)):
                redacted[str(key)] = "[redacted]"
            else:
                redacted[str(key)] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value[:100]]
    if isinstance(value, str):
        value = THINK_TAG_RE.sub("[hidden]", value)
        return value if len(value) <= MAX_DETAIL_CHARS else value[:MAX_DETAIL_CHARS] + "..."
    return _safe_json(value)


def _artifact_node_id(path: str) -> str:
    digest = sha1(path.encode("utf-8")).hexdigest()[:12]
    return f"artifact-{digest}"


def normalize_stream_event(event_type: str, data: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Convert an in-flight stream chunk into a storable run event."""
    safe_data = _redact(data)
    message_type = safe_data.get("type") if isinstance(safe_data, dict) else None

    if event_type == "messages-tuple" and message_type == "tool":
        caller = str(safe_data.get("name") or "tool")
        return "tool_message", caller, safe_data

    if event_type == "messages-tuple" and message_type == "ai":
        tool_calls = safe_data.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            return "ai_tool_calls", "assistant", safe_data
        return "ai_message", "assistant", safe_data

    if event_type == "values":
        return "state_snapshot", "checkpoint", safe_data

    if event_type == "error":
        return "error", "gateway", safe_data

    if event_type == "end":
        return "run_end", "gateway", safe_data

    return event_type, "gateway", safe_data


def _content_summary(content: dict[str, Any]) -> str:
    if "summary" in content and isinstance(content["summary"], str):
        return _truncate(content["summary"])
    if "message" in content and isinstance(content["message"], str):
        return _truncate(content["message"])
    if "content" in content:
        return _truncate(extract_text(content["content"]))
    if "title" in content and content["title"]:
        return _truncate(str(content["title"]))
    if "usage" in content:
        return "Token usage updated."
    if "artifacts" in content and isinstance(content["artifacts"], list):
        return f"{len(content['artifacts'])} artifact(s) available."
    return _truncate(json.dumps(_redact(content), ensure_ascii=False, default=str))


def _node_kind(event_type: str, caller: str, content: dict[str, Any]) -> NodeKind:
    if event_type == "human_message" or content.get("type") == "human":
        return "user"
    if event_type in {"tool_message", "ai_tool_calls"} or content.get("type") == "tool":
        tool_name = str(content.get("name") or caller or "")
        if tool_name == "task" or tool_name.startswith("task"):
            return "subagent"
        return "tool"
    if event_type == "error":
        return "error"
    if event_type == "state_snapshot":
        return "checkpoint"
    if event_type == "run_end":
        return "final"
    if event_type == "ai_message" or content.get("type") == "ai":
        return "agent"
    return "event"


def _node_label(kind: NodeKind, event_type: str, caller: str, content: dict[str, Any]) -> str:
    if kind == "user":
        return "User request"
    if kind == "subagent":
        return str(content.get("name") or caller or "Sub-agent")
    if kind == "tool":
        tool_calls = content.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            names = [str(item.get("name")) for item in tool_calls if isinstance(item, dict) and item.get("name")]
            return ", ".join(names[:3]) if names else "Tool call"
        return str(content.get("name") or caller or "Tool")
    if kind == "checkpoint":
        return "State checkpoint"
    if kind == "final":
        return "Run finished"
    if kind == "error":
        return "Run error"
    if kind == "agent":
        return str(caller) if caller and caller != "assistant" else "Assistant"
    return event_type.replace("_", " ").title()


def _node_status(kind: NodeKind, run_status: str) -> NodeStatus:
    if kind == "error":
        return "error"
    if kind == "final":
        if run_status == "interrupted":
            return "interrupted"
        if run_status == "error":
            return "error"
    return "success"


def _extract_artifacts_from_event(content: dict[str, Any]) -> list[str]:
    found: list[str] = []
    artifacts = content.get("artifacts")
    if isinstance(artifacts, list):
        found.extend(str(item) for item in artifacts if isinstance(item, str))
    tool_calls = content.get("tool_calls")
    if isinstance(tool_calls, list):
        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            args = call.get("args")
            if not isinstance(args, dict):
                continue
            for key in ("paths", "filepaths", "artifacts"):
                value = args.get(key)
                if isinstance(value, list):
                    found.extend(str(item) for item in value if isinstance(item, str))
                elif isinstance(value, str):
                    found.append(value)
    return [path for path in found if path.startswith(VIRTUAL_PATH_PREFIX)]


def _usage_from_event(content: dict[str, Any]) -> WorkflowUsage:
    usage = content.get("usage_metadata") or content.get("usage") or {}
    if not isinstance(usage, dict):
        return WorkflowUsage()
    return WorkflowUsage(
        input_tokens=int(usage.get("input_tokens") or 0),
        output_tokens=int(usage.get("output_tokens") or 0),
        total_tokens=int(usage.get("total_tokens") or 0),
    )


def _list_artifacts(thread_id: str) -> list[WorkflowArtifact]:
    try:
        outputs_dir = get_paths().sandbox_outputs_dir(thread_id)
    except ValueError:
        return []
    if not outputs_dir.exists():
        return []

    items: list[WorkflowArtifact] = []
    for path in outputs_dir.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(outputs_dir)
        if any(part.startswith(".") for part in relative.parts):
            continue
        stat = path.stat()
        items.append(
            WorkflowArtifact(
                filepath=f"{VIRTUAL_PATH_PREFIX}/outputs/{relative.as_posix()}",
                filename=path.name,
                size=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
            )
        )
    return sorted(items, key=lambda item: item.modified_at or "", reverse=True)


def build_workflow_snapshot(
    *,
    record: RunRecord,
    event_rows: list[dict[str, Any]],
    has_more: bool,
) -> WorkflowSnapshot:
    events: list[WorkflowEvent] = []
    nodes: list[WorkflowNode] = []
    edges: list[WorkflowEdge] = []
    usage = WorkflowUsage()
    seen_artifact_nodes: set[str] = set()
    previous_node_id: str | None = None

    for row in event_rows:
        content = _redact(row.get("content") or {})
        summary = _content_summary(content)
        event = WorkflowEvent(
            seq=int(row["seq"]),
            run_id=row["run_id"],
            thread_id=row["thread_id"],
            event_type=row["event_type"],
            caller=row["caller"],
            summary=summary,
            content=content,
            created_at=row["created_at"],
        )
        events.append(event)

        event_usage = _usage_from_event(content)
        usage.input_tokens += event_usage.input_tokens
        usage.output_tokens += event_usage.output_tokens
        usage.total_tokens += event_usage.total_tokens

        kind = _node_kind(event.event_type, event.caller, content)
        node_id = f"event-{event.seq}"
        node = WorkflowNode(
            id=node_id,
            kind=kind,
            label=_node_label(kind, event.event_type, event.caller, content),
            status=_node_status(kind, record.status.value),
            summary=summary,
            caller=event.caller,
            tool_name=content.get("name") if isinstance(content.get("name"), str) else None,
            seq=event.seq,
            created_at=event.created_at,
            metadata={"event_type": event.event_type},
        )
        nodes.append(node)
        if previous_node_id is not None:
            edges.append(WorkflowEdge(id=f"edge-{previous_node_id}-{node_id}", source=previous_node_id, target=node_id))
        previous_node_id = node_id

        for artifact_path in _extract_artifacts_from_event(content):
            if artifact_path in seen_artifact_nodes:
                continue
            seen_artifact_nodes.add(artifact_path)
            artifact_id = _artifact_node_id(artifact_path)
            artifact_node = WorkflowNode(
                id=artifact_id,
                kind="artifact",
                label=Path(artifact_path).name,
                status="success",
                summary=artifact_path,
                artifact_path=artifact_path,
                seq=event.seq,
                created_at=event.created_at,
            )
            nodes.append(artifact_node)
            edges.append(WorkflowEdge(id=f"edge-{node_id}-{artifact_id}", source=node_id, target=artifact_id, label="created"))

    artifacts = _list_artifacts(record.thread_id)
    for artifact in artifacts:
        if artifact.filepath in seen_artifact_nodes:
            continue
        seen_artifact_nodes.add(artifact.filepath)
        node_id = _artifact_node_id(artifact.filepath)
        nodes.append(
            WorkflowNode(
                id=node_id,
                kind="artifact",
                label=artifact.filename,
                status="success",
                summary=artifact.filepath,
                artifact_path=artifact.filepath,
                created_at=artifact.modified_at,
            )
        )
        if previous_node_id is not None:
            edges.append(WorkflowEdge(id=f"edge-{previous_node_id}-{node_id}", source=previous_node_id, target=node_id, label="artifact"))

    if not nodes:
        status = "running" if record.status.value in {"pending", "running"} else record.status.value
        nodes.append(
            WorkflowNode(
                id="run",
                kind="agent",
                label=record.assistant_id or "Assistant",
                status=status if status in {"pending", "running", "success", "error", "interrupted"} else "success",
                summary="Run registered. Waiting for the first visible event.",
                created_at=record.created_at,
            )
        )

    last_event_at = events[-1].created_at if events else None
    return WorkflowSnapshot(
        run=WorkflowRun(
            run_id=record.run_id,
            thread_id=record.thread_id,
            assistant_id=record.assistant_id,
            status=record.status.value,
            error=record.error,
            created_at=record.created_at,
            updated_at=record.updated_at,
            last_event_at=last_event_at,
        ),
        nodes=nodes[-200:],
        edges=[edge for edge in edges if edge.source in {node.id for node in nodes[-200:]} and edge.target in {node.id for node in nodes[-200:]}],
        events=events[-200:],
        artifacts=artifacts,
        usage=usage,
        has_more=has_more,
    )
