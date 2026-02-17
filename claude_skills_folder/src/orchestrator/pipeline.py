from rich.console import Console
from rich.panel import Panel

console = Console()


class Pipeline:
    def __init__(self, skills: dict):
        self.skills = skills

    def run(self, topic: str, publish: bool = True) -> dict:
        results = {}

        # Step 1: Research
        if "researcher" in self.skills:
            console.print(Panel("[bold blue]Researcher working...[/bold blue]", style="blue"))
            research = self.skills["researcher"].execute(f"Research thoroughly: {topic}")
            results["research"] = research
            self._log(research["metrics"])

        # Step 2: Write
        if "writer" in self.skills:
            console.print(Panel("[bold green]Writer drafting...[/bold green]", style="green"))
            context = {}
            if "research" in results:
                context["research_brief"] = results["research"]["content"]
            draft = self.skills["writer"].execute(
                f"Write a comprehensive article about: {topic}",
                context=context or None,
            )
            results["first_draft"] = draft
            self._log(draft["metrics"])

        # Step 3: Review
        if "reviewer" in self.skills:
            console.print(Panel("[bold yellow]Reviewer evaluating...[/bold yellow]", style="yellow"))
            draft_content = results.get("first_draft", {}).get("content", "")
            review = self.skills["reviewer"].execute(
                "Review this content and provide detailed feedback.",
                context={"draft": draft_content, "original_topic": topic},
            )
            results["review"] = review
            self._log(review["metrics"])

            # Step 4: Revise if needed
            if "NEEDS_REVISION" in review["content"].upper() and "writer" in self.skills:
                console.print(Panel("[bold green]Writer revising...[/bold green]", style="green"))
                revision = self.skills["writer"].execute(
                    "Revise the draft based on reviewer feedback.",
                    context={
                        "original_draft": draft_content,
                        "reviewer_feedback": review["content"],
                        "research_brief": results.get("research", {}).get("content", ""),
                    },
                )
                results["revision"] = revision
                results["final_content"] = revision["content"]
                self._log(revision["metrics"])
            else:
                results["final_content"] = results.get("first_draft", {}).get("content", "")
                console.print("[green]Draft approved -- no revision needed[/green]")
        else:
            results["final_content"] = results.get("first_draft", {}).get("content", "")

        # Step 5: Publish
        if publish and "publisher" in self.skills:
            console.print(Panel("[bold magenta]Publisher posting to Notion...[/bold magenta]", style="magenta"))
            published = self.skills["publisher"].execute(
                "Format and publish this content to Notion.",
                context={"final_content": results.get("final_content", ""), "topic": topic},
            )
            results["publish"] = published
            self._log(published["metrics"])

            if published.get("published"):
                console.print(f"[bold green]Published to Notion:[/bold green] {published.get('notion_url', 'N/A')}")
            else:
                console.print(f"[bold red]Publish failed:[/bold red] {published.get('publish_error', 'Unknown error')}")

        return results

    def _log(self, m):
        console.print(
            f"  Tokens: [cyan]{m.input_tokens:,}[/] in / [cyan]{m.output_tokens:,}[/] out"
            f" | Latency: [yellow]{m.latency_ms:,.0f}ms[/]"
            f" | Cost: [green]${m.cost_usd:.4f}[/]"
        )
