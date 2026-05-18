from __future__ import annotations

import importlib
from types import SimpleNamespace

from medrix_flow.config.app_config import AppConfig, ResearchConfig
from medrix_flow.config.sandbox_config import SandboxConfig
from medrix_flow.research import PipelineRunResult

research_tool_module = importlib.import_module("medrix_flow.tools.builtins.research_assistant_tool")


def _make_runtime(tmp_path, *, model_name: str | None = "thread-model") -> SimpleNamespace:
    context = {"thread_id": "thread-research-tool"}
    if model_name:
        context["model_name"] = model_name
    return SimpleNamespace(
        state={},
        context=context,
        config={"configurable": {"model_name": model_name}} if model_name else {},
    )


def _make_config() -> AppConfig:
    return AppConfig(
        models=[],
        sandbox=SandboxConfig(use="medrix_flow.sandbox.local:LocalSandboxProvider"),
        research=ResearchConfig(
            manuscript_model="configured-manuscript-model",
            fast_draft_model="configured-fast-draft-model",
            finalization_model="configured-finalization-model",
            default_auto_gates=["pre_review"],
            default_max_stages=4,
            default_quality_mode="strict_gate",
            default_quality_repair_budget=1,
        ),
    )


def test_research_assistant_run_pipeline_action_dispatches(monkeypatch, tmp_path):
    captured: dict = {}
    generated = {}

    class DummyPaths:
        research_db_file = tmp_path / "research.sqlite3"

    async def fake_run_pipeline(self, quest_id, **kwargs):
        captured["quest_id"] = quest_id
        captured.update(kwargs)
        generated["content"] = await kwargs["content_generator"]("introduction", SimpleNamespace())
        return PipelineRunResult(
            quest_id=quest_id,
            status="stopped_at_max_stages",
            final_stage="evidence_verified",
            message="stopped",
        )

    def fake_build_content_generator(model_name):
        captured["model_name"] = model_name

        async def generate(section_key, snapshot):
            return f"{model_name}:{section_key}:{type(snapshot).__name__}"

        return generate

    monkeypatch.setattr(research_tool_module, "get_paths", lambda: DummyPaths())
    monkeypatch.setattr(research_tool_module, "get_app_config", _make_config)
    monkeypatch.setattr(research_tool_module, "_build_content_generator", fake_build_content_generator)
    monkeypatch.setattr(research_tool_module.ResearchQuestOrchestrator, "run_pipeline", fake_run_pipeline)

    result = research_tool_module.research_assistant_tool.coroutine(
        runtime=_make_runtime(tmp_path),
        tool_call_id="tc-research",
        action="run_pipeline",
        quest_id="rq-existing",
        auto_gates=["experiment_execution"],
        max_stages=2,
        quality_mode="audit_only",
        quality_repair_budget=3,
    )

    import asyncio

    command = asyncio.run(result)
    message = command.update["messages"][0].content

    assert captured["quest_id"] == "rq-existing"
    assert captured["auto_gates"] == ["experiment_execution", "pre_review", "final_release"]
    assert captured["max_stages"] == 2
    assert captured["quality_mode"] == "audit_only"
    assert captured["repair_budget"] == 3
    assert captured["delivery_mode"] == "final_only"
    assert captured["model_name"] == "configured-finalization-model"
    assert generated["content"] == "configured-finalization-model:introduction:SimpleNamespace"
    assert "Research pipeline `rq-existing` returned `stopped_at_max_stages`" in message


def test_research_assistant_run_pipeline_uses_config_defaults(monkeypatch, tmp_path):
    captured: dict = {}

    class DummyPaths:
        research_db_file = tmp_path / "research.sqlite3"

    async def fake_run_pipeline(self, quest_id, **kwargs):
        captured.update(kwargs)
        return PipelineRunResult(
            quest_id=quest_id,
            status="blocked_on_gate",
            final_stage="experiment_planned",
            blocked_gate="experiment_execution",
            message="blocked",
        )

    monkeypatch.setattr(research_tool_module, "get_paths", lambda: DummyPaths())
    monkeypatch.setattr(research_tool_module, "get_app_config", _make_config)
    monkeypatch.setattr(research_tool_module, "_build_content_generator", lambda model_name: captured.setdefault("model_name", model_name))
    monkeypatch.setattr(research_tool_module.ResearchQuestOrchestrator, "run_pipeline", fake_run_pipeline)

    import asyncio

    command = asyncio.run(
        research_tool_module.research_assistant_tool.coroutine(
            runtime=_make_runtime(tmp_path),
            tool_call_id="tc-research",
            action="run_pipeline",
            quest_id="rq-existing",
        )
    )

    assert captured["auto_gates"] == ["pre_review", "experiment_execution", "final_release"]
    assert captured["max_stages"] == 11
    assert captured["quality_mode"] == "strict_gate"
    assert captured["repair_budget"] == 1
    assert captured["delivery_mode"] == "final_only"
    assert captured["model_name"] == "configured-finalization-model"
    assert "Blocked gate: `experiment_execution`." in command.update["messages"][0].content


