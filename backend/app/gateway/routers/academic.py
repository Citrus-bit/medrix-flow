from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.gateway.deps import get_academic_service

router = APIRouter(prefix="/api/academic", tags=["academic"])


class AcademicProjectCreateRequest(BaseModel):
    thread_id: str
    topic: str
    scope: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    force_new: bool = False


class AcademicIngestRequest(BaseModel):
    max_candidates: int = Field(default=120, ge=10, le=240)
    core_paper_limit: int = Field(default=24, ge=10, le=40)
    use_local_uploads: bool = True
    source_profile: str | None = None
    quality_mode: str | None = None
    preprint_policy: str | None = None


class AcademicSynthesizeRequest(BaseModel):
    include_graph: bool = False
    write_outputs: bool = True


@router.post("/projects")
async def create_project(body: AcademicProjectCreateRequest, request: Request) -> dict[str, Any]:
    service = get_academic_service(request)
    project = await service.create_project(
        thread_id=body.thread_id,
        topic=body.topic,
        scope=body.scope,
        metadata=body.metadata,
        force_new=body.force_new,
    )
    return {"project": project.model_dump()}


@router.post("/projects/{project_id}/ingest")
async def ingest_project(project_id: str, body: AcademicIngestRequest, request: Request) -> dict[str, Any]:
    service = get_academic_service(request)
    try:
        result = await service.ingest_project(
            project_id,
            max_candidates=body.max_candidates,
            core_paper_limit=body.core_paper_limit,
            use_local_uploads=body.use_local_uploads,
            source_profile=body.source_profile,
            quality_mode=body.quality_mode,
            preprint_policy=body.preprint_policy,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump()


@router.post("/projects/{project_id}/synthesize")
async def synthesize_project(project_id: str, body: AcademicSynthesizeRequest, request: Request) -> dict[str, Any]:
    service = get_academic_service(request)
    try:
        project = await service.get_project_summary(project_id)
        output_dir = None
        if body.write_outputs:
            output_dir = service.thread_outputs_dir(project["project"]["thread_id"])
        result = await service.synthesize_project(
            project_id,
            output_dir=output_dir,
            include_graph=body.include_graph,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump()


@router.get("/projects/{project_id}")
async def get_project(project_id: str, request: Request) -> dict[str, Any]:
    service = get_academic_service(request)
    try:
        return await service.get_project_summary(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/references")
async def get_references(
    project_id: str,
    request: Request,
    style: str = Query(default="apa7"),
) -> dict[str, Any]:
    if style.lower() != "apa7":
        raise HTTPException(status_code=422, detail="Only apa7 is currently supported")
    service = get_academic_service(request)
    try:
        references = await service.get_references(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"style": "apa7", "data": [entry.model_dump() for entry in references]}


@router.get("/projects/{project_id}/graph")
async def get_graph(project_id: str, request: Request) -> dict[str, Any]:
    service = get_academic_service(request)
    try:
        graph = await service.get_graph(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return graph.model_dump()
