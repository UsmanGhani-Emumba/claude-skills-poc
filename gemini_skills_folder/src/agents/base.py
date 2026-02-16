import os
import google.generativeai as genai
from phoenix.trace import tracer
from src.config import Config

# Configure Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)

class BaseAgent:
    def __init__(self, name: str, model_name: str = "gemini-pro"):
        self.name = name
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)

    def execute(self, *args, **kwargs):
        with tracer().start_span(name=f"{self.name}.execute") as span:
            span.set_attribute("agent.name", self.name)
            try:
                result = self._execute(*args, **kwargs)
                span.set_status(status_code="OK")
                return result
            except Exception as e:
                span.set_status(status_code="ERROR", description=str(e))
                raise e

    def _execute(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement _execute")

    def generate_text(self, prompt: str) -> str:
        with tracer().start_span(name=f"{self.name}.generate_text") as span:
            span.set_attribute("llm.input", prompt)
            try:
                response = self.model.generate_content(prompt)
                text = response.text
                span.set_attribute("llm.output", text)
                return text
            except Exception as e:
                span.set_attribute("error", str(e))
                raise e