def test_research_assistant_fast_draft_registers_finalization_run(monkeypatch, tmp_path):
    captured: dict = {}
    created_tasks = []

    class DummyPaths:
        research_db_file = tmp_path / "research.sqlite3"
        runtime_db_file = tmp_path / "runtime.sqlite3"

        def sandbox_outputs_dir(self, thread_id):
            path = tmp_path / "threads" / thread_id / "user-data" / "outputs"
            path.mkdir(parents=True, exist_ok=True)
            return path

    class DummyService:
        def __init__(self, repository):
            self.repository = repository

        async def list_quests(self, thread_id):
            return []

        async def create_quest(self, **kwargs):
            raise AssertionError("create_quest should not be called")

        async def get_snapshot(self, quest_id):
            return SimpleNamespace(
                quest=SimpleNamespace(quest_id=quest_id, title="Draft Title"),
                manuscript_sections=[
                    SimpleNamespace(title="Introduction", content="Draft introduction."),
                    SimpleNamespace(title="Methods", content="Draft methods."),
                ],
            )

    async def fake_run_pipeline(self, quest_id, **kwargs):
        captured.update(kwargs)
        return PipelineRunResult(
            quest_id=quest_id,
            status="draft_ready",
            final_stage="manuscript_draft",
            message="draft ready",
        )

    async def fake_register_finalization_run(thread_id, quest_id):
        captured["registered_thread_id"] = thread_id
        captured["registered_quest_id"] = quest_id
        return "run-finalization"

    async def fake_set_quest_metadata(quest_id, metadata):
        captured["metadata_quest_id"] = quest_id
        captured["metadata"] = metadata

    async def fake_attach_draft_artifact(quest_id, artifact):
        captured["attached"] = (quest_id, artifact)

    def fake_create_task(coro):
        created_tasks.append(coro)
        coro.close()
        return SimpleNamespace()

    monkeypatch.setattr(research_tool_module, "get_paths", lambda: DummyPaths())
    monkeypatch.setattr(research_tool_module, "get_app_config", _make_config)
    monkeypatch.setattr(research_tool_module, "_build_content_generator", lambda model_name: captured.setdefault("model_name", model_name))
    monkeypatch.setattr(research_tool_module, "_register_finalization_run", fake_register_finalization_run)
    monkeypatch.setattr(research_tool_module, "_set_quest_metadata", fake_set_quest_metadata)
    monkeypatch.setattr(research_tool_module, "_attach_draft_artifact", fake_attach_draft_artifact)
    monkeypatch.setattr(research_tool_module.asyncio, "create_task", fake_create_task)
    monkeypatch.setattr(research_tool_module, "ResearchQuestService", DummyService)
    monkeypatch.setattr(research_tool_module.ResearchQuestOrchestrator, "run_pipeline", fake_run_pipeline)

    import asyncio

    command = asyncio.run(
        research_tool_module.research_assistant_tool.coroutine(
            runtime=_make_runtime(tmp_path),
            tool_call_id="tc-research",
            action="run_pipeline",
            quest_id="rq-existing",
            delivery_mode="fast_draft_first",
        )
    )

    message = command.update["messages"][0].content
    assert "finalization run `run-finalization`" in message
    assert captured["metadata_quest_id"] == "rq-existing"
    assert captured["metadata"]["delivery_mode"] == "fast_draft_first"
    assert captured["metadata"]["finalization_run_id"] == "run-finalization"
    assert captured["attached"][0] == "rq-existing"
    assert captured["attached"][1].endswith("/fast-draft-rq-existing.tex")
    assert captured["model_name"] == "configured-fast-draft-model"
    assert created_tasks


