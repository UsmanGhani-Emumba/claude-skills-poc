#!/usr/bin/env python3
import sys
from dotenv import load_dotenv
from rich.console import Console
from src.config import ANTHROPIC_API_KEY, NOTION_API_KEY, NOTION_PARENT_ID
from src.orchestrator.agent import OrchestratorAgent

console = Console()


def main():
    load_dotenv()
    agent = OrchestratorAgent(
        api_key=ANTHROPIC_API_KEY,
        notion_api_key=NOTION_API_KEY,
        notion_db_id=NOTION_PARENT_ID,
    )

    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        result = agent.run(prompt)
        final = result.get("final_content") or result.get("content", "")
        if final:
            console.print(f"\n[bold]Output:[/bold]\n{final}")
    else:
        console.print("[bold]Orchestrator Agent[/bold] (type 'quit' to exit)\n")
        while True:
            try:
                prompt = console.input("[bold green]You:[/bold green] ")
                if prompt.lower() in ("quit", "exit", "q"):
                    break
                result = agent.run(prompt)
                final = result.get("final_content") or result.get("content", "")
                if final:
                    console.print(f"\n[bold]Output:[/bold]\n{final}\n")
            except KeyboardInterrupt:
                break
        console.print("\n[dim]Goodbye![/dim]")


if __name__ == "__main__":
    main()
