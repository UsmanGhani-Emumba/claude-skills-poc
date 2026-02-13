# Orchestrator Agent

Content pipeline agent: Researcher → Writer → Reviewer → Publisher (Notion).

## Stack
- Python 3.11+, Anthropic SDK, Claude Opus 4.6 (`claude-opus-4-6`)
- Arize Phoenix for observability (http://localhost:6006)
- MCP for Notion publishing
- Rich for CLI output

## Project Structure
- `.claude/skills/` — Individual pipeline skills (SKILL.md + Python implementation co-located)
- `.claude/skills/base.py` — Base skill class used by all skills
- `.claude/agents/orchestrator.md` — Orchestrator subagent definition
- `src/` — Python implementation (orchestrator, observability, MCP)
- Entry point: `.venv/Scripts/python -m src.main`

## Commands
- `.venv/Scripts/pip install -r requirements.txt` to install deps
- `.venv/Scripts/python -m src.main` for interactive mode
- `.venv/Scripts/python -m src.main "your prompt"` for single-shot
- `.venv/Scripts/python -m pytest tests/` to run tests

## Key Conventions
- Always initialize Arize Phoenix BEFORE creating the Anthropic client
- Every Anthropic API call must be traced
- Use `rich` for CLI output, no print()
- All env vars loaded via python-dotenv from .env
