# Blog Agent POC: Skills vs Multi-Agent Architecture

## The Big Idea

This POC demonstrates how a **single agent with multiple skills** can replace a **multi-agent system** for content creation.

### Traditional Multi-Agent Approach
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Research Agent │────▶│  Writer Agent   │────▶│  Reviewer Agent │
│  (Own context)  │     │  (Own context)  │     │  (Own context)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   Message passing         Message passing         Message passing
   Context handoff         Context handoff         Final output
```

**Problems:**
- 3 separate context windows = 3x token costs
- Message passing introduces latency and potential failures
- Context gets "lost in translation" between agents
- Complex orchestration logic needed

### Skills-Based Single Agent Approach
```
┌──────────────────────────────────────────────────────────────┐
│                     SINGLE AGENT                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Researcher  │  │   Writer    │  │  Reviewer   │          │
│  │   Skill     │  │   Skill     │  │   Skill     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│         │               │               │                    │
│         └───────────────┴───────────────┘                    │
│                 SHARED CONTEXT WINDOW                        │
│              (Everything is preserved)                       │
└──────────────────────────────────────────────────────────────┘
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
├── skills/
│   ├── researcher/
│   │   └── SKILL.md    # Web research, fact gathering
│   ├── writer/
│   │   └── SKILL.md    # Blog drafting, storytelling
│   └── reviewer/
│       └── SKILL.md    # Quality check, polishing
├── examples/
│   └── sample-output.md
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
Ensure the agent has access to the skills folder and web search capability.

### Demo Flow

**Step 1: Give a topic**
> "Write a blog post about [topic the CEO suggests]"

**Step 2: Narrate the Research phase**
> "Watch - the agent is now in Researcher mode. It's searching the web, gathering facts, finding statistics..."

*[Show web searches happening, research brief being compiled]*

**Step 3: Narrate the Writing phase**
> "Now it shifts to Writer mode - same agent, different skill, but ALL the research context is preserved. No message passing needed."

*[Show draft being written]*

**Step 4: Narrate the Review phase**
> "Finally, Reviewer mode activates to polish the draft. It can see both the original research AND the draft - full context, zero handoff."

*[Show final polished output]*

### Key Demo Talking Points

1. **"One agent, three behaviors"** - Not three agents talking to each other
2. **"Zero context loss"** - The reviewer sees everything the researcher found
3. **"No orchestration complexity"** - No message queues, no coordination bugs
4. **"Easy to extend"** - Adding an SEO skill is just adding one file

---

## Comparison Summary

| Aspect | Multi-Agent | Skills-Based |
|--------|-------------|--------------|
| Context windows | N (one per agent) | 1 |
| Token cost | High (duplicated context) | Lower |
| Handoff failures | Possible | None |
| Context preservation | Partial (summarized) | Complete |
| Add new capability | New agent + coordination | One skill file |
| Debug complexity | High (distributed) | Low (single agent) |

---

## Technical Notes

- Skills are loaded on-demand (progressive disclosure)
- Only the relevant skill's instructions enter the context when needed
- The agent decides which skill to activate based on task requirements
- Multiple skills can be used in sequence within a single conversation
