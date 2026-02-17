import os
import sys
from dotenv import load_dotenv
from rich.console import Console

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.orchestrator.agent import OrchestratorAgent
from src.config import Config

console = Console()

def main():
    # Load environment variables
    load_dotenv()
    
    try:
        Config.validate()
    except ValueError as e:
        console.print(f"[bold red]Config Error:[/bold red] {e}")
        return

    agent = OrchestratorAgent(api_key=Config.GEMINI_API_KEY)
    
    console.print("\n--- [bold green]Gemini Skill Orchestrator Ready[/bold green] ---\n")
    
    while True:
        try:
            prompt = console.input("[bold blue]You:[/bold blue] ").strip()
            
            if prompt.lower() in ('exit', 'quit', 'q'):
                break
                
            if prompt:
                result = agent.run(prompt)
                # Display final content if it exists
                final = result.get("final_content") or result.get("content", "")
                if final:
                    console.print(f"\n[bold]Final Output:[/bold]\n{final}\n")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"\n[bold red]An error occurred:[/bold red] {e}")

    console.print("\n[dim]Goodbye![/dim]")

if __name__ == "__main__":
    main()
