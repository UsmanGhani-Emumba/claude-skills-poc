# Tool-Based Parallel Research Reference

This document provides detailed examples and templates for implementing tool-based parallel research.

## Tool-Based Structure (Dynamic)

```
Main Topic: "WebdriverIO vs Playwright"
│
├── Sub-topic 1: "Project Setup"
│   ├── WebFetch Agent (docs URLs are known)
│   └── WebSearch Agent (need tutorial articles)
│   = 2 agents
│
├── Sub-topic 2: "Community & Adoption"
│   ├── WebSearch Agent (need survey data, articles)
│   └── Bash Agent (gh CLI for GitHub stars, issues)
│   = 2 agents
│
├── Sub-topic 3: "Performance Benchmarks"
│   └── WebSearch Agent (only articles available)
│   = 1 agent
│
└── Sub-topic 4: "Test Syntax"
    ├── WebFetch Agent (API docs URLs known)
    ├── WebSearch Agent (need examples)
    └── Bash Agent (gh CLI for code examples in repos)
    = 3 agents

Total: 2 + 2 + 1 + 3 = 8 agents (varies by sub-topic needs)
```

## Implementation

### Step 1: Identify sub-topics AND determine tools per sub-topic

```
Sub-topics for "WebdriverIO vs Playwright":

1. Project Setup & Configuration
   - WebFetch: ✅ (docs URLs known)
   - WebSearch: ✅ (need tutorials)
   - Bash (gh): ❌ (not needed)
   → 2 agents

2. Test Syntax & API
   - WebFetch: ✅ (API docs URLs known)
   - WebSearch: ✅ (need examples)
   - Bash (gh): ❌ (not needed)
   → 2 agents

3. Locator Strategies
   - WebFetch: ✅ (docs URLs known)
   - WebSearch: ✅ (need best practices)
   - Bash (gh): ❌ (not needed)
   → 2 agents

4. Community & Ecosystem
   - WebFetch: ❌ (no specific docs)
   - WebSearch: ✅ (need surveys, articles)
   - Bash (gh): ✅ (need GitHub stats)
   → 2 agents

5. CI/CD Integration
   - WebFetch: ✅ (CI docs URLs known)
   - WebSearch: ✅ (need pipeline examples)
   - Bash (gh): ❌ (not needed)
   → 2 agents

Total: 10 agents
```

### Step 2: Spawn agents based on tools needed per sub-topic

Launch all agents in a SINGLE message:

```
// Sub-topic 1: Project Setup (WebFetch + WebSearch)
Agent 1a (WebFetch): Fetch setup docs
Agent 1b (WebSearch): Search setup tutorials

// Sub-topic 2: Test Syntax (WebFetch + WebSearch)
Agent 2a (WebFetch): Fetch API docs
Agent 2b (WebSearch): Search syntax examples

// Sub-topic 3: Locators (WebFetch + WebSearch)
Agent 3a (WebFetch): Fetch locator docs
Agent 3b (WebSearch): Search locator best practices

// Sub-topic 4: Community (WebSearch + Bash)
Agent 4a (WebSearch): Search adoption surveys, community opinions
Agent 4b (Bash): gh CLI for GitHub stars, issues, contributors

// Sub-topic 5: CI/CD (WebFetch + WebSearch)
Agent 5a (WebFetch): Fetch CI docs
Agent 5b (WebSearch): Search CI pipeline examples
```

## Agent Prompt Templates

### WebFetch Agent

```
Research "[SUB_TOPIC]" for [MAIN_TOPIC] by fetching official documentation.

Use the WebFetch tool to fetch these URLs:
1. [URL_1] - Extract [what to look for]
2. [URL_2] - Extract [what to look for]
[Add more URLs as needed]

For each URL, extract:
- Key information relevant to [SUB_TOPIC]
- Code examples
- Configuration options

Return findings organized by source with proper citations.

### Sources
- [Page Title](URL)
```

### WebSearch Agent

```
Research "[SUB_TOPIC]" for [MAIN_TOPIC] by searching the web.

Perform these searches using the WebSearch tool:
1. "[search query 1]"
2. "[search query 2]"
[Add more searches as needed]

For each search, extract:
- Key insights and recommendations
- Pros/cons mentioned
- Community preferences

Return findings with proper source citations.

### Sources
- [Article Title](URL)
```

### Bash (gh CLI) Agent

```
Research "[SUB_TOPIC]" for [MAIN_TOPIC] using GitHub data.

Use the Bash tool with gh CLI commands:
1. gh api repos/[owner]/[repo] --jq '.stargazers_count, .forks_count'
2. gh api repos/[owner]/[repo]/issues --jq 'length'
[Add more commands as needed]

Extract:
- Repository statistics
- Activity metrics
- Community engagement data

Return findings with repository references.

### Sources
- [Repo Name](GitHub URL)
```

## Examples: Dynamic Tool Selection

### Example 1: Technical Comparison (WebdriverIO vs Playwright)

| Sub-topic | WebFetch | WebSearch | Bash (gh) | Total Agents |
|-----------|----------|-----------|-----------|--------------|
| Project Setup | ✅ | ✅ | ❌ | 2 |
| Test Syntax | ✅ | ✅ | ❌ | 2 |
| Locators | ✅ | ✅ | ❌ | 2 |
| Community | ❌ | ✅ | ✅ | 2 |
| CI/CD | ✅ | ✅ | ❌ | 2 |
| **Total** | | | | **10** |

### Example 2: Trending Topic Research (AI Code Assistants)

| Sub-topic | WebFetch | WebSearch | Bash (gh) | Total Agents |
|-----------|----------|-----------|-----------|--------------|
| Overview | ❌ | ✅ | ❌ | 1 |
| Market Players | ❌ | ✅ | ❌ | 1 |
| GitHub Copilot | ✅ | ✅ | ✅ | 3 |
| Privacy Concerns | ❌ | ✅ | ❌ | 1 |
| Future Trends | ❌ | ✅ | ❌ | 1 |
| **Total** | | | | **7** |

### Example 3: Single Tool Deep-Dive (Playwright Guide)

| Sub-topic | WebFetch | WebSearch | Bash (gh) | Total Agents |
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

### From Documentation (WebFetch)
- Key point 1
- Key point 2
- Code example...

### From Web Research (WebSearch)
- Insight 1 (Source: ...)
- Community opinion (Source: ...)

### From GitHub Data (Bash) [if applicable]
- Stars: X
- Open issues: Y
- Recent activity: Z

### Sources
- [Doc Title](URL)
- [Article Title](URL)
- [Repo Name](GitHub URL)
```
