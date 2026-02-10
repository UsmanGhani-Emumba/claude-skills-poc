# Tool-Based Parallel Research Reference

This document provides detailed examples and templates for implementing tool-based parallel research using the instrumented Python agent.

## Tool-Based Structure (Dynamic)

```
Main Topic: "WebdriverIO vs Playwright"
│
├── Sub-topic 1: "Project Setup"
│   ├── web_fetch agent (docs URLs are known)
│   └── web_search agent (need tutorial articles)
│   = 2 agents
│
├── Sub-topic 2: "Community & Adoption"
│   ├── web_search agent (need survey data, articles)
│   └── github_cli agent (gh CLI for GitHub stars, issues)
│   = 2 agents
│
├── Sub-topic 3: "Performance Benchmarks"
│   └── web_search agent (only articles available)
│   = 1 agent
│
└── Sub-topic 4: "Test Syntax"
    ├── web_fetch agent (API docs URLs known)
    ├── web_search agent (need examples)
    └── github_cli agent (gh CLI for code examples in repos)
    = 3 agents

Total: 2 + 2 + 1 + 3 = 8 agents (varies by sub-topic needs)
```

## Implementation

### Step 1: Identify sub-topics AND determine tools per sub-topic

```
Sub-topics for "WebdriverIO vs Playwright":

1. Project Setup & Configuration
   - web_fetch: ✅ (docs URLs known)
   - web_search: ✅ (need tutorials)
   - github_cli: ❌ (not needed)
   → 2 agents

2. Test Syntax & API
   - web_fetch: ✅ (API docs URLs known)
   - web_search: ✅ (need examples)
   - github_cli: ❌ (not needed)
   → 2 agents

3. Locator Strategies
   - web_fetch: ✅ (docs URLs known)
   - web_search: ✅ (need best practices)
   - github_cli: ❌ (not needed)
   → 2 agents

4. Community & Ecosystem
   - web_fetch: ❌ (no specific docs)
   - web_search: ✅ (need surveys, articles)
   - github_cli: ✅ (need GitHub stats)
   → 2 agents

5. CI/CD Integration
   - web_fetch: ✅ (CI docs URLs known)
   - web_search: ✅ (need pipeline examples)
   - github_cli: ❌ (not needed)
   → 2 agents

Total: 10 agents
```

### Step 2: Write task prompt files

Create a task file for each agent using the Write tool:

#### web_fetch task prompt template

**File:** `.claude/logs/tasks/<agent-id>.txt`

```
Research "[SUB_TOPIC]" for [MAIN_TOPIC] by fetching official documentation.

Fetch these URLs and extract key information:
1. [URL_1] - Extract [what to look for]
2. [URL_2] - Extract [what to look for]

For each URL, extract:
- Key information relevant to [SUB_TOPIC]
- Code examples
- Configuration options

Return findings organized by source with proper citations.

### Sources
- [Page Title](URL)
```

#### web_search task prompt template

**File:** `.claude/logs/tasks/<agent-id>.txt`

```
Research "[SUB_TOPIC]" for [MAIN_TOPIC] by searching the web.

Perform these searches:
1. "[search query 1]"
2. "[search query 2]"
3. "[search query 3]"

For each search, extract:
- Key insights and recommendations
- Pros/cons mentioned
- Community preferences

Return findings with proper source citations.

### Sources
- [Article Title](URL)
```

#### github_cli task prompt template

**File:** `.claude/logs/tasks/<agent-id>.txt`

```
Research "[SUB_TOPIC]" for [MAIN_TOPIC] using GitHub data.

Run these gh CLI commands:
1. gh api repos/[owner]/[repo] --jq '.stargazers_count, .forks_count'
2. gh api repos/[owner]/[repo]/issues --jq 'length'

Extract:
- Repository statistics
- Activity metrics
- Community engagement data

Return findings with repository references.

### Sources
- [Repo Name](GitHub URL)
```

### Step 3: Spawn agents based on tools needed per sub-topic

Launch all agents in a SINGLE message using multiple Bash calls:

