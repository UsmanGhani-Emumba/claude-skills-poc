import sys
from pathlib import Path

# Add .claude/skills to sys.path so skill modules are importable
# (e.g., `from researcher.researcher import ResearcherSkill`)
_skills_dir = str(Path(__file__).resolve().parent.parent / ".claude" / "skills")
if _skills_dir not in sys.path:
    sys.path.insert(0, _skills_dir)
