# How to Run

## Prerequisites

- Python 3.11 installed (check: `py -3.11 --version`)
- An Anthropic API key
- (Optional) Notion API key and database ID for publishing

## Setup

### 1. Create the virtual environment

```bash
py -3.11 -m venv .venv
```

### 2. Activate the virtual environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**Git Bash / WSL:**
```bash
source .venv/Scripts/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```
ANTHROPIC_API_KEY=sk-ant-...        # Required
NOTION_API_KEY=ntn_...              # Optional (for publishing)
NOTION_DATABASE_ID=abc123...        # Optional (for publishing)
```

## Running

### Interactive mode

```bash
python -m src.main
```

You'll get a prompt where you can type requests:

```
Orchestrator Agent (type 'quit' to exit)

You: Write an article about quantum computing
```

### Using slash commands (in Claude Code)

```
/research latest trends in AI agents
/write a blog post about sustainable energy
/review <paste content>
/publish <paste content>
/pipeline Write an article about the future of remote work
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Viewing Traces (Arize Phoenix)

The agent auto-launches Phoenix when it starts. Open the dashboard at:

```
http://localhost:6006
```

You'll see traces for every skill invocation with token counts, latency, and cost breakdowns.

## Troubleshooting

| Issue | Solution |
|-------|---------|
| `ModuleNotFoundError` | Make sure the venv is activated |
| `ANTHROPIC_API_KEY not set` | Check your `.env` file |
| Phoenix not loading | Ensure port 6006 is free, or set `PHOENIX_COLLECTOR_ENDPOINT` in `.env` |
| Notion publish fails | Verify `NOTION_API_KEY` and `NOTION_DATABASE_ID` in `.env` |
