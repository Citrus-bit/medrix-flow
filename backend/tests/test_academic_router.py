import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.gateway.routers import academic
from medrix_flow.academic import AcademicRepository, AcademicResearchService
from medrix_flow.academic.types import PaperAuthor, PaperRecord
from medrix_flow.runtime.db import SQLiteRuntimeDB
from medrix_flow.runtime.utils import now_iso


class FakeAdapter:
    name = "openalex"

    async def search(self, query: str, *, project_id: str, limit: int) -> list[PaperRecord]:
        return [
            PaperRecord(
                paper_id=f"{project_id}:paper-1",
                project_id=project_id,
                canonical_id="doi:10.5000/demo",
                title="Structured evidence synthesis for academic agents",
                authors=[PaperAuthor(display_name="Dana Xu", given_name="Dana", family_name="Xu", ordinal=0)],
                year=2025,
                venue="Scholarly Systems",
                abstract="A benchmark study on structured evidence synthesis and report generation.",
                doi="10.5000/demo",
                provider="openalex",
                provider_id="w-openalex-1",
                source_url="https://openalex.org/W1",
                oa_url=None,
                metadata_only=False,
                keywords=["structured", "evidence", "benchmark"],
                methods=["benchmarking"],
                populations=[],
                conflict_flags=[],
                raw_source={"referenced_works": []},
                created_at=now_iso(),
                updated_at=now_iso(),
            )
        ]


def test_academic_router_end_to_end():
    async def make_service():
        db = SQLiteRuntimeDB(":memory:")
        await db.connect()
        repo = AcademicRepository(db)
        await repo.setup()
        service = AcademicResearchService(repo, adapters=[FakeAdapter()])
        return service, db

    service, db = asyncio.run(make_service())
    app = FastAPI()
    app.state.academic_service = service
    app.include_router(academic.router)

    with TestClient(app) as client:
        created = client.post(
            "/api/academic/projects",
            json={"thread_id": "thread-3", "topic": "academic agent evidence synthesis"},
        )
        assert created.status_code == 200
        project_id = created.json()["project"]["project_id"]

        ingested = client.post(
            f"/api/academic/projects/{project_id}/ingest",
            json={"max_candidates": 20, "core_paper_limit": 20, "use_local_uploads": False},
        )
        assert ingested.status_code == 200
        assert ingested.json()["paper_count"] >= 1
        assert ingested.json()["provider_breakdown"]["openalex"] >= 1
        assert "Scholarly Systems" in ingested.json()["venue_breakdown"]
        assert ingested.json()["canonical_reference_count"] >= 1
        assert ingested.json()["preprint_ratio"] == 0.0

        synthesized = client.post(
            f"/api/academic/projects/{project_id}/synthesize",
            json={"include_graph": True, "write_outputs": False},
        )
        assert synthesized.status_code == 200
        assert len(synthesized.json()["references"]) >= 1

        project = client.get(f"/api/academic/projects/{project_id}")
        assert project.status_code == 200
        assert project.json()["project"]["status"] == "synthesized"
        assert project.json()["provider_breakdown"]["openalex"] >= 1
        assert project.json()["canonical_reference_count"] >= 1

        references = client.get(f"/api/academic/projects/{project_id}/references?style=apa7")
        assert references.status_code == 200
        assert references.json()["style"] == "apa7"
        assert len(references.json()["data"]) >= 1

        graph = client.get(f"/api/academic/projects/{project_id}/graph")
        assert graph.status_code == 200
        assert graph.json()["project_id"] == project_id
        assert len(graph.json()["nodes"]) >= 1

    asyncio.run(db.close())
