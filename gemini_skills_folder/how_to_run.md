# How to Run the Gemini Skill Orchestrator

A content pipeline that chains four skills — Researcher, Writer, Reviewer, Publisher — to produce and publish blog posts to Notion.

## Prerequisites

- Python 3.11+ (required for Arize Phoenix compatibility)
- A Google Gemini API key
- A Notion integration token and parent page ID

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

Arize Phoenix launches automatically on startup. Open `http://localhost:6006` to view real-time traces, latency, and token metrics for each skill execution.

## Project Structure

```
.gemini/
  skills/           # Skill definitions (SKILL.md + references/)
    researcher/
    writer/
    reviewer/
    publisher/
  commands/          # Gemini CLI slash commands
src/
  orchestrator/      # Agent, intent resolver, pipeline
  observability/     # Phoenix tracer and metrics
  config.py          # Environment config and validation
main.py              # Entry point
```

## Usage Examples

```
You: Write and publish a blog post about the impact of Generative AI on software testing on Notion.
You: Just research current trends in climate tech for 2026.
You: Review this draft and tell me what needs fixing: [paste content]
```