def test_research_assistant_final_only_exports_pdf_artifacts(monkeypatch, tmp_path):
    captured: dict = {"metadata_updates": []}

    class DummyPaths:
        research_db_file = tmp_path / "research.sqlite3"

    class DummyService:
        def __init__(self, repository):
            self.repository = repository

        async def list_quests(self, thread_id):
            return []

        async def create_quest(self, **kwargs):
            raise AssertionError("create_quest should not be called")

        async def get_snapshot(self, quest_id):
            return SimpleNamespace(quest=SimpleNamespace(quest_id=quest_id))

    async def fake_run_pipeline(self, quest_id, **kwargs):
        captured.update(kwargs)
        return PipelineRunResult(
            quest_id=quest_id,
            status="completed",
            final_stage="final_bundle",
            message="completed",
        )

    async def fake_export(thread_id, snapshot):
        captured["export_thread_id"] = thread_id
        captured["export_quest_id"] = snapshot.quest.quest_id
        return research_tool_module.FinalBundleExportResult(
            artifacts=[
                "/mnt/user-data/outputs/manuscript-rq-existing.pdf",
                "/mnt/user-data/outputs/manuscript-rq-existing.tex",
                "/mnt/user-data/outputs/references.bib",
                "/mnt/user-data/outputs/citation_audit.json",
            ],
            message="PASS: manuscript_export wrote `/mnt/user-data/outputs/manuscript-rq-existing.pdf`.",
            status="passed",
        )

    async def fake_set_quest_metadata(quest_id, metadata):
        captured["metadata_updates"].append((quest_id, metadata))

    monkeypatch.setattr(research_tool_module, "get_paths", lambda: DummyPaths())
    monkeypatch.setattr(research_tool_module, "get_app_config", _make_config)
    monkeypatch.setattr(research_tool_module, "_build_content_generator", lambda model_name: captured.setdefault("model_name", model_name))
    monkeypatch.setattr(research_tool_module, "_set_quest_metadata", fake_set_quest_metadata)
    monkeypatch.setattr(research_tool_module, "_export_final_manuscript_bundle", fake_export)
    monkeypatch.setattr(research_tool_module, "ResearchQuestService", DummyService)
    monkeypatch.setattr(research_tool_module.ResearchQuestOrchestrator, "run_pipeline", fake_run_pipeline)

    import asyncio

    command = asyncio.run(
        research_tool_module.research_assistant_tool.coroutine(
            runtime=_make_runtime(tmp_path),
            tool_call_id="tc-research",
            action="run_pipeline",
            quest_id="rq-existing",
        )
    )

    message = command.update["messages"][0].content
    assert command.update["artifacts"][0] == "/mnt/user-data/outputs/manuscript-rq-existing.pdf"
    assert "Final PDF export passed" in message
    assert captured["delivery_mode"] == "final_only"
    assert captured["max_stages"] == 11
    assert captured["model_name"] == "configured-finalization-model"
    final_metadata = captured["metadata_updates"][-1][1]
    assert final_metadata["final_bundle_export_status"] == "passed"
    assert final_metadata["final_bundle_artifacts"][0].endswith(".pdf")
    assert "final_bundle_ready_at" in final_metadata


def test_research_assistant_final_only_returns_blocking_export_artifacts(monkeypatch, tmp_path):
    captured: dict = {"metadata_updates": []}

    class DummyPaths:
        research_db_file = tmp_path / "research.sqlite3"

    class DummyService:
        def __init__(self, repository):
            self.repository = repository

        async def list_quests(self, thread_id):
            return []

        async def create_quest(self, **kwargs):
            raise AssertionError("create_quest should not be called")

        async def get_snapshot(self, quest_id):
            return SimpleNamespace(quest=SimpleNamespace(quest_id=quest_id))

    async def fake_run_pipeline(self, quest_id, **kwargs):
        captured.update(kwargs)
        return PipelineRunResult(
            quest_id=quest_id,
            status="completed",
            final_stage="final_bundle",
            message="completed",
        )

    async def fake_export(thread_id, snapshot):
        return research_tool_module.FinalBundleExportResult(
            artifacts=[
                "/mnt/user-data/outputs/citation_audit.json",
                "/mnt/user-data/outputs/manuscript-rq-existing.tex",
                "/mnt/user-data/outputs/references.bib",
            ],
            message="FAIL: citation audit blocked PDF generation.",
            status="blocked",
        )

    async def fake_set_quest_metadata(quest_id, metadata):
        captured["metadata_updates"].append((quest_id, metadata))

    monkeypatch.setattr(research_tool_module, "get_paths", lambda: DummyPaths())
    monkeypatch.setattr(research_tool_module, "get_app_config", _make_config)
    monkeypatch.setattr(research_tool_module, "_build_content_generator", lambda model_name: captured.setdefault("model_name", model_name))
    monkeypatch.setattr(research_tool_module, "_set_quest_metadata", fake_set_quest_metadata)
    monkeypatch.setattr(research_tool_module, "_export_final_manuscript_bundle", fake_export)
    monkeypatch.setattr(research_tool_module, "ResearchQuestService", DummyService)
    monkeypatch.setattr(research_tool_module.ResearchQuestOrchestrator, "run_pipeline", fake_run_pipeline)

    import asyncio

    command = asyncio.run(
        research_tool_module.research_assistant_tool.coroutine(
            runtime=_make_runtime(tmp_path),
            tool_call_id="tc-research",
            action="run_pipeline",
            quest_id="rq-existing",
        )
    )

    message = command.update["messages"][0].content
    assert command.update["artifacts"] == [
        "/mnt/user-data/outputs/citation_audit.json",
        "/mnt/user-data/outputs/manuscript-rq-existing.tex",
        "/mnt/user-data/outputs/references.bib",
    ]
    assert "Final bundle export was blocked" in message
    assert "FAIL: citation audit blocked PDF generation" in message
    final_metadata = captured["metadata_updates"][-1][1]
    assert final_metadata["final_bundle_export_status"] == "blocked"
    assert "final_bundle_ready_at" not in final_metadata
