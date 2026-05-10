import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.gateway.routers import runs
from app.gateway.services import GatewayRunService
from medrix_flow.runtime import MemoryStreamBridge, SQLiteFeedbackRepo, SQLiteRunEventStore, SQLiteRunStore
from medrix_flow.runtime.db import SQLiteRuntimeDB
from medrix_flow.runtime.runs import RunManager, RunStatus
from medrix_flow.runtime.runs.manager import ConflictError


class FakeCheckpointer:
    def __init__(self, messages=None):
        self.messages = list(messages or [])

    async def aget_tuple(self, config):
        return SimpleNamespace(
            checkpoint={"channel_values": {"messages": list(self.messages)}}
        )


async def _make_runtime_service(messages=None) -> tuple[GatewayRunService, SQLiteRuntimeDB]:
    db = SQLiteRuntimeDB(":memory:")
    await db.connect()

    run_store = SQLiteRunStore(db)
    event_store = SQLiteRunEventStore(db)
    feedback_repo = SQLiteFeedbackRepo(db)
    await run_store.setup()
    await event_store.setup()
    await feedback_repo.setup()

    service = GatewayRunService(
        checkpointer=FakeCheckpointer(messages=messages),
        stream_bridge=MemoryStreamBridge(),
        run_manager=RunManager(store=run_store),
        run_store=run_store,
        event_store=event_store,
        feedback_repo=feedback_repo,
    )
    return service, db


def test_run_manager_rejects_interrupts_and_rolls_back():
    async def scenario():
        db = SQLiteRuntimeDB(":memory:")
        await db.connect()
        store = SQLiteRunStore(db)
        await store.setup()
        manager = RunManager(store=store)

        first = await manager.create_or_reject("thread-1")
        try:
            await manager.create_or_reject("thread-1")
            raise AssertionError("Expected ConflictError")
        except ConflictError:
            pass

        second = await manager.create_or_reject(
            "thread-1",
            multitask_strategy="interrupt",
        )
        assert first.status is RunStatus.interrupted
        assert first.abort_action == "interrupt"
        assert second.run_id != first.run_id

        third = await manager.create_or_reject(
            "thread-1",
            multitask_strategy="rollback",
        )
        assert second.status is RunStatus.interrupted
        assert second.abort_action == "rollback"
        assert third.run_id != second.run_id

        await db.close()

    asyncio.run(scenario())


def test_sqlite_repositories_persist_and_paginate():
    async def scenario():
        db = SQLiteRuntimeDB(":memory:")
        await db.connect()
        run_store = SQLiteRunStore(db)
        event_store = SQLiteRunEventStore(db)
        feedback_repo = SQLiteFeedbackRepo(db)
        await run_store.setup()
        await event_store.setup()
        await feedback_repo.setup()

        await run_store.put(
            "run-1",
            thread_id="thread-1",
            assistant_id="lead_agent",
            status="pending",
            multitask_strategy="reject",
            source="external",
            metadata={"source": "test"},
            kwargs={"input": {"messages": []}},
            pre_message_count=1,
        )
        await run_store.update_status("run-1", "success")
        await run_store.update_materialization(
            "run-1",
            persisted_message_count=2,
            messages_complete=True,
        )

        stored = await run_store.get("run-1")
        assert stored is not None
        assert stored["status"] == "success"
        assert stored["persisted_message_count"] == 2
        assert stored["messages_complete"] is True

        await event_store.put_batch(
            [
                {
                    "thread_id": "thread-1",
                    "run_id": "run-1",
                    "event_type": "ai_message",
                    "caller": "assistant",
                    "content": {"type": "ai", "content": "hello"},
                },
                {
                    "thread_id": "thread-1",
                    "run_id": "run-1",
                    "event_type": "tool_message",
                    "caller": "search",
                    "content": {"type": "tool", "content": "world"},
                },
            ]
        )

        page = await event_store.list_messages_by_run("thread-1", "run-1", limit=1)
        assert len(page) == 1
        assert page[0]["event_type"] == "ai_message"

        feedback = await feedback_repo.upsert(thread_id="thread-1", run_id="run-1", rating=1)
        assert feedback["rating"] == 1
        assert await feedback_repo.get_by_run(thread_id="thread-1", run_id="run-1") is not None
        assert await feedback_repo.delete_by_run(thread_id="thread-1", run_id="run-1") is True

        await db.close()

    asyncio.run(scenario())


