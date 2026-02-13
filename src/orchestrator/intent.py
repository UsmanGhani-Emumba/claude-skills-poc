import json
import re
import time

INTENT_SYSTEM_PROMPT = """You are an intent classifier for a content pipeline.
Analyze the user's prompt and determine routing.

Available skills: researcher, writer, reviewer, publisher, full_pipeline

Respond with ONLY a raw JSON object, no markdown fences, no extra text:
{"intent": "researcher", "confidence": 0.95, "reasoning": "Brief explanation", "extracted_topic": "The core topic", "publish_to_notion": false}

Rules:
- "write an article about X" or "create content about X" → full_pipeline
- "research X" or "find information about X" → researcher
- "write/draft X" with provided context → writer
- "review this" or "edit this" → reviewer
- "publish this to Notion" → publisher
- Default to full_pipeline if ambiguous and content-related"""


def _extract_json(text: str) -> dict:
    """Extract JSON from a response that may contain markdown fences or extra text."""
    # Try direct parse first
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Find first { ... } block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from response: {text[:200]}")


class IntentDetector:
    def __init__(self, client, model, metrics_collector):
        self.client = client
        self.model = model
        self.metrics = metrics_collector

    def detect(self, user_prompt: str) -> dict:
        start = time.perf_counter()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=INTENT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        latency = time.perf_counter() - start
        self.metrics.record("intent_detection", response, latency)
        return _extract_json(response.content[0].text)
