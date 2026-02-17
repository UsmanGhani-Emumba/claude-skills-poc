"""
Skill auto-discovery registry for Gemini.

Scans .gemini/skills/*/SKILL.md to discover skills, then either:
  - Loads a custom Python class from references/ (if a .py file exists)
  - Dynamically creates a BaseSkill subclass (if no custom Python)

Usage:
    registry = SkillRegistry()
    registry.discover()
    skills = registry.load_all(client, model, metrics)
"""

import importlib.util
import re
import sys
from pathlib import Path

from base import BaseSkill


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from SKILL.md content.
    Returns (metadata_dict, body_content).
    """
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    raw_yaml = parts[1].strip()
    metadata = {}
    for line in raw_yaml.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^(\w+)\s*:\s*(.+)$", line)
        if match:
            key = match.group(1)
            value = match.group(2).strip().strip('"').strip("'")
            metadata[key] = value

    return metadata, parts[2].strip()


def _make_simple_skill_class(skill_name: str, fallback: str) -> type:
    """Dynamically create a BaseSkill subclass for skills with no custom Python."""
    return type(
        f"{skill_name.capitalize()}Skill",
        (BaseSkill,),
        {
            "name": skill_name,
            "_fallback_prompt": fallback,
        },
    )


def _find_custom_py(references_dir: Path) -> Path | None:
    """Find a custom skill .py file in references/, ignoring __init__.py."""
    if not references_dir.exists():
        return None
    for py_file in references_dir.glob("*.py"):
        if py_file.name != "__init__.py":
            return py_file
    return None


def _load_custom_skill_class(skill_name: str, py_path: Path) -> type:
    """Load a custom skill class from a Python file via importlib."""
    spec = importlib.util.spec_from_file_location(
        f"skills.{skill_name}", str(py_path),
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, BaseSkill)
            and attr is not BaseSkill
        ):
            return attr

    raise ValueError(f"No BaseSkill subclass found in {py_path}")


class SkillRegistry:
    """Discovers and loads skills from .gemini/skills/*/SKILL.md."""

    def __init__(self, skills_dir: str | Path = None):
        if skills_dir is None:
            skills_dir = Path(".gemini/skills")
        self.skills_dir = Path(skills_dir)
        self._skill_metadata: list[dict] = []

    def discover(self) -> list[dict]:
        """Scan for SKILL.md files and return metadata for each skill."""
        self._skill_metadata = []

        for skill_md in sorted(self.skills_dir.glob("*/SKILL.md")):
            skill_dir = skill_md.parent
            content = skill_md.read_text(encoding="utf-8")
            meta, _ = parse_frontmatter(content)

            name = meta.get("name", skill_dir.name)
            description = meta.get("description", "")
            fallback_prompt = meta.get(
                "fallback_prompt",
                f"You are an expert {name}. {description}",
            )

            # Check for any custom .py in references/ (handles non-standard names like notion_publish.py)
            py_path = _find_custom_py(skill_dir / "references")

            self._skill_metadata.append({
                "name": name,
                "description": description,
                "fallback_prompt": fallback_prompt,
                "has_custom_class": py_path is not None,
                "class_path": py_path,
                "skill_dir": skill_dir,
            })

        return self._skill_metadata

    def get_skill_names(self) -> list[str]:
        """Return list of discovered skill names."""
        return [m["name"] for m in self._skill_metadata]

    def get_skill_descriptions(self) -> dict[str, str]:
        """Return {name: description} for all discovered skills."""
        return {m["name"]: m["description"] for m in self._skill_metadata}

    def load_all(
        self,
        client,
        model: str,
        metrics_collector,
        extra_kwargs: dict[str, dict] = None,
    ) -> dict[str, BaseSkill]:
        """Instantiate all discovered skills.

        Args:
            client: Gemini client
            model: Model name
            metrics_collector: MetricsCollector instance
            extra_kwargs: Optional per-skill extra constructor kwargs
        """
        if not self._skill_metadata:
            self.discover()

        extra_kwargs = extra_kwargs or {}
        skills = {}

        for meta in self._skill_metadata:
            name = meta["name"]

            if meta["has_custom_class"]:
                cls = _load_custom_skill_class(name, meta["class_path"])
            else:
                cls = _make_simple_skill_class(name, meta["fallback_prompt"])

            kwargs = {
                "client": client,
                "model": model,
                "metrics_collector": metrics_collector,
            }
            kwargs.update(extra_kwargs.get(name, {}))
            skills[name] = cls(**kwargs)

        return skills
