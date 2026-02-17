import json
import re
import time


def _extract_json(text: str) -> dict:
    """Extract JSON from a response that may contain markdown fences or extra text."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            pass

    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from response: {text[:200]}")


class IntentDetector:
    def __init__(self, client, model, metrics_collector, skill_descriptions: dict[str, str] = None):
        self.client = client
        self.model = model
        self.metrics = metrics_collector
        self._skill_descriptions = skill_descriptions or {}

    @property
    def system_prompt(self) -> str:
        skill_list = ", ".join(
            list(self._skill_descriptions.keys()) + ["full_pipeline"]
        )
        skill_details = "\n".join(
            f"- {name}: {desc}" for name, desc in self._skill_descriptions.items()
        )
        return f"""You are an intent classifier for an agent orchestrator.
Analyze the user's prompt and route to exactly one skill.

Available skills: {skill_list}

Skill descriptions:
{skill_details}
- full_pipeline: Run the full content creation pipeline (research -> write -> review -> publish). Only use for content creation requests.

Respond with ONLY a raw JSON object, no markdown fences, no extra text:
{{"intent": "<skill_name>", "confidence": 0.95, "reasoning": "Brief explanation", "extracted_topic": "The core topic", "publish_to_notion": false}}

Routing rules (evaluate in order, use the FIRST match):

1. **Skill description match** — Compare the user's request against each skill description above. If a skill's description clearly matches the user's intent, route to that skill. This is the PRIMARY routing mechanism.

2. **Content creation pipeline** — If the user wants end-to-end content creation (e.g. "write an article about X", "create a blog post about X"), route to full_pipeline.

3. **No match** — If no skill description matches and the request is not about content creation, set intent to "unknown" with a low confidence score.

Guidelines:
- Always prefer a specific skill match over full_pipeline.
- Set publish_to_notion to true only when the user explicitly mentions Notion or publishing.
- For ambiguous requests, pick the skill whose description is the closest semantic match.
- Do NOT force-route unrelated requests to full_pipeline."""

    def detect(self, user_prompt: str) -> dict:
        start = time.perf_counter()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        latency = time.perf_counter() - start
        self.metrics.record("intent_detection", response, latency)
        return _extract_json(response.content[0].text)
