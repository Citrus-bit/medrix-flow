from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.gateway.deps import get_experiment_service

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


class ExperimentProjectCreateRequest(BaseModel):
    thread_id: str
    agent_name: str
    domain: str
    topic: str
    dataset_ids: list[str] = Field(default_factory=list)
    linked_academic_project_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentExecuteRequest(BaseModel):
    analysis_type: str | None = None
    target_column: str | None = None
    metadata_path: str | None = None
    sample_id_column: str | None = None
    group_column: str | None = None
    publication_grade: str = "paper"
    write_outputs: bool = True


class ExperimentExportRequest(BaseModel):
    include_paper_ready: bool = True


@router.post("/projects")
async def create_project(body: ExperimentProjectCreateRequest, request: Request) -> dict[str, Any]:
    service = get_experiment_service(request)
    project = await service.create_project(
        thread_id=body.thread_id,
        agent_name=body.agent_name,
        domain=body.domain,
        topic=body.topic,
        dataset_ids=body.dataset_ids,
        linked_academic_project_id=body.linked_academic_project_id,
        metadata=body.metadata,
    )
    return {"project": project.model_dump()}


@router.post("/projects/{project_id}/execute")
async def execute_project(project_id: str, body: ExperimentExecuteRequest, request: Request) -> dict[str, Any]:
    service = get_experiment_service(request)
    try:
        summary = await service.get_project_summary(project_id)
        output_dir = service.thread_outputs_dir(summary.project.thread_id)
        result = await service.execute_project(
            project_id,
            output_dir=output_dir,
            analysis_type=body.analysis_type,
            target_column=body.target_column,
            metadata_path=body.metadata_path,
            sample_id_column=body.sample_id_column,
            group_column=body.group_column,
            publication_grade=body.publication_grade,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result.model_dump()


@router.post("/projects/{project_id}/export")
async def export_project(project_id: str, body: ExperimentExportRequest, request: Request) -> dict[str, Any]:
    del body
    service = get_experiment_service(request)
    try:
        bundle = await service.export_project(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return bundle.model_dump()


@router.get("/projects/{project_id}")
async def get_project(project_id: str, request: Request) -> dict[str, Any]:
    service = get_experiment_service(request)
    try:
        summary = await service.get_project_summary(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return summary.model_dump()


@router.get("/projects/{project_id}/artifacts")
async def get_project_artifacts(project_id: str, request: Request) -> dict[str, Any]:
    service = get_experiment_service(request)
    try:
        artifacts = await service.list_project_artifacts(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"data": [item.model_dump() for item in artifacts]}