def test_checkpoint_diff_materialization_persists_only_new_messages():
    async def scenario():
        service, db = await _make_runtime_service(messages=[HumanMessage(content="before")])

        await service.start_run(
            "thread-1",
            runs.RunCreateRequest(run_id="run-1", assistant_id="lead_agent"),
        )

        service._checkpointer.messages = [
            HumanMessage(content="before"),
            HumanMessage(content="new question"),
            AIMessage(content="new answer"),
            ToolMessage(content="tool result", tool_call_id="tool-1", name="search"),
        ]

        await service.complete_run("thread-1", "run-1", status=RunStatus.success)
        page = await service.list_run_messages("thread-1", "run-1", limit=10)

        assert [row["event_type"] for row in page["data"]] == [
            "human_message",
            "ai_message",
            "tool_message",
        ]

        stored = await service.require_run("thread-1", "run-1")
        assert stored.messages_complete is True
        assert stored.persisted_message_count == 3
        assert stored.status is RunStatus.success

        await db.close()

    asyncio.run(scenario())


def test_workflow_endpoint_normalizes_run_events():
    async def scenario():
        service, db = await _make_runtime_service(messages=[HumanMessage(content="before")])

        await service.start_run(
            "thread-1",
            runs.RunCreateRequest(run_id="run-workflow-1", assistant_id="lead_agent"),
        )
        await service.record_external_event(
            "thread-1",
            "run-workflow-1",
            event_type="human_message",
            caller="user",
            content={"type": "human", "content": "Write a paper"},
        )
        await service.record_external_event(
            "thread-1",
            "run-workflow-1",
            event_type="ai_tool_calls",
            caller="assistant",
            content={
                "type": "ai",
                "tool_calls": [
                    {
                        "name": "manuscript_export",
                        "args": {"tex_content": "secret-free", "api_key": "should-not-leak"},
                        "id": "call-1",
                    }
                ],
            },
        )
        await service.record_external_event(
            "thread-1",
            "run-workflow-1",
            event_type="tool_message",
            caller="manuscript_export",
            content={
                "type": "tool",
                "name": "manuscript_export",
                "content": "PASS",
                "artifacts": ["/mnt/user-data/outputs/manuscript.pdf"],
            },
        )
        await service.complete_run("thread-1", "run-workflow-1", status=RunStatus.success)

        workflow = await service.build_workflow("thread-1", "run-workflow-1", limit=20)
        kinds = [node["kind"] for node in workflow["nodes"]]
        assert "user" in kinds
        assert "tool" in kinds
        assert "artifact" in kinds
        assert workflow["events"][1]["content"]["tool_calls"][0]["args"]["api_key"] == "[redacted]"
        assert workflow["run"]["status"] == "success"

        delta = await service.build_workflow("thread-1", "run-workflow-1", limit=20, after_seq=2)
        assert [event["seq"] for event in delta["events"]] == [3]

        await db.close()

    asyncio.run(scenario())


def test_external_sideband_events_do_not_advance_checkpoint_materialization():
    async def scenario():
        service, db = await _make_runtime_service(messages=[HumanMessage(content="before")])

        await service.start_run(
            "thread-1",
            runs.RunCreateRequest(run_id="run-sideband-1", assistant_id="lead_agent"),
        )
        await service.record_external_event(
            "thread-1",
            "run-sideband-1",
            event_type="human_message",
            caller="user",
            content={"type": "human", "content": "Visible request"},
        )

        record = await service.require_run("thread-1", "run-sideband-1")
        assert record.persisted_message_count == 0
        assert record.messages_complete is False

        service._checkpointer.messages = [
            HumanMessage(content="before"),
            AIMessage(content="checkpoint answer"),
        ]
        await service.complete_run("thread-1", "run-sideband-1", status=RunStatus.success)

        page = await service.list_run_messages("thread-1", "run-sideband-1", limit=10)
        assert [row["event_type"] for row in page["data"]] == ["human_message", "ai_message"]
        assert page["data"][1]["content"]["content"] == "checkpoint answer"

        await db.close()

    asyncio.run(scenario())


def test_workflow_redacts_hidden_reasoning_content():
    async def scenario():
        service, db = await _make_runtime_service()

        await service.start_run(
            "thread-1",
            runs.RunCreateRequest(run_id="run-redact-1", assistant_id="lead_agent"),
        )
        await service.record_external_event(
            "thread-1",
            "run-redact-1",
            event_type="ai_message",
            caller="assistant",
            content={
                "type": "ai",
                "content": "<think>private reasoning</think>visible answer",
                "additional_kwargs": {"reasoning_content": "private chain"},
            },
        )

        workflow = await service.build_workflow("thread-1", "run-redact-1", limit=20)
        content = workflow["events"][0]["content"]
        assert content["content"] == "[hidden]visible answer"
        assert content["additional_kwargs"]["reasoning_content"] == "[hidden]"

        await db.close()

    asyncio.run(scenario())


