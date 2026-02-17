import time
from abc import ABC, abstractmethod
from pathlib import Path
from google import genai
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


class BaseSkill(ABC):
    """
    Base class for all skills. Each skill:
    1. Reads its system prompt from .gemini/skills/<name>/SKILL.md
    2. Wraps a single Gemini API call with tracing
    """

    def __init__(self, client: genai.Client, model: str, metrics_collector):
        self.client = client
        self.model = model
        self.metrics = metrics_collector
        self.tracer = trace.get_tracer(__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Skill name — must match the .gemini/skills/<name>/ directory."""
        ...

    @property
    def system_prompt(self) -> str:
        """Load system prompt from .gemini/skills/<name>/SKILL.md at runtime."""
        # Try both .gemini/skills and project root skills directory
        paths = [
            Path(f".gemini/skills/{self.name}/SKILL.md"),
            Path(f"skills/{self.name}/SKILL.md")
        ]
        
        for skill_path in paths:
            if skill_path.exists():
                content = skill_path.read_text(encoding="utf-8")
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

            prompt = self._build_prompt(user_message, context)
            span.set_attribute("llm.input", prompt)

            start = time.perf_counter()
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=f"{self.system_prompt}\n\n{prompt}"
                )
                latency = time.perf_counter() - start
                
                content = response.text
                skill_metrics = self.metrics.record(self.name, response, latency)

                span.set_attribute("llm.output", content)
                span.set_attribute("skill.input_tokens", skill_metrics.input_tokens)
                span.set_attribute("skill.output_tokens", skill_metrics.output_tokens)
                span.set_attribute("skill.latency_ms", skill_metrics.latency_ms)
                span.set_attribute("skill.cost_usd", skill_metrics.cost_usd)
                span.set_status(Status(StatusCode.OK))

                return {"content": content, "metrics": skill_metrics}
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise e

    def _build_prompt(self, user_message: str, context: dict = None) -> str:
        msg = user_message
        if context:
            ctx_str = "\n\n".join(f"[{k}]:\n{v}" for k, v in context.items())
            msg = f"{ctx_str}\n\n---\n\n{user_message}"
        return msg
