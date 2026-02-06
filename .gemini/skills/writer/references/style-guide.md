# Blog Writing Style Guide

## Voice & Tone

**Primary Voice:** Conversational authority
- Write like explaining to a smart friend over coffee
- Be confident, not arrogant
- Be clear, not simplistic
- Be engaging, not clickbaity

**Tone Spectrum:**
| Context | Tone |
|---------|------|
| Opening hook | Bold, intriguing |
| Explaining concepts | Warm, patient |
| Presenting data | Direct, credible |
| Conclusions | Thoughtful, memorable |

**Avoid:**
- Corporate jargon ("synergy", "leverage", "utilize")
- Filler phrases ("it goes without saying", "at the end of the day")
- Passive voice when active is clearer
- Hedging language ("maybe", "perhaps", "it seems like")


## Document Structure

**Hierarchy:**
```
# Title (H1) — One per document, the hook
  
## Main Section (H2) — 3-5 per blog post

### Subsection (H3) — Only if section needs subdivision

Body text — The actual content
```

**Section Flow:**
1. **Opening** — Hook + thesis (1-2 paragraphs)
2. **Context** — Why this matters now (1 section)
3. **Core Content** — The meat (2-3 sections)
4. **Implication** — So what? What's next? (1 section)
5. **Closing** — Memorable ending (1-2 paragraphs)


## Typography & Formatting

**Headings:**
- H1: Title case for blog title only
- H2: Sentence case ("The data doesn't lie" not "The Data Doesn't Lie")
- H3: Sentence case, use sparingly
- Never skip levels (H1 → H3)
- Never end headings with punctuation

**Paragraphs:**
- 2-4 sentences ideal, 5 maximum
- One idea per paragraph
- Single blank line between paragraphs
- First paragraph after heading: no indent

**Emphasis:**
- **Bold** — Key terms, critical points, words you'd stress verbally
- *Italics* — Book/article titles, foreign words, introducing new terms
- `Code` — Technical terms, file names, commands
- Never combine bold and italics
- Never use ALL CAPS (reads as shouting)
- Use emphasis sparingly — if everything is bold, nothing is

**Line Breaks:**
- One blank line after headings
- Two blank lines before H2 sections
- No trailing whitespace
- No multiple consecutive blank lines


## Lists & Bullets

**When to Use:**
- Bullet points: Unordered items, features, examples
- Numbered lists: Sequential steps, rankings, priorities
- Avoid lists for: Narrative content, arguments, emotional appeals

**List Formatting:**
- Lead-in sentence ends with colon
- Each item starts with capital letter
- Parallel structure (all nouns, all verbs, all sentences)
- No periods for short items (under 5 words)
- Periods for complete sentences
- 3-7 items ideal, never exceed 10

**Example — Good:**
```markdown
The report highlighted three concerns:
- Rising operational costs
- Declining customer retention
- Increased competitor activity
```

**Example — Bad:**
```markdown
The report highlighted concerns:
- costs are rising
- Customer retention is declining.
- competitors
```


## Callouts & Special Elements

**Blockquotes** — For direct quotes or key callouts:
```markdown
> "The best time to plant a tree was 20 years ago. The second best time is now."
> — Chinese Proverb
```

**Callout Boxes** (Notion-style):
```markdown
💡 **Key Insight:** One sentence summarizing the crucial point.

⚠️ **Warning:** Important caveat the reader should know.

📊 **By the Numbers:** Quick stat or data point.
```

**Horizontal Rules** — Use sparingly:
- Before source citations at end
- To separate major thematic shifts
- Never more than 2 per post


## Numbers & Data

**General Rules:**
- Spell out one through nine
- Use numerals for 10 and above
- Always use numerals for: percentages, money, measurements
- Use numerals when comparing ("5 of the 12 respondents")

**Percentages:**
- Use % symbol with numerals: 67%, not sixty-seven percent
- Round to whole numbers unless precision matters
- Always provide context: "67% of workers" not just "67%"

**Large Numbers:**
- Use words for readability: "$11 million" not "$11,000,000"
- Be consistent within a paragraph

**Data Presentation:**
```markdown
Good: "Nearly 60% of workers—about 80 million Americans—now have remote options."
Bad: "58.3% of workers (approximately 79,847,000 people) have remote options."
```


## Links & Citations

**Inline Links:**
- Anchor text should be descriptive, not "click here"
- Good: "according to [McKinsey's workforce analysis](url)"
- Bad: "according to this report ([link](url))"

**Source Citations:**
- Integrate naturally: "Stanford researchers found..."
- Parenthetical when needed: (Buffer State of Remote Work, 2024)
- End-of-post source list for transparency

**Citation Format:**
```markdown
---
*Sources: [Source 1 Name](url), [Source 2 Name](url), [Source 3 Name](url)*
```


## Readability Standards

**Sentence Length:**
- Average: 15-20 words
- Mix short punchy sentences with longer flowing ones
- Never exceed 35 words in a single sentence
- Use short sentences for emphasis. Like this.

**Paragraph Length:**
- 40-80 words ideal
- Never exceed 100 words
- Single-sentence paragraphs for dramatic effect (use sparingly)

**Reading Level:**
- Target: 8th-10th grade reading level
- Avoid jargon without explanation
- Prefer common words over fancy alternatives

**Word Choice:**
| Avoid | Prefer |
|-------|--------|
| utilize | use |
| facilitate | help |
| implement | start, build |
| leverage | use |
| synergy | teamwork |
| paradigm | model, approach |


## Notion-Specific Best Practices

**Toggle Sections:**
- Use for supplementary detail readers might skip
- Never hide critical information in toggles

**Tables:**
- Use for comparisons, not decoration
- Keep to 2-4 columns maximum
- Header row always bold

**Dividers:**
- Use `---` for thematic breaks
- Don't overuse — breaks reading flow

**Emoji Usage:**
- Acceptable in callout boxes
- Acceptable in informal/casual blogs
- Never in headings
- Never more than one per paragraph
- When in doubt, leave it out


## Opening & Closing Patterns

**Strong Openings:**
1. **Surprising stat:** "Sixty-seven percent of workers would choose flexibility over a raise."
2. **Provocative question:** "What if everything you know about productivity is wrong?"
3. **Bold claim:** "The office is dead. It just doesn't know it yet."
4. **Scene setting:** "It's 9 AM. You're still in your pajamas. And you've never been more productive."
5. **Contrast:** "They said remote work would kill collaboration. The data says otherwise."

**Weak Openings to Avoid:**
- "In this blog post, I will discuss..."
- "Have you ever wondered about...?"
- "According to Webster's dictionary..."
- "Since the dawn of time..."

**Strong Closings:**
1. **Forward-looking:** End with what happens next
2. **Callback:** Reference your opening hook
3. **Challenge:** Pose a question for the reader
4. **Memorable line:** Something quotable

**Weak Closings to Avoid:**
- "In conclusion..."
- "To summarize what we've discussed..."
- "I hope you found this helpful"
- Generic call-to-action