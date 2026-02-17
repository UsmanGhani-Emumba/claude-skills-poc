import os
import sys
from dotenv import load_dotenv

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.orchestrator import Orchestrator
from src.config import Config
import phoenix as px
from phoenix.otel import register

def main():
    # Load environment variables
    load_dotenv()
    
    try:
        Config.validate()
    except ValueError as e:
        print(f"Config Error: {e}")
        return

    # Initialize Arize Phoenix for observability
    print("Initializing Arize Phoenix tracing...")
    session = px.launch_app()
    
    # Configure OpenTelemetry to export to Phoenix using the modern register method
    # auto_instrument=True will detect openinference-instrumentation-google-genai
    register(
        project_name="gemini-orchestrator",
        endpoint="http://localhost:6006/v1/traces",
        auto_instrument=True
    )
    
    print(f"Phoenix UI available at: {session.url}")

    orchestrator = Orchestrator()
    
    print("\n--- Gemini Skill Orchestrator (genai v1) Ready ---")
    
    while True:
        try:
            topic = input("\nEnter a topic (or 'exit' to quit): ").strip()
            
            if topic.lower() == 'exit':
                break
                
            if topic:
                result = orchestrator.execute(topic)
                print(f"\nFINAL RESULT:\n{result}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
