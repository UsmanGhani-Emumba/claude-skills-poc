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
├── .mcp-example.json                 # MCP config template (commit this)
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

### Prerequisites

Before using the publisher skill, you must set up your Notion workspace:

1. **Create a Parent Page** in Notion (e.g., "Blog Posts" or "Claude Workspace")
   - This acts as a container for all your published content

2. **Create Child Pages** for each blog you want to publish
   - Create an empty child page under the parent with the exact name you'll use in your prompt
   - Example: Create a page named "Agentic AI" under "Blog Posts"

3. **Share the Parent Page** with your integration
   - Open the parent page in Notion
   - Click the `⋯` menu (top right)
   - Select **Add connections**
   - Choose your integration
   - All child pages will inherit this access

```
Notion Workspace
└── Blog Posts (Parent Page) ← Share this with integration
    ├── Agentic AI (Child Page) ← Use this name in prompt
    ├── Future of Work (Child Page)
    └── AI in Healthcare (Child Page)
```

### Integration Setup

#### Step 1: Create a Notion Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Fill in the details:
   - **Name:** Give it a name (e.g., "Claude Blog Publisher")
   - **Associated workspace:** Select your Notion workspace
   - **Type:** Keep as "Internal integration"
4. Click **"Submit"**

#### Step 2: Get the Integration Secret Key

1. After creating the integration, you'll see the **"Internal Integration Secret"**
2. Click **"Show"** to reveal the token
3. Click **"Copy"** to copy the token
   - The token starts with `ntn_` (e.g., `ntn_abc123xyz...`)
4. **Keep this token safe** - treat it like a password

#### Step 3: Configure the MCP Server

1. **Create config file:**
   ```bash
   cp .mcp-example.json .mcp.json
   ```

2. **Add your token** to `.mcp.json`:
   ```json
   {
     "mcpServers": {
       "notion": {
         "command": "npx",
         "args": ["-y", "@notionhq/notion-mcp-server"],
         "env": {
           "NOTION_TOKEN": "ntn_your_token_here"
         }
       }
     }
   }
   ```
   Replace `ntn_your_token_here` with the token you copied.

#### Step 4: Connect Integration to Your Pages

1. Open your **Parent Page** in Notion (e.g., "Blog Posts")
2. Click the `⋯` menu (top right corner)
3. Scroll down and click **"Add connections"**
4. Search for your integration name (e.g., "Claude Blog Publisher")
5. Click to add it
6. Confirm by clicking **"Confirm"**

All child pages under this parent will automatically have access.

#### Step 5: Verify Connection

Run `/mcp` command in Claude Code CLI to verify the Notion MCP server is connected and working.

### Usage Example

Once setup is complete, use this prompt in Claude Code CLI:

```
Write a blog on "What is Agentic AI" and publish on Notion on page "Agentic AI"
```

**Note:** The page name must already exist in Notion, otherwise the API call will fail.

The agent will:
1. Research the topic (Researcher skill)
2. Write the blog post (Writer skill)
3. Review and polish (Reviewer skill)
4. Publish to the specified Notion page (Publisher skill)

### For Team Members

Each person needs their own:
- Notion integration token
- `.mcp.json` file (gitignored, not shared)
- Shared pages in their Notion workspace

See `.mcp-example.json` for the config template.

### Workspace Example:

**Workspace URL :**  https://www.notion.so/Claude-Workspace-2f801e7f802c80cda17cd058fe3d60b3

---

## Skill Pipeline

These commands can be found in Claude Code CLI:

```
/researcher  →  Gathers facts, creates research brief
     ↓
/writer      →  Transforms research into blog draft
     ↓
/reviewer    →  Polishes and improves the draft
     ↓
/publisher   →  Publishes to Notion workspace
```

Each skill is independent and can be used standalone or in sequence within Claude Code CLI.