from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage


def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        if content and all(isinstance(block, str) for block in content):
            return "\n".join(content)

        pieces: list[str] = []
        for block in content:
            if isinstance(block, str):
                pieces.append(block)
            elif isinstance(block, dict):
                text = block.get("text")
                if isinstance(text, str):
                    pieces.append(text)
        return "\n".join(piece for piece in pieces if piece)
    return str(content)


def serialize_message(message: Any) -> dict[str, Any]:
    if isinstance(message, AIMessage):
        payload: dict[str, Any] = {
            "type": "ai",
            "content": message.content,
            "id": getattr(message, "id", None),
        }
        if message.tool_calls:
            payload["tool_calls"] = [
                {
                    "name": tool_call["name"],
                    "args": tool_call["args"],
                    "id": tool_call.get("id"),
                }
                for tool_call in message.tool_calls
            ]
        if getattr(message, "usage_metadata", None):
            payload["usage_metadata"] = message.usage_metadata
        if getattr(message, "additional_kwargs", None):
            payload["additional_kwargs"] = message.additional_kwargs
        if getattr(message, "name", None):
            payload["name"] = message.name
        return payload
    if isinstance(message, ToolMessage):
        payload = {
            "type": "tool",
            "content": extract_text(message.content),
            "name": getattr(message, "name", None),
            "tool_call_id": getattr(message, "tool_call_id", None),
            "id": getattr(message, "id", None),
        }
        if getattr(message, "additional_kwargs", None):
            payload["additional_kwargs"] = message.additional_kwargs
        return payload
    if isinstance(message, HumanMessage):
        payload = {"type": "human", "content": message.content, "id": getattr(message, "id", None)}
        if getattr(message, "additional_kwargs", None):
            payload["additional_kwargs"] = message.additional_kwargs
        if getattr(message, "name", None):
            payload["name"] = message.name
        return payload
    if isinstance(message, SystemMessage):
        return {
            "type": "system",
            "content": message.content,
            "id": getattr(message, "id", None),
            "name": getattr(message, "name", None),
        }
    if isinstance(message, dict):
        return dict(message)
    return {"type": "unknown", "content": str(message), "id": getattr(message, "id", None)}


def message_event_type(message: Any) -> str:
    if isinstance(message, HumanMessage):
        return "human_message"
    if isinstance(message, ToolMessage):
        return "tool_message"
    if isinstance(message, SystemMessage):
        return "system_message"
    return "ai_message"


def message_caller(message: Any) -> str:
    if isinstance(message, HumanMessage):
        return "user"
    if isinstance(message, ToolMessage):
        return getattr(message, "name", None) or "tool"

    name = getattr(message, "name", None)
    if isinstance(name, str) and name.strip():
        return name

    additional_kwargs = getattr(message, "additional_kwargs", None)
    if isinstance(additional_kwargs, dict):
        for key in ("caller", "agent_name", "name"):
            value = additional_kwargs.get(key)
            if isinstance(value, str) and value.strip():
                return value

    msg_type = getattr(message, "type", None)
    if isinstance(msg_type, str) and msg_type.strip():
        return msg_type
    return "assistant"
