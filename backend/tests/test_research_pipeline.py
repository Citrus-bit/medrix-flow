from __future__ import annotations

import asyncio
import json
import time

from medrix_flow.research import PipelineRunResult, PipelineStageEvent, ResearchQuestOrchestrator, ResearchQuestService
from medrix_flow.research.repository import ResearchRepository
from medrix_flow.runtime.db import SQLiteRuntimeDB
from medrix_flow.runtime.utils import now_iso


async def _make_pipeline() -> tuple[ResearchQuestOrchestrator, ResearchQuestService, ResearchRepository, SQLiteRuntimeDB]:
    db = SQLiteRuntimeDB(":memory:")
    await db.connect()
    repo = ResearchRepository(db)
    await repo.setup()
    service = ResearchQuestService(repo)
    return ResearchQuestOrchestrator(service), service, repo, db


def test_pipeline_run_result_serializes_and_defaults_are_isolated():
    first_event = PipelineStageEvent(stage="literature", entered_at="2026-05-10T00:00:00Z")
    second_event = PipelineStageEvent(stage="review", entered_at="2026-05-10T00:00:01Z")
    first_event.outputs["claim_count"] = 3
    first_event.artifacts.append("/mnt/user-data/outputs/literature.json")

    assert second_event.outputs == {}
    assert second_event.artifacts == []

    result = PipelineRunResult(
        quest_id="rq-test",
        status="stopped_at_max_stages",
        stages_executed=[first_event, second_event],
        final_stage="review",
        message="Pipeline stopped after 2 stages.",
    )

    payload = json.loads(result.model_dump_json())
    assert payload["quest_id"] == "rq-test"
    assert payload["status"] == "stopped_at_max_stages"
    assert payload["final_stage"] == "review"
    assert payload["stages_executed"][0]["outputs"]["claim_count"] == 3
    assert payload["blocked_gate"] is None


def test_research_pipeline_happy_path_auto_approves_gates():
    async def scenario() -> None:
        orchestrator, service, _repo, db = await _make_pipeline()
        quest = await service.create_quest(thread_id="thread-pipeline-1", topic="citation integrity for agents")

        async def content_generator(section_key, snapshot):
            return f"Generated {section_key} for {snapshot.quest.topic}."

        async def reviewer_generator(profile, snapshot):
            return {"profile": profile, "quest_id": snapshot.quest.quest_id}

        result = await orchestrator.run_pipeline(
            quest.quest_id,
            auto_gates=["experiment_execution", "pre_review", "final_release"],
            content_generator=content_generator,
            reviewer_generator=reviewer_generator,
        )

        assert result.status == "completed"
        assert result.final_stage == "final_bundle"
        assert [event.stage for event in result.stages_executed][-1] == "final_bundle"
        assert {event.stage for event in result.stages_executed} >= {
            "literature",
            "novelty_check",
            "experiment_planned",
            "manuscript_draft",
            "review",
        }
        snapshot = await service.get_snapshot(quest.quest_id)
        assert snapshot.quest.status == "completed"
        assert {gate.gate_type: gate.status for gate in snapshot.gates} == {
            "experiment_execution": "approved",
            "pre_review": "approved",
            "final_quality_repair": "pending",
            "final_release": "approved",
        }
        assert len([entry for entry in snapshot.ledger if entry.event_type == "quality_repair_required"]) == 2
        assert len([entry for entry in snapshot.ledger if entry.event_type == "quality_repair_attempted"]) == 2
        await db.close()

    asyncio.run(scenario())


def test_research_pipeline_fast_draft_first_stops_after_manuscript_draft():
    async def scenario() -> None:
        orchestrator, service, _repo, db = await _make_pipeline()
        quest = await service.create_quest(thread_id="thread-pipeline-fast-draft", topic="fast manuscript drafts")

        async def content_generator(section_key, snapshot):
            return f"Generated {section_key} for {snapshot.quest.topic}."

        result = await orchestrator.run_pipeline(
            quest.quest_id,
            auto_gates=["experiment_execution"],
            max_stages=8,
            delivery_mode="fast_draft_first",
            content_generator=content_generator,
        )

        assert result.status == "draft_ready"
        assert result.final_stage == "manuscript_draft"
        assert [event.stage for event in result.stages_executed][-1] == "manuscript_draft"
        snapshot = await service.get_snapshot(quest.quest_id)
        assert snapshot.quest.stage == "manuscript_draft"
        assert snapshot.quest.metadata["draft_status"] == "draft_ready"
        assert len(snapshot.manuscript_sections) == 5
        assert {section.status for section in snapshot.manuscript_sections} == {"draft_ready"}
        await db.close()

    asyncio.run(scenario())


