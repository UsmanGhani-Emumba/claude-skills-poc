from rich.console import Console
from rich.panel import Panel

console = Console()


class Pipeline:
    def __init__(self, researcher, writer, reviewer, publisher):
        self.researcher = researcher
        self.writer = writer
        self.reviewer = reviewer
        self.publisher = publisher

    def run(self, topic: str, publish: bool = True) -> dict:
        results = {}

        # Step 1: Research
        console.print(Panel("[bold blue]Researcher working...[/bold blue]", style="blue"))
        research = self.researcher.execute(f"Research thoroughly: {topic}")
        results["research"] = research
        self._log(research["metrics"])

        # Step 2: Write
        console.print(Panel("[bold green]Writer drafting...[/bold green]", style="green"))
        draft = self.writer.execute(
            f"Write a comprehensive article about: {topic}",
            context={"research_brief": research["content"]},
        )
        results["first_draft"] = draft
        self._log(draft["metrics"])

        # Step 3: Review
        console.print(Panel("[bold yellow]Reviewer evaluating...[/bold yellow]", style="yellow"))
        review = self.reviewer.execute(
            "Review this content and provide detailed feedback.",
            context={"draft": draft["content"], "original_topic": topic},
        )
        results["review"] = review
        self._log(review["metrics"])

        # Step 4: Revise if needed
        if "NEEDS_REVISION" in review["content"].upper():
            console.print(Panel("[bold green]Writer revising...[/bold green]", style="green"))
            revision = self.writer.execute(
                "Revise the draft based on reviewer feedback.",
                context={
                    "original_draft": draft["content"],
                    "reviewer_feedback": review["content"],
                    "research_brief": research["content"],
                },
            )
            results["revision"] = revision
            results["final_content"] = revision["content"]
            self._log(revision["metrics"])
        else:
            results["final_content"] = draft["content"]
            console.print("[green]Draft approved -- no revision needed[/green]")

        # Step 5: Publish
        if publish:
            console.print(Panel("[bold magenta]Publisher posting to Notion...[/bold magenta]", style="magenta"))
            published = self.publisher.execute(
                "Format and publish this content to Notion.",
                context={"final_content": results["final_content"], "topic": topic},
            )
            results["publish"] = published
            self._log(published["metrics"])

        return results

    def _log(self, m):
        console.print(
            f"  Tokens: [cyan]{m.input_tokens:,}[/] in / [cyan]{m.output_tokens:,}[/] out"
            f" | Latency: [yellow]{m.latency_ms:,.0f}ms[/]"
            f" | Cost: [green]${m.cost_usd:.4f}[/]"
        )
