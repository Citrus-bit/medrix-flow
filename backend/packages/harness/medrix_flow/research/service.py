from __future__ import annotations

import re
import uuid
from typing import Any, cast

from medrix_flow.academic.utils import detect_domain, slugify
from medrix_flow.runtime.utils import now_iso

from .repository import ResearchRepository
from .types import (
    GATED_TRANSITIONS,
    RESEARCH_STAGES,
    ClaimEvidenceRecord,
    ExperimentBranchRecord,
    ManuscriptSectionRecord,
    NoveltyCheckRecord,
    OverlapRisk,
    ResearchAdvanceResult,
    ResearchGate,
    ResearchLedgerEntry,
    ResearchQuest,
    ResearchQuestSnapshot,
    ResearchStage,
    ReviewerReportRecord,
)

_EMPIRICAL_METHOD_HINTS = {
    "difference-in-differences": "did",
    "staggered did": "staggered_did",
    "event study": "event_study",
    "event-study": "event_study",
    "instrumental variable": "iv",
    "regression discontinuity": "rdd",
    "synthetic control": "synthetic_control",
    "target trial": "target_trial",
    "causal forest": "causal_forest",
    "propensity score": "psm",
    "double machine learning": "dml",
    "survival": "survival",
    "tmle": "tmle",
    "did": "did",
    "iv": "iv",
    "rdd": "rdd",
    "psm": "psm",
    "ipw": "ipw",
    "dml": "dml",
}

_EMPIRICAL_DOMAIN_HINTS = {
    "applied economics",
    "econometric",
    "empirical",
    "finance",
    "management",
    "policy",
    "public health",
    "sociology",
}


