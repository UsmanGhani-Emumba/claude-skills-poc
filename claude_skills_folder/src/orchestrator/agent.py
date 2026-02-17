from anthropic import Anthropic
from rich.console import Console
from rich.table import Table

from src.config import MODEL_NAME, INPUT_COST_PER_1K, OUTPUT_COST_PER_1K, CONTEXT_WINDOW
from src.observability.tracer import launch_phoenix, setup_observability, _slugify
from src.observability.metrics import MetricsCollector
from src.orchestrator.intent import IntentDetector
from src.orchestrator.pipeline import Pipeline
from registry import SkillRegistry

console = Console()


class OrchestratorAgent:
    def __init__(self, api_key: str):
        # Step 1: Launch Phoenix UI (tracer registered later with topic name)
        launch_phoenix()

        # Step 2: Anthropic client
        self.client = Anthropic(api_key=api_key)
        self.model = MODEL_NAME

        # Step 3: Metrics
        self.metrics = MetricsCollector(INPUT_COST_PER_1K, OUTPUT_COST_PER_1K)

        # Step 4: Auto-discover skills from .claude/skills/*/SKILL.md
        self.registry = SkillRegistry()
        self.registry.discover()

        # Step 5: Intent detector (with dynamic skill descriptions)
        self.intent_detector = IntentDetector(
            self.client, self.model, self.metrics,
            skill_descriptions=self.registry.get_skill_descriptions(),
        )

        # Step 6: Load all skills (publisher gets extra kwargs)
        self.skills = self.registry.load_all(
            self.client, self.model, self.metrics,
            extra_kwargs={
                "publisher": {"notion_mcp_client": None},
            },
        )

        # Step 7: Pipeline
        self.pipeline = Pipeline(self.skills)

    def run(self, user_prompt: str) -> dict:
        console.print(f"\n[bold]Prompt:[/bold] {user_prompt}\n")

        # Detect intent
        console.print("[dim]Detecting intent...[/dim]")
        intent_result = self.intent_detector.detect(user_prompt)
        intent = intent_result["intent"]
        topic = intent_result["extracted_topic"]

        console.print(
            f"[bold]Intent:[/bold] {intent} "
            f"(confidence: {intent_result['confidence']:.0%})\n"
            f"[bold]Topic:[/bold] {topic}\n"
        )

        # Register tracer with topic-based project name so spans appear
        # under a meaningful project in the Phoenix dashboard
        project_name = _slugify(topic)
        self.tracer_provider = setup_observability(project_name)
        console.print(f"[dim]Phoenix project: {project_name}[/dim]\n")

        # Route dynamically
        if intent == "full_pipeline":
            publish = intent_result.get("publish_to_notion", True)
            result = self.pipeline.run(topic, publish=publish)
        elif intent in self.skills:
            result = self.skills[intent].execute(topic)
        elif intent == "unknown":
            console.print(
                "[bold yellow]No matching skill found for this request.[/bold yellow]\n"
                f"Available skills: {', '.join(self.skills.keys())}"
            )
            result = {"error": "No matching skill for this request", "topic": topic}
        else:
            console.print(f"[dim]Unknown intent '{intent}', falling back to full pipeline[/dim]")
            result = self.pipeline.run(topic)

        # Summary
        self._print_summary()
        return result

    def _print_summary(self):
        s = self.metrics.summary()

        table = Table(title="Pipeline Metrics Summary")
        table.add_column("Metric", style="bold")
        table.add_column("Value", style="cyan")
        table.add_row("Total Input Tokens", f"{s['total_input_tokens']:,}")
        table.add_row("Total Output Tokens", f"{s['total_output_tokens']:,}")
        table.add_row("Context Window", f"{s['context_window']:,} tokens")
        table.add_row("Total Latency", f"{s['total_latency_ms']:,.0f} ms")
        table.add_row("Total Cost", f"${s['total_cost_usd']:.4f}")
        table.add_row("Skills Invoked", " -> ".join(s["skills_invoked"]))
        console.print(table)

        detail = Table(title="Per-Skill Breakdown")
        detail.add_column("Skill")
        detail.add_column("Input Tokens")
        detail.add_column("Output Tokens")
        detail.add_column("Latency (ms)")
        detail.add_column("Cost")
        for m in s["per_skill"]:
            detail.add_row(
                m["skill_name"],
                f"{m['input_tokens']:,}",
                f"{m['output_tokens']:,}",
                f"{m['latency_ms']:,.0f}",
                f"${m['cost_usd']:.4f}",
            )
        console.print(detail)
        console.print(f"\n[dim]Phoenix dashboard: http://localhost:6006[/dim]\n")
