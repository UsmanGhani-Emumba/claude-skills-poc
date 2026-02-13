from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest

from researcher.references.researcher import ResearcherSkill
from writer.references.writer import WriterSkill
from reviewer.references.reviewer import ReviewerSkill
from publisher.references.publisher import PublisherSkill
from src.observability.metrics import MetricsCollector


def _make_mock_response(text: str, input_tokens: int = 100, output_tokens: int = 200):
    """Create a mock Anthropic response."""
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    response.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return response


class TestBaseSkill:
    def setup_method(self):
        self.client = MagicMock()
        self.metrics = MetricsCollector(0.015, 0.075)

    def test_researcher_skill_name(self):
        skill = ResearcherSkill(self.client, "claude-opus-4-6", self.metrics)
        assert skill.name == "researcher"

    def test_writer_skill_name(self):
        skill = WriterSkill(self.client, "claude-opus-4-6", self.metrics)
        assert skill.name == "writer"

    def test_reviewer_skill_name(self):
        skill = ReviewerSkill(self.client, "claude-opus-4-6", self.metrics)
        assert skill.name == "reviewer"

    def test_publisher_skill_name(self):
        skill = PublisherSkill(self.client, "claude-opus-4-6", self.metrics)
        assert skill.name == "publisher"

    def test_skill_execute_returns_content_and_metrics(self):
        self.client.messages.create.return_value = _make_mock_response("Research results here")
        skill = ResearcherSkill(self.client, "claude-opus-4-6", self.metrics)
        result = skill.execute("Research AI")

        assert "content" in result
        assert "metrics" in result
        assert result["content"] == "Research results here"
        assert result["metrics"].skill_name == "researcher"

    def test_skill_execute_with_context(self):
        self.client.messages.create.return_value = _make_mock_response("Draft content")
        skill = WriterSkill(self.client, "claude-opus-4-6", self.metrics)
        result = skill.execute("Write article", context={"research_brief": "Some research data"})

        assert result["content"] == "Draft content"
        call_args = self.client.messages.create.call_args
        user_msg = call_args.kwargs["messages"][0]["content"]
        assert "research_brief" in user_msg
        assert "Some research data" in user_msg

    def test_skill_records_metrics(self):
        self.client.messages.create.return_value = _make_mock_response("Output", 150, 300)
        skill = ReviewerSkill(self.client, "claude-opus-4-6", self.metrics)
        result = skill.execute("Review this content")

        assert result["metrics"].input_tokens == 150
        assert result["metrics"].output_tokens == 300
        assert result["metrics"].cost_usd > 0

    def test_skill_fallback_prompt_used_when_no_skill_md(self):
        skill = ResearcherSkill(self.client, "claude-opus-4-6", self.metrics)
        with patch.object(Path, "exists", return_value=False):
            prompt = skill.system_prompt
        assert "expert researcher" in prompt.lower()


class TestPublisherSkill:
    def setup_method(self):
        self.client = MagicMock()
        self.metrics = MetricsCollector(0.015, 0.075)

    def test_publisher_without_notion_client(self):
        self.client.messages.create.return_value = _make_mock_response('{"title": "Test"}')
        skill = PublisherSkill(self.client, "claude-opus-4-6", self.metrics)
        result = skill.execute("Publish this")

        assert result["published"] is False
        assert "not configured" in result["publish_error"]

    def test_publisher_with_notion_client(self):
        self.client.messages.create.return_value = _make_mock_response(
            '{"title": "Test Article", "tags": ["ai"], "category": "Tech", "summary": "A test.", "content_blocks": []}'
        )
        notion_mock = MagicMock()
        notion_mock.create_page.return_value = {"url": "https://notion.so/test-page", "id": "123"}

        skill = PublisherSkill(self.client, "claude-opus-4-6", self.metrics, notion_mock)
        result = skill.execute("Publish this")

        assert result["published"] is True
        assert result["notion_url"] == "https://notion.so/test-page"
