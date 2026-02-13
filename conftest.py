import sys
from pathlib import Path

# Ensure .claude/skills is on sys.path for test imports
_skills_dir = str(Path(__file__).resolve().parent / ".claude" / "skills")
if _skills_dir not in sys.path:
    sys.path.insert(0, _skills_dir)
