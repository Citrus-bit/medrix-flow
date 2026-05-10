import re
from pathlib import Path

import yaml

from .types import Skill


def parse_skill_file(skill_file: Path, category: str, relative_path: Path | None = None) -> Skill | None:
    """
    Parse a SKILL.md file and extract metadata.

    Args:
        skill_file: Path to the SKILL.md file
        category: Category of the skill ('public' or 'custom')

    Returns:
        Skill object if parsing succeeds, None otherwise
    """
    if not skill_file.exists() or skill_file.name != "SKILL.md":
        return None

    try:
        content = skill_file.read_text(encoding="utf-8")

        # Extract YAML front matter
        # Pattern: ---\nkey: value\n---
        front_matter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)

        if not front_matter_match:
            return None

        front_matter = front_matter_match.group(1)

        metadata = yaml.safe_load(front_matter) or {}
        if not isinstance(metadata, dict):
            return None

        # Extract required fields
        name = str(metadata.get("name", "")).strip()
        description = str(metadata.get("description", "")).strip()

        if not name or not description:
            return None

        license_value = metadata.get("license")
        license_text = str(license_value).strip() if license_value else None

        return Skill(
            name=name,
            description=description,
            license=license_text,
            skill_dir=skill_file.parent,
            skill_file=skill_file,
            relative_path=relative_path or Path(skill_file.parent.name),
            category=category,
            enabled=True,  # Default to enabled, actual state comes from config file
        )

    except Exception as e:
        print(f"Error parsing skill file {skill_file}: {e}")
        return None
