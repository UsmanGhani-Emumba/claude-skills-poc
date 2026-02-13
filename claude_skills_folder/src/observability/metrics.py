from dataclasses import dataclass
from src.config import CONTEXT_WINDOW


@dataclass
class SkillMetrics:
    skill_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    context_window: int = CONTEXT_WINDOW
    latency_ms: float = 0.0
    cost_usd: float = 0.0


class MetricsCollector:
    def __init__(self, input_cost_per_1k: float, output_cost_per_1k: float):
        self.input_cost = input_cost_per_1k
        self.output_cost = output_cost_per_1k
        self.history: list[SkillMetrics] = []

    def record(self, skill_name: str, response, latency_s: float) -> SkillMetrics:
        usage = response.usage
        cost = (usage.input_tokens / 1000 * self.input_cost) + \
               (usage.output_tokens / 1000 * self.output_cost)

        metrics = SkillMetrics(
            skill_name=skill_name,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=latency_s * 1000,
            cost_usd=cost,
        )
        self.history.append(metrics)
        return metrics

    def summary(self) -> dict:
        return {
            "total_input_tokens": sum(m.input_tokens for m in self.history),
            "total_output_tokens": sum(m.output_tokens for m in self.history),
            "total_latency_ms": sum(m.latency_ms for m in self.history),
            "total_cost_usd": sum(m.cost_usd for m in self.history),
            "context_window": CONTEXT_WINDOW,
            "skills_invoked": [m.skill_name for m in self.history],
            "per_skill": [vars(m) for m in self.history],
        }
