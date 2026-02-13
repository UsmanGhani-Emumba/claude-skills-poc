import time
from abc import ABC, abstractmethod
from pathlib import Path
from anthropic import Anthropic
from opentelemetry import trace


class BaseSkill(ABC):
    """
    Base class for all skills. Each skill:
    1. Reads its system prompt from .claude/skills/<name>/SKILL.md
    2. Wraps a single Anthropic API call with tracing
    3. Records metrics via MetricsCollector
    """

    def __init__(self, client: Anthropic, model: str, metrics_collector):
        self.client = client
        self.model = model
        self.metrics = metrics_collector
        self.tracer = trace.get_tracer(__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Skill name — must match the .claude/skills/<name>/ directory."""
        ...

    @property
    def system_prompt(self) -> str:
        """Load system prompt from .claude/skills/<name>/SKILL.md at runtime."""
        skill_path = Path(f".claude/skills/{self.name}/SKILL.md")
        if skill_path.exists():
            content = skill_path.read_text()
            # Strip YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    return parts[2].strip()
            return content
        return self._fallback_prompt

    @property
    @abstractmethod
    def _fallback_prompt(self) -> str:
        """Fallback prompt if SKILL.md is not found."""
        ...

    def execute(self, user_message: str, context: dict = None) -> dict:
        """Execute the skill with full tracing. Returns dict with 'content' and 'metrics'."""
        with self.tracer.start_as_current_span(f"skill.{self.name}") as span:
            span.set_attribute("skill.name", self.name)
            span.set_attribute("skill.model", self.model)

            messages = self._build_messages(user_message, context)

            start = time.perf_counter()
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16384,
                system=self.system_prompt,
                messages=messages,
            )
            latency = time.perf_counter() - start

            content = response.content[0].text
            skill_metrics = self.metrics.record(self.name, response, latency)

            span.set_attribute("skill.input_tokens", skill_metrics.input_tokens)
            span.set_attribute("skill.output_tokens", skill_metrics.output_tokens)
            span.set_attribute("skill.latency_ms", skill_metrics.latency_ms)
            span.set_attribute("skill.cost_usd", skill_metrics.cost_usd)

            return {"content": content, "metrics": skill_metrics}

    def _build_messages(self, user_message: str, context: dict = None) -> list:
        msg = user_message
        if context:
            ctx_str = "\n\n".join(f"[{k}]:\n{v}" for k, v in context.items())
            msg = f"{ctx_str}\n\n---\n\n{user_message}"
        return [{"role": "user", "content": msg}]
