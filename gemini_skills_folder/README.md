# Gemini Skill Orchestrator

A content pipeline that chains four skills — Researcher, Writer, Reviewer, Publisher — to produce and publish blog posts to Notion, powered by Gemini 2.0 Flash.

## Pipeline

```
User Prompt → Intent Detection → Skill Routing
                                      │
        ┌─────────────┬───────────────┼───────────────┬──────────────┐
        ▼             ▼               ▼               ▼              ▼
   Researcher      Writer         Reviewer        Publisher     Full Pipeline
   (research)     (draft)         (review)       (Notion)      (all skills)
```

**Full Pipeline:**
```
Researcher → Writer → Reviewer → Writer (revision if needed) → Publisher (Notion)
```

## Skills

| Skill | Purpose | Trigger Keywords |
|-------|---------|-----------------|
| **Researcher** | Gathers facts, statistics, multiple perspectives | "research", "find info", "investigate" |
| **Writer** | Produces polished articles, handles revisions. Format enforced via [sample_output.md](.gemini/skills/writer/references/sample_output.md) | "write", "draft", "compose" |
| **Reviewer** | Evaluates quality using [review_checklist.md](.gemini/skills/reviewer/references/review_checklist.md), returns APPROVED/NEEDS_REVISION | "review", "edit", "feedback" |
| **Publisher** | Formats and publishes to Notion | "publish", "post to Notion" |

## Project Structure

```
.gemini/
  commands/                          # Slash commands (/research, /write, /review, /publish, /pipeline)
  skills/
    base.py                          # Shared base skill class
    registry.py                      # Skill registry
    researcher/
      SKILL.md                       # Skill prompt definition
    writer/
      SKILL.md
      references/
        sample_output.md             # Blog format reference
    reviewer/
      SKILL.md
      references/
        review_checklist.md          # Quality + AI-detection checklist
        notion_best_practices.md     # Notion formatting guidelines
    publisher/
      SKILL.md
      references/
        notion_publish.py            # Notion publishing implementation
        notion_api_specs.md          # Notion API reference
src/
  config.py                          # Environment configuration
  agents/
    base.py                          # Base agent class
  orchestrator/
    agent.py                         # Core orchestrator logic
    intent.py                        # Intent classification
    pipeline.py                      # Full pipeline execution
  observability/
    tracer.py                        # Arize Phoenix setup
    metrics.py                       # Token/cost/latency tracking
main.py                              # CLI entry point
```

## Setup

### 1. Create and activate a virtual environment

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_google_gemini_api_key
NOTION_API_KEY=your_notion_integration_token
NOTION_PARENT_ID=your_notion_parent_page_id
ARIZE_SPACE_KEY=your_arize_space_key    # optional
ARIZE_API_KEY=your_arize_api_key        # optional
```

## Running

```powershell
python main.py
```

This starts an interactive session. Type your prompt and press Enter. Type `exit`, `quit`, or `q` to stop.

## Observability

Arize Phoenix launches automatically on startup. Open `http://localhost:6006` to view real-time traces, latency, token counts, and cost metrics for each skill execution.

## Usage Examples

```
You: Write and publish a blog post about the impact of Generative AI on software testing on Notion.
You: Just research current trends in climate tech for 2026.
You: Review this draft and tell me what needs fixing: [paste content]
```