def test_manuscript_sections_generate_concurrently():
    async def scenario() -> None:
        _orchestrator, service, _repo, db = await _make_pipeline()
        quest = await service.create_quest(thread_id="thread-concurrent-draft", topic="concurrent drafts")
        await service.advance_quest(quest.quest_id, target_stage="literature")
        await service.advance_quest(quest.quest_id, target_stage="novelty_check")
        await service.advance_quest(quest.quest_id, target_stage="evidence_verified")
        await service.advance_quest(quest.quest_id, target_stage="experiment_planned")
        await service.decide_gate(
            quest.quest_id,
            stage="experiment_running",
            gate_type="experiment_execution",
            status="approved",
        )
        await service.advance_quest(quest.quest_id, target_stage="experiment_running")
        await service.advance_quest(quest.quest_id, target_stage="results_synthesized")
        started: list[float] = []

        async def content_generator(section_key, snapshot):
            started.append(time.perf_counter())
            await asyncio.sleep(0.05)
            return f"Generated {section_key}."

        before = time.perf_counter()
        result = await service.advance_quest(
            quest.quest_id,
            target_stage="manuscript_draft",
            inputs={"section_concurrency": 5},
            content_generator=content_generator,
        )
        elapsed = time.perf_counter() - before

        assert result.generated["section_generation_mode"] == "parallel"
        assert result.generated["section_generation_concurrency"] == 5
        assert len(started) == 5
        assert max(started) - min(started) < 0.04
        assert elapsed < 0.2
        await db.close()

    asyncio.run(scenario())


def test_research_pipeline_strict_quality_mode_blocks_on_quality_gate():
    async def scenario() -> None:
        orchestrator, service, _repo, db = await _make_pipeline()
        quest = await service.create_quest(thread_id="thread-pipeline-quality", topic="citation integrity for agents")

        result = await orchestrator.run_pipeline(
            quest.quest_id,
            auto_gates=["experiment_execution", "pre_review", "final_release"],
            quality_mode="strict_gate",
        )

        assert result.status == "blocked_on_gate"
        assert result.blocked_gate == "final_quality_repair"
        assert result.final_stage == "revision"
        await db.close()

    asyncio.run(scenario())


def test_research_pipeline_stops_at_max_stages():
    async def scenario() -> None:
        orchestrator, service, _repo, db = await _make_pipeline()
        quest = await service.create_quest(thread_id="thread-pipeline-2", topic="evidence workflows")

        result = await orchestrator.run_pipeline(quest.quest_id, max_stages=3)

        assert result.status == "stopped_at_max_stages"
        assert len(result.stages_executed) == 3
        assert result.final_stage == "evidence_verified"
        await db.close()

    asyncio.run(scenario())


def test_research_pipeline_blocks_on_non_auto_gate():
    async def scenario() -> None:
        orchestrator, service, _repo, db = await _make_pipeline()
        quest = await service.create_quest(thread_id="thread-pipeline-3", topic="agent experiment gates")

        result = await orchestrator.run_pipeline(quest.quest_id, max_stages=5)

        assert result.status == "blocked_on_gate"
        assert result.blocked_gate == "experiment_execution"
        assert result.final_stage == "experiment_planned"
        assert [event.stage for event in result.stages_executed][-1] == "experiment_planned"
        await db.close()

    asyncio.run(scenario())


def test_research_pipeline_returns_cancelled_status():
    async def scenario() -> None:
        orchestrator, service, repo, db = await _make_pipeline()
        quest = await service.create_quest(thread_id="thread-pipeline-4", topic="cancelled quest")
        quest.status = "cancelled"
        quest.updated_at = now_iso()
        await repo.update_quest(quest)

        result = await orchestrator.run_pipeline(quest.quest_id)

        assert result.status == "cancelled"
        assert result.stages_executed == []
        assert result.final_stage == "intake"
        await db.close()

    asyncio.run(scenario())
