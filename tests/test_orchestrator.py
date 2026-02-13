import json
from unittest.mock import MagicMock, patch
import pytest

from src.orchestrator.intent import IntentDetector
from src.orchestrator.pipeline import Pipeline
from src.observability.metrics import MetricsCollector, SkillMetrics


def _make_mock_response(text: str, input_tokens: int = 100, output_tokens: int = 200):
    """Create a mock Anthropic response."""
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    response.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return response


class TestIntentDetector:
    def setup_method(self):
        self.client = MagicMock()
        self.metrics = MetricsCollector(0.015, 0.075)

    def test_detect_researcher_intent(self):
        intent_json = json.dumps({
            "intent": "researcher",
            "confidence": 0.95,
            "reasoning": "User wants to research a topic",
            "extracted_topic": "quantum computing",
            "publish_to_notion": False,
        })
        self.client.messages.create.return_value = _make_mock_response(intent_json)

        detector = IntentDetector(self.client, "claude-opus-4-6", self.metrics)
        result = detector.detect("Research quantum computing")

        assert result["intent"] == "researcher"
        assert result["confidence"] == 0.95
        assert result["extracted_topic"] == "quantum computing"

    def test_detect_full_pipeline_intent(self):
        intent_json = json.dumps({
            "intent": "full_pipeline",
            "confidence": 0.9,
            "reasoning": "User wants end-to-end content creation",
            "extracted_topic": "AI trends",
            "publish_to_notion": True,
        })
        self.client.messages.create.return_value = _make_mock_response(intent_json)

        detector = IntentDetector(self.client, "claude-opus-4-6", self.metrics)
        result = detector.detect("Write an article about AI trends")

        assert result["intent"] == "full_pipeline"
        assert result["publish_to_notion"] is True

    def test_intent_records_metrics(self):
        intent_json = json.dumps({
            "intent": "writer",
            "confidence": 0.8,
            "reasoning": "test",
            "extracted_topic": "test",
            "publish_to_notion": False,
        })
        self.client.messages.create.return_value = _make_mock_response(intent_json, 50, 30)

        detector = IntentDetector(self.client, "claude-opus-4-6", self.metrics)
        detector.detect("Write something")

        assert len(self.metrics.history) == 1
        assert self.metrics.history[0].skill_name == "intent_detection"


class TestPipeline:
    def setup_method(self):
        self.researcher = MagicMock()
        self.writer = MagicMock()
        self.reviewer = MagicMock()
        self.publisher = MagicMock()

        metrics = SkillMetrics(skill_name="test", input_tokens=100, output_tokens=200, latency_ms=500, cost_usd=0.01)

        for skill in [self.researcher, self.writer, self.reviewer, self.publisher]:
            skill.execute.return_value = {"content": "test content", "metrics": metrics}

    def test_pipeline_approved_no_revision(self):
        self.reviewer.execute.return_value = {
            "content": "Score: 9/10. Verdict: APPROVED. Great work!",
            "metrics": SkillMetrics(skill_name="reviewer", input_tokens=100, output_tokens=200, latency_ms=500, cost_usd=0.01),
        }

        pipeline = Pipeline(self.researcher, self.writer, self.reviewer, self.publisher)
        result = pipeline.run("test topic", publish=False)

        assert "final_content" in result
        assert "revision" not in result
        self.writer.execute.assert_called_once()

    def test_pipeline_needs_revision(self):
        self.reviewer.execute.return_value = {
            "content": "Score: 5/10. Verdict: NEEDS_REVISION. Please fix issues.",
            "metrics": SkillMetrics(skill_name="reviewer", input_tokens=100, output_tokens=200, latency_ms=500, cost_usd=0.01),
        }

        pipeline = Pipeline(self.researcher, self.writer, self.reviewer, self.publisher)
        result = pipeline.run("test topic", publish=False)

        assert "revision" in result
        assert self.writer.execute.call_count == 2

    def test_pipeline_with_publish(self):
        self.reviewer.execute.return_value = {
            "content": "APPROVED",
            "metrics": SkillMetrics(skill_name="reviewer", input_tokens=100, output_tokens=200, latency_ms=500, cost_usd=0.01),
        }

        pipeline = Pipeline(self.researcher, self.writer, self.reviewer, self.publisher)
        result = pipeline.run("test topic", publish=True)

        self.publisher.execute.assert_called_once()
        assert "publish" in result