```
// Sub-topic 1: Project Setup (web_fetch + web_search)
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/1a.txt --tools web_fetch  --agent-id 1a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/1b.txt --tools web_search --agent-id 1b --skill researcher

// Sub-topic 2: Test Syntax (web_fetch + web_search)
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/2a.txt --tools web_fetch  --agent-id 2a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/2b.txt --tools web_search --agent-id 2b --skill researcher

// Sub-topic 3: Locators (web_fetch + web_search)
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/3a.txt --tools web_fetch  --agent-id 3a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/3b.txt --tools web_search --agent-id 3b --skill researcher

// Sub-topic 4: Community (web_search + github_cli)
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/4a.txt --tools web_search --agent-id 4a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/4b.txt --tools github_cli --agent-id 4b --skill researcher

// Sub-topic 5: CI/CD (web_fetch + web_search)
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/5a.txt --tools web_fetch  --agent-id 5a --skill researcher
Bash: python scripts/arize_agent.py --task-file .claude/logs/tasks/5b.txt --tools web_search --agent-id 5b --skill researcher
```

## JSON Output Structure

Each agent returns JSON to stdout:

```json
{
  "result": "## Project Setup\n\n### Key Findings\n- Finding 1...\n\n### Sources\n- [Playwright Docs](https://playwright.dev/...)",
  "metrics": {
    "agent_id": "1a",
    "skill": "researcher",
    "model": "claude-sonnet-4-5-20250929",
    "input_tokens": 3200,
    "output_tokens": 600,
    "cost_usd": 0.0186,
    "latency_seconds": 12.1,
    "distinct_tools_count": 1,
    "tools_used": ["web_fetch"],
    "tool_calls_count": 2,
    "api_calls": 3,
    "context_tokens": 3200,
    "timestamp": "2025-06-15T10:30:00Z"
  }
}
```

## Examples: Dynamic Tool Selection

### Example 1: Technical Comparison (WebdriverIO vs Playwright)

| Sub-topic | web_fetch | web_search | github_cli | Total Agents |
|-----------|----------|-----------|-----------|--------------|
| Project Setup | ✅ | ✅ | ❌ | 2 |
| Test Syntax | ✅ | ✅ | ❌ | 2 |
| Locators | ✅ | ✅ | ❌ | 2 |
| Community | ❌ | ✅ | ✅ | 2 |
| CI/CD | ✅ | ✅ | ❌ | 2 |
| **Total** | | | | **10** |

### Example 2: Trending Topic Research (AI Code Assistants)

| Sub-topic | web_fetch | web_search | github_cli | Total Agents |
|-----------|----------|-----------|-----------|--------------|
| Overview | ❌ | ✅ | ❌ | 1 |
| Market Players | ❌ | ✅ | ❌ | 1 |
| GitHub Copilot | ✅ | ✅ | ✅ | 3 |
| Privacy Concerns | ❌ | ✅ | ❌ | 1 |
| Future Trends | ❌ | ✅ | ❌ | 1 |
| **Total** | | | | **7** |

### Example 3: Single Tool Deep-Dive (Playwright Guide)

| Sub-topic | web_fetch | web_search | github_cli | Total Agents |
|-----------|----------|-----------|-----------|--------------|
| Installation | ✅ | ❌ | ❌ | 1 |
| Test Writing | ✅ | ✅ | ❌ | 2 |
| Debugging | ✅ | ✅ | ❌ | 2 |
| CI Setup | ✅ | ✅ | ❌ | 2 |
| Community Tips | ❌ | ✅ | ✅ | 2 |
| **Total** | | | | **9** |

## Compilation

After all agents complete, merge results per sub-topic:

```markdown
## [Sub-topic Name]

### From Documentation (web_fetch)
- Key point 1
- Key point 2
- Code example...

### From Web Research (web_search)
- Insight 1 (Source: ...)
- Community opinion (Source: ...)

### From GitHub Data (github_cli) [if applicable]
- Stars: X
- Open issues: Y
- Recent activity: Z

### Sources
- [Doc Title](URL)
- [Article Title](URL)
- [Repo Name](GitHub URL)
```

## Metrics Compilation

After compiling research, aggregate all agent metrics into a summary table:

```markdown
## Research Metrics

| Agent | Tool | Input Tokens | Output Tokens | Cost | Latency |
|-------|------|-------------|---------------|------|---------|
| 1a | web_fetch | 3,200 | 600 | $0.0186 | 12.1s |
| 1b | web_search | 2,100 | 450 | $0.0138 | 8.2s |
| 2a | web_fetch | 2,800 | 520 | $0.0162 | 10.5s |
| ... | ... | ... | ... | ... | ... |
| **Total** | | **28,000** | **5,200** | **$0.1620** | **10.2s avg** |

- **Sub-agents spawned:** 10
- **Distinct tools used:** 3 (web_search, web_fetch, github_cli)
```

You can also view historical metrics:
```bash
python scripts/metrics_summary.py --detail
python scripts/metrics_summary.py --skill researcher --last 20
```
