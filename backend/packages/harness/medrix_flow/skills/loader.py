import os
from pathlib import Path

from .parser import parse_skill_file
from .types import Skill


def get_skills_root_path() -> Path:
    """
    Get the root path of the skills directory.

    Returns:
        Path to the skills directory (medrix-flow/skills)
    """
    # loader.py lives at packages/harness/medrix_flow/skills/loader.py — 5 parents up reaches backend/
    backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    # skills directory is sibling to backend directory
    skills_dir = backend_dir.parent / "skills"
    return skills_dir


class _SkillsCache:
    """Mtime-based cache: skip filesystem walk when nothing changed."""

    def __init__(self) -> None:
        self._mtime_snapshot: dict[str, float] = {}
        self._cached_skills: list[Skill] = []

    def _collect_mtimes(self, skills_path: Path) -> dict[str, float]:
        mtimes: dict[str, float] = {}
        for category in ["public", "custom"]:
            category_path = skills_path / category
            if not category_path.exists():
                continue
            try:
                mtimes[str(category_path)] = category_path.stat().st_mtime
            except OSError:
                continue
            for current_root, dir_names, file_names in os.walk(category_path):
                dir_names[:] = sorted(name for name in dir_names if not name.startswith("."))
                if "SKILL.md" in file_names:
                    p = os.path.join(current_root, "SKILL.md")
                    try:
                        mtimes[p] = os.stat(p).st_mtime
                    except OSError:
                        continue
        ext_path = self._extensions_config_path()
        if ext_path and ext_path.exists():
            try:
                mtimes[str(ext_path)] = ext_path.stat().st_mtime
            except OSError:
                pass
        return mtimes

    @staticmethod
    def _extensions_config_path() -> Path | None:
        from medrix_flow.config.extensions_config import ExtensionsConfig

        return ExtensionsConfig.resolve_config_path()

    def get(self, skills_path: Path) -> list[Skill] | None:
        mtimes = self._collect_mtimes(skills_path)
        if mtimes == self._mtime_snapshot and self._cached_skills:
            return self._cached_skills
        return None

    def put(self, skills_path: Path, skills: list[Skill]) -> None:
        self._mtime_snapshot = self._collect_mtimes(skills_path)
        self._cached_skills = skills

    def invalidate(self) -> None:
        self._mtime_snapshot = {}
        self._cached_skills = []


_skills_cache = _SkillsCache()


def invalidate_skills_cache() -> None:
    _skills_cache.invalidate()


def load_skills(skills_path: Path | None = None, use_config: bool = True, enabled_only: bool = False) -> list[Skill]:
    """
    Load all skills from the skills directory.

    Scans both public and custom skill directories, parsing SKILL.md files
    to extract metadata. The enabled state is determined by the skills_state_config.json file.

    Args:
        skills_path: Optional custom path to skills directory.
                     If not provided and use_config is True, uses path from config.
                     Otherwise defaults to medrix-flow/skills
        use_config: Whether to load skills path from config (default: True)
        enabled_only: If True, only return enabled skills (default: False)

    Returns:
        List of Skill objects, sorted by name
    """
    if skills_path is None:
        if use_config:
            try:
                from medrix_flow.config import get_app_config

                config = get_app_config()
                skills_path = config.skills.get_skills_path()
            except Exception:
                # Fallback to default if config fails
                skills_path = get_skills_root_path()
        else:
            skills_path = get_skills_root_path()

    if not skills_path.exists():
        return []

    cached = _skills_cache.get(skills_path)
    if cached is not None:
        if enabled_only:
            return [skill for skill in cached if skill.enabled]
        return list(cached)

    skills = []

    # Scan public and custom directories
    for category in ["public", "custom"]:
        category_path = skills_path / category
        if not category_path.exists() or not category_path.is_dir():
            continue

        for current_root, dir_names, file_names in os.walk(category_path):
            # Keep traversal deterministic and skip hidden directories.
            dir_names[:] = sorted(name for name in dir_names if not name.startswith("."))
            if "SKILL.md" not in file_names:
                continue

            skill_file = Path(current_root) / "SKILL.md"
            relative_path = skill_file.parent.relative_to(category_path)

            skill = parse_skill_file(skill_file, category=category, relative_path=relative_path)
            if skill:
                skills.append(skill)

    # Load skills state configuration and update enabled status
    # NOTE: We use ExtensionsConfig.from_file() instead of get_extensions_config()
    # to always read the latest configuration from disk. This ensures that changes
    # made through the Gateway API (which runs in a separate process) are immediately
    # reflected in the LangGraph Server when loading skills.
    try:
        from medrix_flow.config.extensions_config import ExtensionsConfig

        extensions_config = ExtensionsConfig.from_file()
        for skill in skills:
            skill.enabled = extensions_config.is_skill_enabled(skill.name, skill.category)
    except Exception as e:
        # If config loading fails, default to all enabled
        print(f"Warning: Failed to load extensions config: {e}")

    # Sort by name for consistent ordering
    skills.sort(key=lambda s: s.name)

    _skills_cache.put(skills_path, skills)

    # Filter by enabled status if requested
    if enabled_only:
        return [skill for skill in skills if skill.enabled]

    return list(skills)
