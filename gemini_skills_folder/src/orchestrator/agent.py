import sys
import os
from google import genai
from rich.console import Console
from rich.table import Table

from src.config import Config
from src.observability.tracer import launch_phoenix, setup_observability, _slugify
from src.observability.metrics import MetricsCollector
from src.orchestrator.intent import IntentDetector
from src.orchestrator.pipeline import Pipeline

# Add .gemini/skills to sys.path to allow importing skills
skills_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".gemini", "skills"))
if skills_path not in sys.path:
    sys.path.insert(0, skills_path)

from researcher.references.researcher import ResearcherSkill
from writer.references.writer import WriterSkill
from reviewer.references.reviewer import ReviewerSkill
from publisher.references.notion_publish import PublisherSkill

console = Console()


class OrchestratorAgent:
    def __init__(self, api_key: str):
        # Step 1: Launch Phoenix UI
        launch_phoenix()

        # Step 2: Gemini client
        self.client = genai.Client(api_key=api_key)
        self.model = Config.MODEL_NAME

        # Step 3: Metrics
        self.metrics = MetricsCollector(Config.INPUT_COST_PER_1K, Config.OUTPUT_COST_PER_1K)

        # Step 4: Intent detector
        self.intent_detector = IntentDetector(self.client, self.model, self.metrics)

        # Step 5: Skills
        self.researcher = ResearcherSkill(self.client, self.model, self.metrics)
        self.writer = WriterSkill(self.client, self.model, self.metrics)
        self.reviewer = ReviewerSkill(self.client, self.model, self.metrics)
        self.publisher = PublisherSkill(self.client, self.model, self.metrics)

        # Step 6: Pipeline
        self.pipeline = Pipeline(self.researcher, self.writer, self.reviewer, self.publisher)

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

        # Register tracer with topic-based project name
        project_name = _slugify(topic)
        self.tracer_provider = setup_observability(project_name)
        console.print(f"[dim]Phoenix project: {project_name}[/dim]\n")

        # Route
        if intent == "full_pipeline":
            publish = intent_result.get("publish_to_notion", True)
            result = self.pipeline.run(topic, publish=publish)
        elif intent == "researcher":
            result = self.researcher.execute(topic)
        elif intent == "writer":
            result = self.writer.execute(topic)
        elif intent == "reviewer":
            result = self.reviewer.execute(topic)
        elif intent == "publisher":
            result = self.publisher.execute(topic)
        else:
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
