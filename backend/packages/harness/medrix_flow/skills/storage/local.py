"""Local filesystem-backed skill storage."""

from __future__ import annotations

import errno
import json
import shutil
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from medrix_flow.config import get_app_config
from medrix_flow.skills.installer import (
    SkillAlreadyExistsError,
    move_staged_skill_into_reserved_target,
    resolve_skill_dir_from_archive,
    safe_extract_skill_archive,
    scan_skill_archive_contents_or_raise,
)
from medrix_flow.skills.loader import invalidate_skills_cache
from medrix_flow.skills.storage.base import SkillStorage


class LocalSkillStorage(SkillStorage):
    def __init__(
        self,
        host_path: str | Path | None = None,
        container_path: str | None = None,
    ) -> None:
        config = get_app_config() if host_path is None or container_path is None else None
        super().__init__(container_path=container_path or config.skills.container_path)
        base_path = Path(host_path) if host_path is not None else config.skills.get_skills_path()
        self._host_root = base_path.resolve()

    def get_skills_root_path(self) -> Path:
        return self._host_root

    def load_skills(self, *, enabled_only: bool = False) -> list:
        from medrix_flow.skills.loader import load_skills

        return load_skills(
            skills_path=self._host_root,
            use_config=False,
            enabled_only=enabled_only,
        )

    def custom_skill_exists(self, name: str) -> bool:
        return self.get_custom_skill_file(name).exists()

    def public_skill_exists(self, name: str) -> bool:
        normalized_name = self.validate_skill_name(name)
        return (self._host_root / "public" / normalized_name / "SKILL.md").exists()

    def read_custom_skill(self, name: str) -> str:
        if not self.custom_skill_exists(name):
            raise FileNotFoundError(f"Custom skill '{name}' not found.")
        return self.get_custom_skill_file(name).read_text(encoding="utf-8")

    def write_custom_skill(self, name: str, relative_path: str, content: str) -> None:
        target = self.validate_relative_path(relative_path, self.get_custom_skill_dir(name))
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=str(target.parent)) as tmp_file:
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
        tmp_path.replace(target)
        invalidate_skills_cache()

    def install_skill_from_archive(self, archive_path: str | Path) -> dict:
        from medrix_flow.skills.validation import _validate_skill_frontmatter

        path = Path(archive_path)
        if not path.is_file():
            if not path.exists():
                raise FileNotFoundError(f"Skill file not found: {archive_path}")
            raise ValueError(f"Path is not a file: {archive_path}")
        if path.suffix != ".skill":
            raise ValueError("File must have .skill extension")

        custom_dir = self._host_root / "custom"
        custom_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            try:
                zf = zipfile.ZipFile(path, "r")
            except FileNotFoundError:
                raise FileNotFoundError(f"Skill file not found: {archive_path}") from None
            except (zipfile.BadZipFile, IsADirectoryError):
                raise ValueError("File is not a valid ZIP archive") from None

            with zf:
                safe_extract_skill_archive(zf, tmp_path)

            skill_dir = resolve_skill_dir_from_archive(tmp_path)
            is_valid, message, skill_name = _validate_skill_frontmatter(skill_dir)
            if not is_valid:
                raise ValueError(f"Invalid skill: {message}")
            if not skill_name:
                raise ValueError("Could not determine skill name")
            skill_name = self.validate_skill_name(skill_name)

            target = custom_dir / skill_name
            if target.exists():
                raise SkillAlreadyExistsError(f"Skill '{skill_name}' already exists")

            scan_skill_archive_contents_or_raise(skill_dir, skill_name)

            with tempfile.TemporaryDirectory(prefix=f".installing-{skill_name}-", dir=custom_dir) as staging_root:
                staging_target = Path(staging_root) / skill_name
                shutil.copytree(skill_dir, staging_target)
                move_staged_skill_into_reserved_target(staging_target, target)

        invalidate_skills_cache()
        return {
            "success": True,
            "skill_name": skill_name,
            "message": f"Skill '{skill_name}' installed successfully",
        }

    def delete_custom_skill(self, name: str, *, history_meta: dict | None = None) -> None:
        self.validate_skill_name(name)
        self.ensure_custom_skill_is_editable(name)
        target = self.get_custom_skill_dir(name)
        if history_meta is not None:
            prev_content = self.read_custom_skill(name)
            try:
                self.append_history(name, {**history_meta, "prev_content": prev_content})
            except OSError as exc:
                if not isinstance(exc, PermissionError) and exc.errno not in {errno.EACCES, errno.EPERM, errno.EROFS}:
                    raise
        if target.exists():
            shutil.rmtree(target)
        invalidate_skills_cache()

    def append_history(self, name: str, record: dict) -> None:
        self.validate_skill_name(name)
        payload = {"ts": datetime.now(UTC).isoformat(), **record}
        history_path = self.get_skill_history_file(name)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False))
            file.write("\n")

    def read_history(self, name: str) -> list[dict]:
        self.validate_skill_name(name)
        history_path = self.get_skill_history_file(name)
        if not history_path.exists():
            return []
        records: list[dict] = []
        for line in history_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            records.append(json.loads(line))
        return records
