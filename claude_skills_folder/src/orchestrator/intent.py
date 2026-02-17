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
        return f"""You are an intent classifier for a content pipeline.
Analyze the user's prompt and determine routing.

Available skills: {skill_list}

Skill descriptions:
{skill_details}
- full_pipeline: Run the full content pipeline (research -> write -> review -> publish)

Respond with ONLY a raw JSON object, no markdown fences, no extra text:
{{"intent": "<skill_name>", "confidence": 0.95, "reasoning": "Brief explanation", "extracted_topic": "The core topic", "publish_to_notion": false}}

Rules:
- "write an article about X" or "create content about X" -> full_pipeline
- Default to full_pipeline if ambiguous and content-related
- Match user intent to the most specific skill available"""

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
