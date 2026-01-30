# Blog Agent POC: Skills vs Multi-Agent Architecture

## The Big Idea

This POC demonstrates how a **single agent with multiple skills** can replace a **multi-agent system** for content creation.

### Traditional Multi-Agent Approach
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Research   │───▶│   Writer    │───▶│  Reviewer   │───▶│  Publisher  │
│   Agent     │    │   Agent     │    │   Agent     │    │   Agent     │
│(Own context)│    │(Own context)│    │(Own context)│    │(Own context)│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
  Message passing    Message passing    Message passing    Final output
  Context handoff    Context handoff    Context handoff
```

**Problems:**
- 4 separate context windows = 4x token costs
- Message passing introduces latency and potential failures
- Context gets "lost in translation" between agents
- Complex orchestration logic needed

### Skills-Based Single Agent Approach
```
┌────────────────────────────────────────────────────────────────────────────┐
│                            SINGLE AGENT                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ Researcher  │  │   Writer    │  │  Reviewer   │  │  Publisher  │       │
│  │   Skill     │  │   Skill     │  │   Skill     │  │   Skill     │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│         │               │               │                 │                │
│         └───────────────┴───────────────┴─────────────────┘                │
│                       SHARED CONTEXT WINDOW                                 │
│                    (Everything is preserved)                                │
└────────────────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- Single context window = lower costs
- Zero message passing = no handoff failures
- Full context preserved across all skills
- Simpler architecture, easier to maintain

---

## Project Structure

```
blog-agent-poc/
├── .claude/
│   └── skills/
│       ├── researcher/
│       │   ├── SKILL.md              # Web research, fact gathering
│       │   └── references/
│       │       └── sample-output.md  # Example research brief
│       ├── writer/
│       │   ├── SKILL.md              # Blog drafting, storytelling
│       │   └── references/
│       │       ├── sample-output.md  # Example blog draft
│       │       └── style-guide.md    # Formatting & typography rules
│       ├── reviewer/
│       │   ├── SKILL.md              # Quality check, polishing
│       │   └── references/
│       │       └── sample-output.md  # Example reviewed output
│       └── publisher/
│           ├── SKILL.md              # Notion publishing
│           └── references/
│               └── sample-output.md  # Example publish output
├── .mcp.json.example                 # MCP config template (commit this)
├── .mcp.json                         # Your MCP config (gitignored)
├── .gitignore
└── README.md
```

---

## How Skills Work

Each skill is a **SKILL.md** file containing:

1. **Metadata** (name + description) - Tells the agent WHEN to activate
2. **Instructions** - Tells the agent HOW to behave when active
3. **Output format** - Ensures consistent, quality results

The agent reads the skill description and decides which skill to activate based on the current task. Unlike multi-agent systems, the same agent embodies different "personas" while maintaining full context.

---

## Demo Script (5 minutes)

### Setup
Ensure the agent has access to the `.claude/skills` folder and web search capability.

### Demo Flow

**Step 1: Give a topic**
> "Write a blog post about [topic the CEO suggests] and publish it to Notion"

**Step 2: Narrate the Research phase**
> "Watch - the agent is now in Researcher mode. It's searching the web, gathering facts, finding statistics..."

*[Show web searches happening, research brief being compiled]*

**Step 3: Narrate the Writing phase**
> "Now it shifts to Writer mode - same agent, different skill, but ALL the research context is preserved. No message passing needed."

*[Show draft being written]*

**Step 4: Narrate the Review phase**
> "Reviewer mode activates to polish the draft. It can see both the original research AND the draft - full context, zero handoff."

*[Show final polished output]*

**Step 5: Narrate the Publish phase**
> "Finally, Publisher mode deploys directly to Notion. The blog appears in your workspace instantly with proper formatting."

*[Show Notion page created with the blog content]*

### Key Demo Talking Points

1. **"One agent, four behaviors"** - Not four agents talking to each other
2. **"Zero context loss"** - The reviewer sees everything the researcher found
3. **"No orchestration complexity"** - No message queues, no coordination bugs
4. **"Easy to extend"** - Adding an SEO skill is just adding one file
5. **"End-to-end automation"** - Research to published Notion page in one conversation

---

## Comparison Summary

| Aspect | Multi-Agent (4 agents) | Skills-Based (1 agent) |
|--------|------------------------|------------------------|
| Context windows | 4 separate | 1 shared |
| Token cost | High (duplicated context) | Lower |
| Handoff failures | Possible at each step | None |
| Context preservation | Partial (summarized) | Complete |
| Add new capability | New agent + coordination | One skill file |
| Debug complexity | High (distributed) | Low (single agent) |
| External integrations | Each agent needs setup | Single MCP config |

---

## Technical Notes

- Skills are loaded on-demand (progressive disclosure)
- Only the relevant skill's instructions enter the context when needed
- The agent decides which skill to activate based on task requirements
- Multiple skills can be used in sequence within a single conversation

---

## Notion MCP Setup

The Publisher skill requires Notion MCP connection. Setup once, use forever.

### Quick Setup

1. **Create Notion integration** at [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. **Copy your token** (starts with `ntn_`)
3. **Create config file:**
   ```bash
   cp .mcp.json.example .mcp.json
   ```
4. **Add your token** to `.mcp.json`
5. **Create a workspace page** in Notion (e.g., "Claude Workspace")
6. **Share the page** with your integration (⋯ → Add connections)
7. **Verify connection:** Run `/mcp` in Claude Code

### For Team Members

Each person needs their own:
- Notion integration token
- `.mcp.json` file (gitignored, not shared)
- Shared pages in their Notion workspace

See `.mcp.json.example` for the config template.

---

## Skill Pipeline

```
/researcher  →  Gathers facts, creates research brief
     ↓
/writer      →  Transforms research into blog draft
     ↓
/reviewer    →  Polishes and improves the draft
     ↓
/publisher   →  Publishes to Notion workspace
```

Each skill is independent and can be used standalone or in sequence.