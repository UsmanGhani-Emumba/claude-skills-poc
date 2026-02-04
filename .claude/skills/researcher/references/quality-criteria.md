# Research Quality Criteria

## Standard Mode

- Minimum 3 sub-topics researched in parallel
- Each sub-topic has at least 2 distinct sources
- Total of 8+ distinct, credible sources across all sub-topics
- Include statistics/data in at least 3 sub-topics
- Prioritize recent information (last 1-2 years when relevant)
- Flag any conflicting information found across sub-topics
- Note gaps where information was not found
- Identify at least 2 cross-cutting insights

## Tool-Based Mode (Additional Criteria)

- Tools are selected dynamically based on sub-topic requirements
- Each sub-topic spawns 1-3 agents depending on tools needed
- WebFetch used when documentation URLs are known
- WebSearch used when articles/tutorials are needed
- Bash (gh CLI) used when GitHub repository data is needed
- Official documentation is included for any tool/framework being discussed
- For comparison topics: both/all items being compared have equivalent source coverage
- Code examples are extracted from official docs via WebFetch when available
- Total agents = sum of tools needed across all sub-topics
