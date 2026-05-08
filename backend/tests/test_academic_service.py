import asyncio
from pathlib import Path

from medrix_flow.academic import AcademicRepository, AcademicResearchService
from medrix_flow.academic.types import PaperAuthor, PaperRecord
from medrix_flow.config import paths as paths_module
from medrix_flow.runtime.db import SQLiteRuntimeDB
from medrix_flow.runtime.utils import now_iso


class FakeAdapter:
    def __init__(self, name: str, papers: list[PaperRecord]) -> None:
        self.name = name
        self._papers = papers

    async def search(self, query: str, *, project_id: str, limit: int) -> list[PaperRecord]:
        results: list[PaperRecord] = []
        for paper in self._papers[:limit]:
            results.append(paper.model_copy(update={"project_id": project_id, "paper_id": f"{project_id}:{paper.paper_id}"}))
        return results


def _paper(
    *,
    provider: str,
    provider_id: str,
    title: str,
    year: int,
    venue: str,
    doi: str | None,
    abstract: str,
    referenced_works: list[str] | None = None,
) -> PaperRecord:
    return PaperRecord(
        paper_id=f"{provider}:{provider_id}",
        project_id="project-x",
        canonical_id=f"doi:{doi.lower()}" if doi else f"{provider}:{provider_id}",
        title=title,
        authors=[PaperAuthor(display_name="Alice Smith", given_name="Alice", family_name="Smith", ordinal=0)],
        year=year,
        venue=venue,
        abstract=abstract,
        doi=doi,
        provider=provider,
        provider_id=provider_id,
        source_url=f"https://example.org/{provider_id}",
        oa_url=None,
        metadata_only=False,
        keywords=[],
        methods=["benchmarking"] if "benchmark" in abstract.lower() else ["review"],
        populations=["patients"] if "patient" in abstract.lower() else [],
        conflict_flags=["challenge"] if "challenge" in abstract.lower() else [],
        raw_source={"referenced_works": referenced_works or []},
        created_at=now_iso(),
        updated_at=now_iso(),
    )