def test_streaming_gateway_run_persists_visible_events():
    async def scenario():
        service, db = await _make_runtime_service()

        fake_client = MagicMock()
        fake_client.stream.return_value = iter(
            [
                SimpleNamespace(type="messages-tuple", data={"type": "ai", "content": "", "id": "ai-1", "tool_calls": [{"name": "search", "args": {}, "id": "call-1"}]}),
                SimpleNamespace(type="messages-tuple", data={"type": "tool", "content": "result", "name": "search", "tool_call_id": "call-1", "id": "tool-1"}),
                SimpleNamespace(type="messages-tuple", data={"type": "ai", "content": "done", "id": "ai-2", "usage_metadata": {"input_tokens": 3, "output_tokens": 4, "total_tokens": 7}}),
            ]
        )

        with (
            patch("app.gateway.services.get_paths") as mock_get_paths,
            patch("app.gateway.services.get_sync_checkpointer", return_value="sync-checkpointer"),
            patch("app.gateway.services.MedrixFlowClient", return_value=fake_client),
        ):
            mock_get_paths.return_value.ensure_thread_dirs.return_value = None
            record = await service.start_run(
                "thread-stream-1",
                runs.RunCreateRequest(
                    assistant_id="lead_agent",
                    input={"messages": [HumanMessage(content="hello")]},
                ),
            )
            assert record.task is not None
            await record.task

        workflow = await service.build_workflow("thread-stream-1", record.run_id, limit=20)
        assert workflow["run"]["status"] == "success"
        assert [event["event_type"] for event in workflow["events"]] == ["ai_tool_calls", "tool_message", "ai_message"]
        assert workflow["usage"]["total_tokens"] == 7

        await db.close()

    asyncio.run(scenario())


def test_gateway_run_threads_reasoning_effort_into_embedded_client():
    async def scenario():
        service, db = await _make_runtime_service()

        fake_client = MagicMock()
        fake_client.stream.return_value = iter([])

        with (
            patch("app.gateway.services.get_paths") as mock_get_paths,
            patch("app.gateway.services.get_sync_checkpointer", return_value="sync-checkpointer"),
            patch("app.gateway.services.MedrixFlowClient", return_value=fake_client) as mock_client_cls,
        ):
            mock_get_paths.return_value.ensure_thread_dirs.return_value = None
            record = await service.start_run(
                "thread-1",
                runs.RunCreateRequest(
                    assistant_id="lead_agent",
                    input={"messages": [HumanMessage(content="hello")]},
                    context={
                        "model_name": "gpt-5.4",
                        "thinking_enabled": True,
                        "reasoning_effort": "high",
                    },
                ),
            )
            assert record.task is not None
            await record.task

        assert mock_client_cls.call_args.kwargs["reasoning_effort"] == "high"
        await db.close()

    asyncio.run(scenario())


def test_materialization_failures_are_best_effort():
    async def scenario():
        service, db = await _make_runtime_service(
            messages=[HumanMessage(content="before"), AIMessage(content="after")]
        )
        await service.start_run(
            "thread-1",
            runs.RunCreateRequest(run_id="run-2", assistant_id="lead_agent"),
        )
        record = await service.require_run("thread-1", "run-2")

        async def boom(events):
            raise RuntimeError("db offline")

        service._event_store.put_batch = boom  # type: ignore[method-assign]
        await service.materialize_run_messages(
            record,
            finalize=True,
            final_status=RunStatus.success,
        )

        updated = await service.require_run("thread-1", "run-2")
        assert updated.messages_complete is True
        assert updated.status is RunStatus.success

        await db.close()

    asyncio.run(scenario())


def test_runs_router_and_feedback_end_to_end():
    service, db = asyncio.run(
        _make_runtime_service(messages=[HumanMessage(content="before")])
    )

    app = FastAPI()
    app.state.run_service = service
    app.include_router(runs.router)

    with TestClient(app) as client:
        response = client.post(
            "/api/threads/thread-1/runs",
            json={"run_id": "run-route-1", "assistant_id": "lead_agent"},
        )
        assert response.status_code == 200
        assert response.json()["run_id"] == "run-route-1"

        service._checkpointer.messages = [
            HumanMessage(content="before"),
            HumanMessage(content="follow up"),
            AIMessage(content="answer"),
        ]

        complete = client.post(
            "/api/threads/thread-1/runs/run-route-1/complete",
            json={"status": "success"},
        )
        assert complete.status_code == 200

        messages = client.get("/api/threads/thread-1/runs/run-route-1/messages")
        assert messages.status_code == 200
        assert len(messages.json()["data"]) == 2

        put_feedback = client.put(
            "/api/threads/thread-1/runs/run-route-1/feedback",
            json={"rating": 1},
        )
        assert put_feedback.status_code == 200
        assert put_feedback.json()["rating"] == 1

        get_feedback = client.get("/api/threads/thread-1/runs/run-route-1/feedback")
        assert get_feedback.status_code == 200
        assert get_feedback.json()["rating"] == 1

        delete_feedback = client.delete("/api/threads/thread-1/runs/run-route-1/feedback")
        assert delete_feedback.status_code == 204

    asyncio.run(db.close())
