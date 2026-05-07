import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.gateway.auth import require_admin_access
from app.gateway.path_utils import resolve_thread_virtual_path
from medrix_flow.skills import Skill, SkillCategory
from medrix_flow.skills.installer import SkillAlreadyExistsError, resolve_skill_dir_from_archive, safe_extract_skill_archive
from medrix_flow.skills.service import SkillService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["skills"])


class SkillResponse(BaseModel):
    """Response model for skill information."""

    name: str = Field(..., description="Name of the skill")
    description: str = Field(..., description="Description of what the skill does")
    license: str | None = Field(None, description="License information")
    category: SkillCategory | str = Field(..., description="Category of the skill (public or custom)")
    enabled: bool = Field(default=True, description="Whether this skill is enabled")


class SkillsListResponse(BaseModel):
    """Response model for listing all skills."""

    skills: list[SkillResponse]


class SkillUpdateRequest(BaseModel):
    """Request model for updating a skill."""

    enabled: bool = Field(..., description="Whether to enable or disable the skill")


class SkillInstallRequest(BaseModel):
    """Request model for installing a skill from a .skill file."""

    thread_id: str = Field(..., description="The thread ID where the .skill file is located")
    path: str = Field(..., description="Virtual path to the .skill file (e.g., mnt/user-data/outputs/my-skill.skill)")


class SkillInstallResponse(BaseModel):
    """Response model for skill installation."""

    success: bool = Field(..., description="Whether the installation was successful")
    skill_name: str = Field(..., description="Name of the installed skill")
    message: str = Field(..., description="Installation result message")


class CustomSkillContentResponse(SkillResponse):
    content: str = Field(..., description="Raw SKILL.md content")


class CustomSkillUpdateRequest(BaseModel):
    content: str = Field(..., description="Replacement SKILL.md content")


class CustomSkillHistoryResponse(BaseModel):
    history: list[dict]


class SkillRollbackRequest(BaseModel):
    history_index: int = Field(default=-1, description="History entry index to restore from, defaulting to the latest change.")


def _skill_to_response(skill: Skill) -> SkillResponse:
    return SkillResponse(
        name=skill.name,
        description=skill.description,
        license=skill.license,
        category=skill.category,
        enabled=skill.enabled,
    )


def _service() -> SkillService:
    return SkillService()


def _sanitize_skill_name(skill_name: str) -> str:
    return skill_name.replace("\r\n", "").replace("\n", "")


def _resolve_skill_dir_from_archive_root(temp_path: Path) -> Path:
    try:
        return resolve_skill_dir_from_archive(temp_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _safe_extract_skill_archive(*args, **kwargs) -> None:
    try:
        safe_extract_skill_archive(*args, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/skills",
    response_model=SkillsListResponse,
    summary="List All Skills",
    description="Retrieve a list of all available skills from both public and custom directories.",
)
async def list_skills() -> SkillsListResponse:
    try:
        skills = _service().list_skills(enabled_only=False)
        return SkillsListResponse(skills=[_skill_to_response(skill) for skill in skills])
    except Exception as exc:
        logger.error("Failed to load skills: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load skills: {str(exc)}")


@router.post(
    "/skills/install",
    dependencies=[Depends(require_admin_access)],
    response_model=SkillInstallResponse,
    summary="Install Skill",
    description="Install a skill from a .skill file (ZIP archive) located in the thread's user-data directory.",
)
async def install_skill(request: SkillInstallRequest) -> SkillInstallResponse:
    try:
        skill_file_path = resolve_thread_virtual_path(request.thread_id, request.path)
        result = _service().install_skill_from_archive(skill_file_path)
        return SkillInstallResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except SkillAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to install skill: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to install skill: {str(exc)}")


@router.get("/skills/custom", response_model=SkillsListResponse, summary="List Custom Skills")
async def list_custom_skills() -> SkillsListResponse:
    try:
        skills = _service().list_custom_skills()
        return SkillsListResponse(skills=[_skill_to_response(skill) for skill in skills])
    except Exception as exc:
        logger.error("Failed to list custom skills: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list custom skills: {str(exc)}")


@router.get("/skills/custom/{skill_name}", response_model=CustomSkillContentResponse, summary="Get Custom Skill Content")
async def get_custom_skill(skill_name: str) -> CustomSkillContentResponse:
    try:
        skill, content = _service().get_custom_skill(_sanitize_skill_name(skill_name))
        return CustomSkillContentResponse(**_skill_to_response(skill).model_dump(), content=content)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to get custom skill %s: %s", skill_name, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get custom skill: {str(exc)}")


@router.put("/skills/custom/{skill_name}", dependencies=[Depends(require_admin_access)], response_model=CustomSkillContentResponse, summary="Edit Custom Skill")
async def update_custom_skill(skill_name: str, request: CustomSkillUpdateRequest) -> CustomSkillContentResponse:
    try:
        skill, content = _service().update_custom_skill(_sanitize_skill_name(skill_name), request.content)
        return CustomSkillContentResponse(**_skill_to_response(skill).model_dump(), content=content)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to update custom skill %s: %s", skill_name, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update custom skill: {str(exc)}")


@router.delete("/skills/custom/{skill_name}", dependencies=[Depends(require_admin_access)], summary="Delete Custom Skill")
async def delete_custom_skill(skill_name: str) -> dict[str, bool]:
    try:
        _service().delete_custom_skill(_sanitize_skill_name(skill_name))
        return {"success": True}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to delete custom skill %s: %s", skill_name, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete custom skill: {str(exc)}")


@router.get("/skills/custom/{skill_name}/history", response_model=CustomSkillHistoryResponse, summary="Get Custom Skill History")
async def get_custom_skill_history(skill_name: str) -> CustomSkillHistoryResponse:
    try:
        history = _service().get_custom_skill_history(_sanitize_skill_name(skill_name))
        return CustomSkillHistoryResponse(history=history)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to read history for %s: %s", skill_name, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to read history: {str(exc)}")


@router.post("/skills/custom/{skill_name}/rollback", dependencies=[Depends(require_admin_access)], response_model=CustomSkillContentResponse, summary="Rollback Custom Skill")
async def rollback_custom_skill(skill_name: str, request: SkillRollbackRequest) -> CustomSkillContentResponse:
    try:
        skill, content = _service().rollback_custom_skill(
            _sanitize_skill_name(skill_name),
            history_index=request.history_index,
        )
        return CustomSkillContentResponse(**_skill_to_response(skill).model_dump(), content=content)
    except IndexError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to roll back custom skill %s: %s", skill_name, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to roll back custom skill: {str(exc)}")


@router.get(
    "/skills/{skill_name}",
    response_model=SkillResponse,
    summary="Get Skill Details",
    description="Retrieve detailed information about a specific skill by its name.",
)
async def get_skill(skill_name: str) -> SkillResponse:
    try:
        skill = _service().get_skill(_sanitize_skill_name(skill_name))
        return _skill_to_response(skill)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to get skill %s: %s", skill_name, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get skill: {str(exc)}")


@router.put(
    "/skills/{skill_name}",
    dependencies=[Depends(require_admin_access)],
    response_model=SkillResponse,
    summary="Update Skill",
    description="Update a skill's enabled status by modifying the extensions_config.json file.",
)
async def update_skill(skill_name: str, request: SkillUpdateRequest) -> SkillResponse:
    try:
        skill = _service().update_skill_enabled(_sanitize_skill_name(skill_name), enabled=request.enabled)
        return _skill_to_response(skill)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to update skill %s: %s", skill_name, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update skill: {str(exc)}")