def test_academic_service_reuses_project_and_prefers_local_uploads(tmp_path, monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv("MEDRIX_FLOW_HOME", str(tmp_path))
        paths_module._paths = None

        uploads_dir = paths_module.get_paths().sandbox_uploads_dir("thread-1")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        (uploads_dir / "uploaded-paper.md").write_text(
            "# Uploaded Evidence Paper\n\nDOI: 10.9999/uploaded\n\n2023\n\nA patient benchmark challenge with practical limitations.",
            encoding="utf-8",
        )

        db = SQLiteRuntimeDB(":memory:")
        await db.connect()
        repo = AcademicRepository(db)
        await repo.setup()
        service = AcademicResearchService(repo, adapters=[FakeAdapter("openalex", [])])

        first = await service.create_project(thread_id="thread-1", topic="clinical reasoning foundation models")
        second = await service.create_project(thread_id="thread-1", topic="clinical reasoning foundation models")
        assert first.project_id == second.project_id

        ingested = await service.ingest_project(first.project_id, max_candidates=20, core_paper_limit=20)
        assert ingested.paper_count >= 1
        assert any(paper.provider == "local-upload" for paper in ingested.selected_papers)

        await db.close()

    asyncio.run(scenario())


def test_academic_service_synthesizes_exports_and_graph(tmp_path, monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv("MEDRIX_FLOW_HOME", str(tmp_path))
        paths_module._paths = None

        db = SQLiteRuntimeDB(":memory:")
        await db.connect()
        repo = AcademicRepository(db)
        await repo.setup()
        base_papers = [
            _paper(
                provider="openalex",
                provider_id="w1",
                title="Foundation models for clinical reasoning",
                year=2025,
                venue="Journal of Clinical AI",
                doi="10.1000/w1",
                abstract="A review of clinical reasoning methods and benchmark design.",
                referenced_works=["https://openalex.org/w2"],
            ),
            _paper(
                provider="openalex",
                provider_id="w2",
                title="Benchmark datasets for patient-facing decision support",
                year=2024,
                venue="Medical Data Systems",
                doi="10.1000/w2",
                abstract="Benchmark dataset construction for patient decision support with empirical evaluation.",
            ),
            _paper(
                provider="crossref",
                provider_id="w3",
                title="Challenges in multimodal evidence synthesis",
                year=2023,
                venue="Computational Medicine Review",
                doi="10.1000/w3",
                abstract="A review describing challenge patterns, limitations, and controversy in evidence synthesis.",
            ),
            _paper(
                provider="arxiv",
                provider_id="2501.12345",
                title="Hybrid retrieval pipelines for experiment reports",
                year=2025,
                venue="arXiv",
                doi=None,
                abstract="A benchmark study on hybrid retrieval pipelines for experiment reports and open questions.",
            ),
        ]
        service = AcademicResearchService(repo, adapters=[FakeAdapter("openalex", base_papers)])

        project = await service.create_project(thread_id="thread-2", topic="experiment report retrieval")
        ingested = await service.ingest_project(project.project_id, max_candidates=20, core_paper_limit=20)
        assert ingested.paper_count >= 4

        output_dir = tmp_path / "thread-2-outputs"
        result = await service.synthesize_project(project.project_id, output_dir=output_dir, include_graph=True)

        export_files = {Path(path).name for path in result.export_files}
        assert {
            "report.md",
            "references.md",
            "references.bib",
            "evidence_map.json",
            "graph.json",
            "retrieval_audit.json",
        } <= export_files
        assert len([entry for entry in result.references if entry.included_in_final]) >= 3
        assert len(result.graph.nodes) >= 4
        assert len(result.graph.edges) >= 4
        assert any("Candidate Innovation Directions" in Path(path).read_text(encoding="utf-8") for path in result.export_files if path.endswith("report.md"))

        await db.close()

    asyncio.run(scenario())


def test_academic_service_prefers_published_versions_and_exports_all_verified_references(tmp_path, monkeypatch):
    async def scenario() -> None:
        monkeypatch.setenv("MEDRIX_FLOW_HOME", str(tmp_path))
        paths_module._paths = None

        db = SQLiteRuntimeDB(":memory:")
        await db.connect()
        repo = AcademicRepository(db)
        await repo.setup()

        matched_doi = "10.5555/final-version"
        papers = [
            _paper(
                provider="arxiv",
                provider_id="2501.11111",
                title="Retrieval-augmented evaluation for large language models",
                year=2025,
                venue="arXiv",
                doi=matched_doi,
                abstract="A benchmark study on large language model evaluation with retrieval augmentation.",
            ),
            _paper(
                provider="dblp",
                provider_id="conf/neurips/final-version",
                title="Retrieval-augmented evaluation for large language models",
                year=2025,
                venue="NeurIPS",
                doi=matched_doi,
                abstract="A benchmark study on large language model evaluation with retrieval augmentation.",
            ),
        ]
        papers.extend(
            [
                _paper(
                    provider="crossref",
                    provider_id=f"paper-{idx}",
                    title=f"Verified study {idx}",
                    year=2024,
                    venue="Journal of Evaluation Science",
                    doi=f"10.6000/{idx}",
                    abstract="A verified study with sufficient metadata for APA export.",
                )
                for idx in range(30)
            ]
        )

        class RollingAdapter:
            name = "mixed"

            def __init__(self, rows: list[PaperRecord]) -> None:
                self._rows = rows
                self._offset = 0

            async def search(self, query: str, *, project_id: str, limit: int) -> list[PaperRecord]:
                start = self._offset
                end = min(start + limit, len(self._rows))
                self._offset = end
                batch = self._rows[start:end]
                return [
                    paper.model_copy(
                        update={
                            "project_id": project_id,
                            "paper_id": f"{project_id}:{paper.paper_id}:{idx}",
                        }
                    )
                    for idx, paper in enumerate(batch, start=start)
                ]

        service = AcademicResearchService(repo, adapters=[RollingAdapter(papers)])
        project = await service.create_project(thread_id="thread-refs", topic="retrieval augmented generation evaluation")
        ingested = await service.ingest_project(project.project_id, max_candidates=120, core_paper_limit=20)

        stored = await repo.list_project_papers(project.project_id)
        canonical = next(paper for paper in stored if paper.canonical_id == f"doi:{matched_doi}")
        assert canonical.provider == "dblp"
        assert canonical.is_preprint is False

        result = await service.synthesize_project(project.project_id, output_dir=tmp_path / "outputs", include_graph=False)
        included = [entry for entry in result.references if entry.included_in_final]

        assert len(ingested.selected_papers) <= 20
        assert len(included) >= 30
        assert all("arxiv.org" not in entry.formatted_text.lower() for entry in included if "Retrieval-augmented evaluation" in entry.formatted_text)

        await db.close()

    asyncio.run(scenario())
