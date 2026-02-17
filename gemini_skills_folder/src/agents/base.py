import os
import subprocess
import json
from google import genai
from google.genai import types
from opentelemetry import trace
from src.config import Config

# Initialize the GenAI Client
client = genai.Client(api_key=Config.GEMINI_API_KEY)
tracer = trace.get_tracer(__name__)

def run_shell_command(command: str) -> str:
    """Executes a shell command and returns the output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        output = result.stdout
        if result.stderr:
            output += f"\nErrors:\n{result.stderr}"
        return output
    except Exception as e:
        return f"Error executing command: {str(e)}"

class BaseAgent:
    def __init__(self, name: str, model_name: str = "gemini-2.0-flash"):
        self.name = name
        self.model_name = model_name
        self.tools = [run_shell_command]

    def execute(self, *args, **kwargs):
        with tracer.start_as_current_span(name=f"{self.name}.execute") as span:
            span.set_attribute("agent.name", self.name)
            try:
                result = self._execute(*args, **kwargs)
                span.set_status(trace.Status(trace.StatusCode.OK))
                return result
            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise e

    def _execute(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement _execute")

    def generate_text(self, prompt: str) -> str:
        with tracer.start_as_current_span(name=f"{self.name}.generate_text") as span:
            span.set_attribute("llm.input", prompt)
            try:
                # Using the new google.genai syntax with tools
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=self.tools,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
                    )
                )
                
                text = response.text
                span.set_attribute("llm.output", text)
                return text
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise e