class ResearchQuestService:
    def __init__(self, repository: ResearchRepository) -> None:
        self._repository = repository

    async def create_quest(
        self,
        *,
        thread_id: str,
        topic: str,
        title: str | None = None,
        scope: str | None = None,
        objective: str | None = None,
        domain: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResearchQuest:
        timestamp = now_iso()
        quest = ResearchQuest(
            quest_id=f"rq-{uuid.uuid4().hex[:12]}",
            thread_id=thread_id,
            title=(title or topic).strip(),
            topic=topic.strip(),
            scope=scope.strip() if scope else None,
            objective=objective.strip() if objective else None,
            domain=domain or self._detect_research_domain(topic, scope, objective, metadata),
            stage="intake",
            status="active",
            metadata=self._initial_metadata(topic=topic, scope=scope, objective=objective, metadata=metadata),
            created_at=timestamp,
            updated_at=timestamp,
        )
        created = await self._repository.create_quest(quest)
        await self._add_ledger(
            created,
            event_type="quest_created",
            summary="Research quest created and ready for staged execution.",
            inputs={"topic": topic, "scope": scope, "objective": objective},
            outputs={"stage": created.stage, "human_gates": list(GATED_TRANSITIONS.values())},
        )
        return created

    def _initial_metadata(
        self,
        *,
        topic: str,
        scope: str | None,
        objective: str | None,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        merged = dict(metadata or {})
        if self._is_empirical_research(topic, scope, objective, metadata):
            methods = self._infer_empirical_methods(topic, scope, objective, metadata)
            merged.setdefault("skill_guidance", []).append("empirical-research-methods")
            merged.setdefault("methodology_skill_path", "/mnt/skills/public/empirical-research-methods/SKILL.md")
            merged.setdefault("empirical_methods", methods)
            merged.setdefault(
                "experiment_metadata_contract",
                {
                    "required": [
                        "empirical_method",
                        "estimand",
                        "outcome",
                        "treatment_or_exposure",
                        "sample_restrictions",
                        "identification_assumptions",
                    ],
                    "conditional": [
                        "unit_id",
                        "time",
                        "treatment_time",
                        "instrument",
                        "running_variable",
                        "cutoff",
                        "covariates",
                        "fixed_effects",
                        "cluster",
                    ],
                },
            )
        return merged

    def _detect_research_domain(
        self,
        topic: str,
        scope: str | None,
        objective: str | None,
        metadata: dict[str, Any] | None,
    ) -> str:
        if self._is_empirical_research(topic, scope, objective, metadata):
            return "empirical_social_science"
        return detect_domain(topic, scope)

    def _is_empirical_research(
        self,
        topic: str,
        scope: str | None,
        objective: str | None,
        metadata: dict[str, Any] | None,
    ) -> bool:
        haystack = " ".join(
            [
                topic.lower(),
                (scope or "").lower(),
                (objective or "").lower(),
                " ".join(str(value).lower() for value in (metadata or {}).values()),
            ]
        )
        return any(hint in haystack for hint in _EMPIRICAL_DOMAIN_HINTS) or bool(
            self._infer_empirical_methods(topic, scope, objective, metadata)
        )

    def _infer_empirical_methods(
        self,
        topic: str,
        scope: str | None,
        objective: str | None,
        metadata: dict[str, Any] | None,
    ) -> list[str]:
        haystack = " ".join(
            [
                topic.lower(),
                (scope or "").lower(),
                (objective or "").lower(),
                " ".join(str(value).lower() for value in (metadata or {}).values()),
            ]
        )
        return sorted({method for hint, method in _EMPIRICAL_METHOD_HINTS.items() if hint in haystack})

    async def list_quests(self, thread_id: str | None = None) -> list[ResearchQuest]:
        return await self._repository.list_quests(thread_id)

    async def get_snapshot(self, quest_id: str) -> ResearchQuestSnapshot:
        quest = await self._require_quest(quest_id)
        return ResearchQuestSnapshot(
            quest=quest,
            ledger=await self._repository.list_ledger(quest_id),
            gates=await self._repository.list_gates(quest_id),
            evidence=await self._repository.list_claim_evidence(quest_id),
            novelty_checks=await self._repository.list_novelty_checks(quest_id),
            experiment_branches=await self._repository.list_experiment_branches(quest_id),
            manuscript_sections=await self._repository.list_manuscript_sections(quest_id),
            reviewer_reports=await self._repository.list_reviewer_reports(quest_id),
        )

    async def advance_quest(
        self,
        quest_id: str,
        *,
        target_stage: ResearchStage | None = None,
        inputs: dict[str, Any] | None = None,
        artifacts: list[str] | None = None,
        tool_name: str | None = None,
        model_name: str | None = None,
    ) -> ResearchAdvanceResult:
        quest = await self._require_quest(quest_id)
        inputs = inputs or {}
        artifacts = artifacts or []
        next_stage = target_stage or self._next_stage(quest.stage)
        if next_stage is None:
            entry = await self._add_ledger(
                quest,
                event_type="already_complete",
                summary="Research quest is already at final_bundle.",
                inputs=inputs,
                outputs={"stage": quest.stage},
                artifacts=artifacts,
                tool_name=tool_name,
                model_name=model_name,
            )
            return ResearchAdvanceResult(quest=quest, advanced=False, ledger_entry=entry)

        self._validate_transition(quest.stage, next_stage)
        if next_stage == "experiment_planned" and not await self._novelty_allows_experiment(quest.quest_id):
            gate = await self._ensure_gate(quest, next_stage, "novelty_override")
            if gate.status != "approved":
                quest.status = "blocked"
                quest.updated_at = now_iso()
                quest = await self._repository.update_quest(quest)
                entry = await self._add_ledger(
                    quest,
                    stage=next_stage,
                    event_type="novelty_block",
                    summary="High overlap risk blocks experiment planning until a human override is recorded.",
                    inputs=inputs,
                    outputs={"gate_type": gate.gate_type, "gate_status": gate.status},
                    artifacts=artifacts,
                    tool_name=tool_name,
                    model_name=model_name,
                )
                return ResearchAdvanceResult(
                    quest=quest,
                    advanced=False,
                    blocked=True,
                    required_gate=gate,
                    ledger_entry=entry,
                    generated={"reason": "high_overlap_risk"},
                )
        gate_type = GATED_TRANSITIONS.get(next_stage)
        if gate_type:
            gate = await self._ensure_gate(quest, next_stage, gate_type)
            if gate.status != "approved":
                quest.status = "blocked"
                quest.updated_at = now_iso()
                quest = await self._repository.update_quest(quest)
                entry = await self._add_ledger(
                    quest,
                    stage=next_stage,
                    event_type="gate_required",
                    summary=f"Human approval is required before entering {next_stage}.",
                    inputs=inputs,
                    outputs={"gate_type": gate.gate_type, "gate_status": gate.status},
                    artifacts=artifacts,
                    tool_name=tool_name,
                    model_name=model_name,
                )
                return ResearchAdvanceResult(
                    quest=quest,
                    advanced=False,
                    blocked=True,
                    required_gate=gate,
                    ledger_entry=entry,
                    generated={"reason": "human_gate_required"},
                )

        generated = await self._apply_stage(quest, next_stage, inputs, artifacts)
        quest.stage = next_stage
        quest.status = "completed" if next_stage == "final_bundle" else "active"
        quest.updated_at = now_iso()
        quest = await self._repository.update_quest(quest)
        entry = await self._add_ledger(
            quest,
            stage=next_stage,
            event_type="stage_advanced",
            summary=f"Research quest advanced to {next_stage}.",
            inputs=inputs,
            outputs=generated,
            artifacts=artifacts,
            tool_name=tool_name,
            model_name=model_name,
        )
        return ResearchAdvanceResult(
            quest=quest,
            advanced=True,
            ledger_entry=entry,
            generated=generated,
        )

    async def decide_gate(
        self,
        quest_id: str,
        *,
        stage: ResearchStage,
        gate_type: str,
        status: str,
        decision: str | None = None,
        reason: str | None = None,
    ) -> ResearchGate:
        quest = await self._require_quest(quest_id)
        if status not in {"approved", "rejected", "pending"}:
            raise ValueError("Gate status must be approved, rejected, or pending.")
        existing = await self._repository.get_gate(quest_id, stage, gate_type)
        timestamp = now_iso()
        gate = ResearchGate(
            gate_id=existing.gate_id if existing else f"gate-{uuid.uuid4().hex[:12]}",
            quest_id=quest_id,
            stage=stage,
            gate_type=gate_type,
            status=cast(Any, status),
            decision=decision,
            reason=reason,
            required=True,
            created_at=existing.created_at if existing else timestamp,
            decided_at=timestamp if status in {"approved", "rejected"} else None,
        )
        stored = await self._repository.upsert_gate(gate)
        quest.status = "active" if status == "approved" else "blocked"
        quest.updated_at = timestamp
        await self._repository.update_quest(quest)
        await self._add_ledger(
            quest,
            stage=stage,
            event_type="gate_decision",
            summary=f"Human gate {gate_type} marked {status}.",
            inputs={"gate_type": gate_type, "decision": decision, "reason": reason},
            outputs={"status": status},
            gate_decision=status,
        )
        return stored

    async def list_evidence(self, quest_id: str) -> list[ClaimEvidenceRecord]:
        await self._require_quest(quest_id)
        return await self._repository.list_claim_evidence(quest_id)

    async def list_experiment_branches(self, quest_id: str) -> list[ExperimentBranchRecord]:
        await self._require_quest(quest_id)
        return await self._repository.list_experiment_branches(quest_id)

    async def list_manuscript_sections(self, quest_id: str) -> list[ManuscriptSectionRecord]:
        await self._require_quest(quest_id)
        return await self._repository.list_manuscript_sections(quest_id)

    async def _apply_stage(
        self,
        quest: ResearchQuest,
        stage: ResearchStage,
        inputs: dict[str, Any],
        artifacts: list[str],
    ) -> dict[str, Any]:
        if stage == "literature":
            return await self._stage_literature(quest, inputs)
        if stage == "novelty_check":
            return await self._stage_novelty_check(quest, inputs)
        if stage == "evidence_verified":
            return await self._stage_evidence_verified(quest, inputs)
        if stage == "experiment_planned":
            return await self._stage_experiment_planned(quest, inputs)
        if stage == "experiment_running":
            return await self._stage_experiment_running(quest, inputs, artifacts)
        if stage == "results_synthesized":
            return await self._stage_results_synthesized(quest, inputs, artifacts)
        if stage == "manuscript_draft":
            return await self._stage_manuscript_draft(quest, inputs, artifacts)
        if stage == "review":
            return await self._stage_review(quest, inputs)
        if stage == "revision":
            return await self._stage_revision(quest, inputs)
        if stage == "final_bundle":
            return await self._stage_final_bundle(quest, artifacts)
        return {"stage": stage}

    async def _stage_literature(self, quest: ResearchQuest, inputs: dict[str, Any]) -> dict[str, Any]:
        academic_project_id = inputs.get("academic_project_id")
        if isinstance(academic_project_id, str) and academic_project_id:
            quest.academic_project_id = academic_project_id
            quest.metadata = {**quest.metadata, "academic_project_id": academic_project_id}
            await self._repository.update_quest(quest)

        created_claims = 0
        for claim in self._normalize_claims(inputs.get("claims")):
            await self._repository.add_claim_evidence(
                ClaimEvidenceRecord(
                    claim_id=f"claim-{uuid.uuid4().hex[:12]}",
                    quest_id=quest.quest_id,
                    claim=claim["claim"],
                    paper_id=claim.get("paper_id"),
                    source_title=claim.get("source_title"),
                    locator=claim.get("locator"),
                    snippet=claim.get("snippet"),
                    quote=claim.get("quote"),
                    support_status=claim.get("support_status", "uncertain"),
                    confidence=float(claim.get("confidence", 0.4)),
                    artifact_path=claim.get("artifact_path"),
                    metadata=claim.get("metadata", {}),
                    created_at=now_iso(),
                )
            )
            created_claims += 1

        if created_claims == 0:
            await self._repository.add_claim_evidence(
                ClaimEvidenceRecord(
                    claim_id=f"claim-{uuid.uuid4().hex[:12]}",
                    quest_id=quest.quest_id,
                    claim=f"The research question focuses on {quest.topic}.",
                    support_status="uncertain",
                    confidence=0.2,
                    metadata={"source": "intake-placeholder", "needs_full_text_verification": True},
                    created_at=now_iso(),
                )
            )
            created_claims = 1

        return {
            "academic_project_id": quest.academic_project_id,
            "claim_count": created_claims,
            "next_required": "Run or attach academic_research outputs for paper-backed evidence.",
        }

    async def _stage_novelty_check(self, quest: ResearchQuest, inputs: dict[str, Any]) -> dict[str, Any]:
        idea = str(inputs.get("idea") or quest.objective or quest.topic)
        closest_papers = self._normalize_dict_list(inputs.get("closest_papers"))
        hypotheses = [str(item).strip() for item in inputs.get("hypotheses", []) if str(item).strip()]
        if not hypotheses:
            hypotheses = [f"Test whether the proposed approach improves a measurable outcome for {quest.topic}."]
        risk = self._estimate_overlap_risk(idea, closest_papers, inputs.get("overlap_risk"))
        decision = "revise" if risk == "high" else "proceed"
        record = NoveltyCheckRecord(
            check_id=f"novelty-{uuid.uuid4().hex[:12]}",
            quest_id=quest.quest_id,
            idea=idea,
            overlap_risk=risk,
            closest_papers=closest_papers,
            hypotheses=hypotheses,
            minimum_experiment=str(
                inputs.get("minimum_experiment")
                or "Define one baseline, one ablation, fixed seeds, and a primary metric before execution."
            ),
            decision=decision,
            created_at=now_iso(),
        )
        await self._repository.add_novelty_check(record)
        return {
            "overlap_risk": risk,
            "decision": decision,
            "hypothesis_count": len(hypotheses),
            "closest_paper_count": len(closest_papers),
        }

    async def _stage_evidence_verified(self, quest: ResearchQuest, inputs: dict[str, Any]) -> dict[str, Any]:
        evidence = await self._repository.list_claim_evidence(quest.quest_id)
        if not evidence:
            await self._repository.add_claim_evidence(
                ClaimEvidenceRecord(
                    claim_id=f"claim-{uuid.uuid4().hex[:12]}",
                    quest_id=quest.quest_id,
                    claim=f"No source-backed claim has been attached for {quest.topic}.",
                    support_status="unsupported",
                    confidence=0.0,
                    metadata={"source": "evidence-integrity-gate"},
                    created_at=now_iso(),
                )
            )
            evidence = await self._repository.list_claim_evidence(quest.quest_id)
        counts: dict[str, int] = {}
        for item in evidence:
            counts[item.support_status] = counts.get(item.support_status, 0) + 1
        return {
            "claim_count": len(evidence),
            "support_status_counts": counts,
            "strict_rule": "Manuscript claims must remain linked to evidence or be marked unsupported.",
        }

    async def _stage_experiment_planned(self, quest: ResearchQuest, inputs: dict[str, Any]) -> dict[str, Any]:
        branch_payloads = self._normalize_dict_list(inputs.get("branches"))
        if not branch_payloads:
            metadata = {"budget_policy": "human approval required before execution"}
            if quest.domain == "empirical_social_science":
                metadata.update(
                    {
                        "skill_guidance": "empirical-research-methods",
                        "methodology_skill_path": "/mnt/skills/public/empirical-research-methods/SKILL.md",
                        "empirical_methods": quest.metadata.get("empirical_methods", []),
                        "identification_gate": "required before causal claims",
                        "experiment_lab_metadata_required": quest.metadata.get("experiment_metadata_contract", {}),
                    }
                )
            branch_payloads = [
                {
                    "name": "Baseline protocol",
                    "branch_type": "baseline",
                    "priority": 1.0,
                    "seed": 42,
                    "metadata": metadata,
                }
            ]
        created = 0
        for payload in branch_payloads:
            await self._repository.upsert_experiment_branch(
                ExperimentBranchRecord(
                    branch_id=str(payload.get("branch_id") or f"branch-{uuid.uuid4().hex[:12]}"),
                    quest_id=quest.quest_id,
                    experiment_project_id=payload.get("experiment_project_id"),
                    parent_branch_id=payload.get("parent_branch_id"),
                    name=str(payload.get("name") or "Experiment branch"),
                    branch_type=str(payload.get("branch_type") or "baseline"),
                    status=payload.get("status", "planned"),
                    priority=float(payload.get("priority", 0.0)),
                    seed=payload.get("seed"),
                    metrics=payload.get("metrics", {}),
                    artifact_paths=payload.get("artifact_paths", []),
                    failure_summary=payload.get("failure_summary"),
                    metadata=payload.get("metadata", {}),
                    created_at=now_iso(),
                    updated_at=now_iso(),
                )
            )
            created += 1
        await self._ensure_gate(quest, "experiment_running", "experiment_execution")
        return {"branch_count": created, "execution_gate": "experiment_execution"}

    async def _stage_experiment_running(
        self,
        quest: ResearchQuest,
        inputs: dict[str, Any],
        artifacts: list[str],
    ) -> dict[str, Any]:
        experiment_project_id = inputs.get("experiment_project_id")
        if isinstance(experiment_project_id, str) and experiment_project_id:
            ids = [*quest.experiment_project_ids]
            if experiment_project_id not in ids:
                ids.append(experiment_project_id)
            quest.experiment_project_ids = ids
            await self._repository.update_quest(quest)

        branches = await self._repository.list_experiment_branches(quest.quest_id)
        if branches:
            branch = branches[0]
            branch.status = "running" if not experiment_project_id else "completed"
            branch.experiment_project_id = experiment_project_id or branch.experiment_project_id
            branch.artifact_paths = sorted(set(branch.artifact_paths + artifacts))
            branch.updated_at = now_iso()
            await self._repository.upsert_experiment_branch(branch)
        return {
            "experiment_project_ids": quest.experiment_project_ids,
            "branch_status": "completed" if experiment_project_id else "running",
            "artifact_count": len(artifacts),
        }

    async def _stage_results_synthesized(
        self,
        quest: ResearchQuest,
        inputs: dict[str, Any],
        artifacts: list[str],
    ) -> dict[str, Any]:
        metrics = inputs.get("metrics") if isinstance(inputs.get("metrics"), dict) else {}
        branches = await self._repository.list_experiment_branches(quest.quest_id)
        for branch in branches:
            if metrics:
                branch.metrics = {**branch.metrics, **metrics}
            if artifacts:
                branch.artifact_paths = sorted(set(branch.artifact_paths + artifacts))
            if branch.status == "running":
                branch.status = "completed"
            branch.updated_at = now_iso()
            await self._repository.upsert_experiment_branch(branch)
        return {"branch_count": len(branches), "metric_keys": sorted(metrics), "artifact_count": len(artifacts)}

    async def _stage_manuscript_draft(
        self,
        quest: ResearchQuest,
        inputs: dict[str, Any],
        artifacts: list[str],
    ) -> dict[str, Any]:
        sections = self._normalize_dict_list(inputs.get("sections"))
        evidence = await self._repository.list_claim_evidence(quest.quest_id)
        claim_ids = [item.claim_id for item in evidence]
        if not sections:
            sections = [
                {"section_key": "introduction", "title": "Introduction"},
                {"section_key": "related_work", "title": "Related Work"},
                {"section_key": "methods", "title": "Methods"},
                {"section_key": "results", "title": "Results"},
                {"section_key": "limitations", "title": "Limitations"},
            ]
        for payload in sections:
            await self._repository.upsert_manuscript_section(
                ManuscriptSectionRecord(
                    section_id=str(payload.get("section_id") or f"section-{uuid.uuid4().hex[:12]}"),
                    quest_id=quest.quest_id,
                    section_key=str(payload.get("section_key") or slugify(str(payload.get("title") or "section"))),
                    title=str(payload.get("title") or "Section"),
                    content=str(payload.get("content") or ""),
                    claim_ids=payload.get("claim_ids", claim_ids),
                    artifact_paths=payload.get("artifact_paths", artifacts),
                    status=str(payload.get("status") or "draft"),
                    created_at=now_iso(),
                    updated_at=now_iso(),
                )
            )
        await self._ensure_gate(quest, "review", "pre_review")
        return {"section_count": len(sections), "linked_claim_count": len(claim_ids), "review_gate": "pre_review"}

    async def _stage_review(self, quest: ResearchQuest, inputs: dict[str, Any]) -> dict[str, Any]:
        evidence = await self._repository.list_claim_evidence(quest.quest_id)
        sections = await self._repository.list_manuscript_sections(quest.quest_id)
        unsupported = len([item for item in evidence if item.support_status == "unsupported"])
        profiles = ["methodology", "domain", "citation-integrity", "devils-advocate"]
        created = 0
        for profile in profiles:
            score = self._review_score(profile, evidence, sections, unsupported)
            verdict = "block" if score < 0.45 else "revise" if score < 0.75 else "pass"
            await self._repository.add_reviewer_report(
                ReviewerReportRecord(
                    report_id=f"review-{uuid.uuid4().hex[:12]}",
                    quest_id=quest.quest_id,
                    stage="review",
                    reviewer_profile=profile,
                    score=score,
                    verdict=verdict,
                    findings=self._review_findings(profile, unsupported, len(sections)),
                    required_actions=self._review_actions(profile, verdict),
                    created_at=now_iso(),
                )
            )
            created += 1
        await self._ensure_gate(quest, "final_bundle", "final_release")
        return {"reviewer_count": created, "unsupported_claims": unsupported, "final_gate": "final_release"}

    async def _stage_revision(self, quest: ResearchQuest, inputs: dict[str, Any]) -> dict[str, Any]:
        reports = await self._repository.list_reviewer_reports(quest.quest_id)
        required_actions = [action for report in reports for action in report.required_actions]
        completed_actions = [str(item) for item in inputs.get("completed_actions", [])]
        return {
            "required_action_count": len(required_actions),
            "completed_action_count": len(completed_actions),
            "remaining_action_count": max(len(required_actions) - len(completed_actions), 0),
        }

    async def _stage_final_bundle(self, quest: ResearchQuest, artifacts: list[str]) -> dict[str, Any]:
        snapshot = await self.get_snapshot(quest.quest_id)
        return {
            "artifact_count": len(artifacts),
            "claim_count": len(snapshot.evidence),
            "branch_count": len(snapshot.experiment_branches),
            "reviewer_count": len(snapshot.reviewer_reports),
            "bundle_policy": "Final output was released after human approval.",
        }

    async def _require_quest(self, quest_id: str) -> ResearchQuest:
        quest = await self._repository.get_quest(quest_id)
        if quest is None:
            raise ValueError(f"Research quest {quest_id} not found")
        return quest

    async def _add_ledger(
        self,
        quest: ResearchQuest,
        *,
        event_type: str,
        summary: str,
        stage: ResearchStage | None = None,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        artifacts: list[str] | None = None,
        tool_name: str | None = None,
        model_name: str | None = None,
        error: str | None = None,
        gate_decision: str | None = None,
    ) -> ResearchLedgerEntry:
        entry = ResearchLedgerEntry(
            entry_id=f"ledger-{uuid.uuid4().hex[:12]}",
            quest_id=quest.quest_id,
            stage=stage or quest.stage,
            event_type=event_type,
            summary=summary,
            inputs=inputs or {},
            outputs=outputs or {},
            artifacts=artifacts or [],
            tool_name=tool_name,
            model_name=model_name,
            error=error,
            gate_decision=gate_decision,
            created_at=now_iso(),
        )
        return await self._repository.add_ledger_entry(entry)

    async def _ensure_gate(self, quest: ResearchQuest, stage: ResearchStage, gate_type: str) -> ResearchGate:
        existing = await self._repository.get_gate(quest.quest_id, stage, gate_type)
        if existing is not None:
            return existing
        return await self._repository.upsert_gate(
            ResearchGate(
                gate_id=f"gate-{uuid.uuid4().hex[:12]}",
                quest_id=quest.quest_id,
                stage=stage,
                gate_type=gate_type,
                status="pending",
                required=True,
                created_at=now_iso(),
            )
        )

    async def _novelty_allows_experiment(self, quest_id: str) -> bool:
        checks = await self._repository.list_novelty_checks(quest_id)
        if not checks:
            return True
        latest = checks[-1]
        return latest.overlap_risk != "high" and latest.decision == "proceed"

    @staticmethod
    def _next_stage(stage: ResearchStage) -> ResearchStage | None:
        index = RESEARCH_STAGES.index(stage)
        if index >= len(RESEARCH_STAGES) - 1:
            return None
        return RESEARCH_STAGES[index + 1]

    @staticmethod
    def _validate_transition(current: ResearchStage, target: ResearchStage) -> None:
        current_index = RESEARCH_STAGES.index(current)
        target_index = RESEARCH_STAGES.index(target)
        if target_index != current_index + 1:
            raise ValueError(f"Invalid research stage transition: {current} -> {target}")

    @staticmethod
    def _normalize_claims(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        claims: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                claims.append({"claim": item.strip()})
            elif isinstance(item, dict) and str(item.get("claim", "")).strip():
                claims.append({**item, "claim": str(item["claim"]).strip()})
        return claims

    @staticmethod
    def _normalize_dict_list(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @staticmethod
    def _estimate_overlap_risk(idea: str, closest_papers: list[dict[str, Any]], requested: Any) -> OverlapRisk:
        if requested in {"low", "medium", "high"}:
            return cast(OverlapRisk, requested)
        idea_terms = {term for term in re.findall(r"[a-zA-Z0-9]+", idea.lower()) if len(term) > 4}
        if not closest_papers:
            return "medium"
        max_overlap = 0.0
        for paper in closest_papers:
            title = str(paper.get("title") or "").lower()
            title_terms = {term for term in re.findall(r"[a-zA-Z0-9]+", title) if len(term) > 4}
            if idea_terms:
                max_overlap = max(max_overlap, len(idea_terms & title_terms) / len(idea_terms))
        if max_overlap >= 0.5:
            return "high"
        if max_overlap >= 0.2:
            return "medium"
        return "low"

    @staticmethod
    def _review_score(
        profile: str,
        evidence: list[ClaimEvidenceRecord],
        sections: list[ManuscriptSectionRecord],
        unsupported_count: int,
    ) -> float:
        base = 0.7
        if not evidence:
            base -= 0.25
        if not sections:
            base -= 0.2
        if unsupported_count:
            base -= min(0.3, unsupported_count * 0.1)
        if profile == "citation-integrity" and unsupported_count:
            base -= 0.15
        if profile == "devils-advocate":
            base -= 0.05
        return max(0.0, min(1.0, base))

    @staticmethod
    def _review_findings(profile: str, unsupported_count: int, section_count: int) -> list[str]:
        findings = [f"{profile} review completed with structured integrity checks."]
        if unsupported_count:
            findings.append(f"{unsupported_count} claim(s) are still marked unsupported.")
        if section_count == 0:
            findings.append("No manuscript sections are available for review.")
        return findings

    @staticmethod
    def _review_actions(profile: str, verdict: str) -> list[str]:
        if verdict == "pass":
            return []
        if profile == "citation-integrity":
            return ["Resolve unsupported claims or explicitly mark them as limitations."]
        if profile == "methodology":
            return ["Document baseline, ablation, seed, metric, and failure handling."]
        if profile == "domain":
            return ["Confirm the stated contribution against closest related work."]
        return ["Add limitations and a concrete falsification path before final release."]
