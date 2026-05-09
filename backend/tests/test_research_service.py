from __future__ import annotations

import asyncio

import pytest

from medrix_flow.research import ResearchQuestService, ResearchRepository
from medrix_flow.runtime.db import SQLiteRuntimeDB


async def _make_service() -> tuple[ResearchQuestService, SQLiteRuntimeDB]:
    db = SQLiteRuntimeDB(":memory:")
    await db.connect()
    repo = ResearchRepository(db)
    await repo.setup()
    return ResearchQuestService(repo), db


def test_research_quest_lifecycle_gates_and_artifacts():
    async def scenario() -> None:
        service, db = await _make_service()
        quest = await service.create_quest(
            thread_id="thread-research-1",
            topic="claim-level evidence checking for biomedical agents",
            objective="Build a verifiable research assistant workflow",
        )
        assert quest.stage == "intake"

        literature = await service.advance_quest(
            quest.quest_id,
            inputs={
                "academic_project_id": "academic-1",
                "claims": [
                    {
                        "claim": "Claim-level citation checks reduce unsupported manuscript claims.",
                        "source_title": "Evidence Checking Systems",
                        "locator": "p. 3",
                        "snippet": "Citation checks identify unsupported claims in generated manuscripts.",
                        "support_status": "supported",
                        "confidence": 0.8,
                    }
                ],
            },
        )
        assert literature.quest.stage == "literature"
        assert literature.generated["claim_count"] == 1

        novelty = await service.advance_quest(
            quest.quest_id,
            inputs={
                "idea": "Claim-level evidence checking for biomedical agents",
                "closest_papers": [{"title": "Audit trails for research agents"}],
                "hypotheses": ["Evidence gates reduce unsupported claims."],
            },
        )
        assert novelty.quest.stage == "novelty_check"
        assert novelty.generated["decision"] == "proceed"

        evidence = await service.advance_quest(quest.quest_id)
        assert evidence.quest.stage == "evidence_verified"
        assert evidence.generated["support_status_counts"]["supported"] == 1

        planned = await service.advance_quest(
            quest.quest_id,
            inputs={"branches": [{"name": "Baseline evidence verifier", "branch_type": "baseline", "priority": 1.0}]},
        )
        assert planned.quest.stage == "experiment_planned"
        assert planned.generated["execution_gate"] == "experiment_execution"

        blocked_run = await service.advance_quest(quest.quest_id)
        assert blocked_run.blocked is True
        assert blocked_run.required_gate is not None
        assert blocked_run.required_gate.gate_type == "experiment_execution"

        await service.decide_gate(
            quest.quest_id,
            stage="experiment_running",
            gate_type="experiment_execution",
            status="approved",
            reason="Small local fixture only.",
        )
        running = await service.advance_quest(
            quest.quest_id,
            inputs={"experiment_project_id": "exp-1"},
            artifacts=["/mnt/user-data/outputs/metrics.json"],
        )
        assert running.quest.stage == "experiment_running"
        assert running.generated["branch_status"] == "completed"

        results = await service.advance_quest(
            quest.quest_id,
            inputs={"metrics": {"unsupported_claim_rate": 0.1}},
        )
        assert results.quest.stage == "results_synthesized"
        assert "unsupported_claim_rate" in results.generated["metric_keys"]

        manuscript = await service.advance_quest(quest.quest_id)
        assert manuscript.quest.stage == "manuscript_draft"
        assert manuscript.generated["review_gate"] == "pre_review"

        blocked_review = await service.advance_quest(quest.quest_id)
        assert blocked_review.blocked is True
        assert blocked_review.required_gate is not None
        assert blocked_review.required_gate.gate_type == "pre_review"

        await service.decide_gate(
            quest.quest_id,
            stage="review",
            gate_type="pre_review",
            status="approved",
        )
        review = await service.advance_quest(quest.quest_id)
        assert review.quest.stage == "review"
        assert review.generated["reviewer_count"] == 4

        revision = await service.advance_quest(
            quest.quest_id,
            inputs={"completed_actions": ["Documented baselines and limitations."]},
        )
        assert revision.quest.stage == "revision"

        blocked_final = await service.advance_quest(quest.quest_id)
        assert blocked_final.blocked is True
        assert blocked_final.required_gate is not None
        assert blocked_final.required_gate.gate_type == "final_release"

        await service.decide_gate(
            quest.quest_id,
            stage="final_bundle",
            gate_type="final_release",
            status="approved",
        )
        final = await service.advance_quest(quest.quest_id, artifacts=["/mnt/user-data/outputs/manuscript.md"])
        assert final.quest.stage == "final_bundle"
        assert final.quest.status == "completed"

        snapshot = await service.get_snapshot(quest.quest_id)
        assert len(snapshot.ledger) >= 10
        assert len(snapshot.evidence) == 1
        assert len(snapshot.experiment_branches) == 1
        assert len(snapshot.manuscript_sections) >= 5
        assert len(snapshot.reviewer_reports) == 4
        await db.close()

    asyncio.run(scenario())


