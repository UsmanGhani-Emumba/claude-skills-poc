from unittest.mock import MagicMock
import pytest

from src.observability.metrics import MetricsCollector, SkillMetrics


class TestSkillMetrics:
    def test_default_values(self):
        metrics = SkillMetrics(skill_name="test")
        assert metrics.skill_name == "test"
        assert metrics.input_tokens == 0
        assert metrics.output_tokens == 0
        assert metrics.latency_ms == 0.0
        assert metrics.cost_usd == 0.0
        assert metrics.context_window == 200_000


class TestMetricsCollector:
    def setup_method(self):
        self.collector = MetricsCollector(0.015, 0.075)

    def _mock_response(self, input_tokens: int, output_tokens: int):
        response = MagicMock()
        response.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
        return response

    def test_record_single_metric(self):
        response = self._mock_response(100, 200)
        metrics = self.collector.record("researcher", response, 1.5)

        assert metrics.skill_name == "researcher"
        assert metrics.input_tokens == 100
        assert metrics.output_tokens == 200
        assert metrics.latency_ms == 1500.0
        expected_cost = (100 / 1000 * 0.015) + (200 / 1000 * 0.075)
        assert abs(metrics.cost_usd - expected_cost) < 1e-10

    def test_record_multiple_metrics(self):
        self.collector.record("researcher", self._mock_response(100, 200), 1.0)
        self.collector.record("writer", self._mock_response(300, 500), 2.0)

        assert len(self.collector.history) == 2

    def test_summary_totals(self):
        self.collector.record("researcher", self._mock_response(100, 200), 1.0)
        self.collector.record("writer", self._mock_response(300, 500), 2.0)

        summary = self.collector.summary()
        assert summary["total_input_tokens"] == 400
        assert summary["total_output_tokens"] == 700
        assert summary["total_latency_ms"] == 3000.0
        assert summary["skills_invoked"] == ["researcher", "writer"]
        assert len(summary["per_skill"]) == 2

    def test_summary_empty(self):
        summary = self.collector.summary()
        assert summary["total_input_tokens"] == 0
        assert summary["total_output_tokens"] == 0
        assert summary["total_cost_usd"] == 0.0
        assert summary["skills_invoked"] == []

    def test_cost_calculation(self):
        response = self._mock_response(1000, 1000)
        metrics = self.collector.record("test", response, 1.0)

        expected_cost = (1000 / 1000 * 0.015) + (1000 / 1000 * 0.075)
        assert metrics.cost_usd == expected_cost
        assert metrics.cost_usd == 0.09