def test_research_quest_rejects_invalid_stage_jump():
    async def scenario() -> None:
        service, db = await _make_service()
        quest = await service.create_quest(thread_id="thread-research-2", topic="novelty gates")
        with pytest.raises(ValueError, match="Invalid research stage transition"):
            await service.advance_quest(quest.quest_id, target_stage="experiment_planned")
        await db.close()

    asyncio.run(scenario())


def test_empirical_research_quest_attaches_method_skill_and_branch_contract():
    async def scenario() -> None:
        service, db = await _make_service()
        quest = await service.create_quest(
            thread_id="thread-empirical-1",
            topic="DID evaluation of education policy effects on student outcomes",
            objective="Run an empirical public policy analysis with event-study robustness.",
        )

        assert quest.domain == "empirical_social_science"
        assert "empirical-research-methods" in quest.metadata["skill_guidance"]
        assert quest.metadata["methodology_skill_path"] == "/mnt/skills/public/empirical-research-methods/SKILL.md"
        assert {"did", "event_study"} <= set(quest.metadata["empirical_methods"])

        await service.advance_quest(quest.quest_id)
        await service.advance_quest(
            quest.quest_id,
            inputs={
                "idea": "DID evaluation of education policy effects on student outcomes",
                "closest_papers": [{"title": "Education policy and student outcomes"}],
                "overlap_risk": "low",
            },
        )
        await service.advance_quest(quest.quest_id)
        planned = await service.advance_quest(quest.quest_id)

        assert planned.quest.stage == "experiment_planned"
        snapshot = await service.get_snapshot(quest.quest_id)
        branch = snapshot.experiment_branches[0]
        assert branch.metadata["skill_guidance"] == "empirical-research-methods"
        assert branch.metadata["identification_gate"] == "required before causal claims"
        assert branch.metadata["experiment_lab_metadata_required"]["required"]
        await db.close()

    asyncio.run(scenario())


def test_high_overlap_blocks_experiment_planning_until_override():
    async def scenario() -> None:
        service, db = await _make_service()
        quest = await service.create_quest(thread_id="thread-research-3", topic="graph neural network citation verifier")
        await service.advance_quest(quest.quest_id)
        await service.advance_quest(
            quest.quest_id,
            inputs={
                "idea": "Graph neural network citation verifier",
                "closest_papers": [{"title": "Graph neural network citation verifier"}],
            },
        )
        await service.advance_quest(quest.quest_id)
        blocked = await service.advance_quest(quest.quest_id)
        assert blocked.blocked is True
        assert blocked.required_gate is not None
        assert blocked.required_gate.gate_type == "novelty_override"

        await service.decide_gate(
            quest.quest_id,
            stage="experiment_planned",
            gate_type="novelty_override",
            status="approved",
            reason="User explicitly accepts overlap risk for replication.",
        )
        planned = await service.advance_quest(quest.quest_id)
        assert planned.quest.stage == "experiment_planned"
        await db.close()

    asyncio.run(scenario())
