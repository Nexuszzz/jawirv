"""
JAWIR OS - Unit Tests for Tool Analytics
==========================================
Task 5.4: Per-tool usage analytics.

Run:
    cd backend
    python -m pytest tests/test_analytics.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from agent.tool_analytics import ToolAnalytics, ToolStats


class TestToolStats:
    """Test ToolStats dataclass."""

    def test_default_values(self):
        stats = ToolStats()
        assert stats.total_calls == 0
        assert stats.success_count == 0
        assert stats.error_count == 0
        assert stats.avg_duration == 0.0
        assert stats.success_rate == 0.0

    def test_avg_duration(self):
        stats = ToolStats(total_calls=3, total_duration=6.0)
        assert stats.avg_duration == 2.0

    def test_success_rate(self):
        stats = ToolStats(total_calls=10, success_count=8, error_count=2)
        assert stats.success_rate == 80.0

    def test_to_dict(self):
        stats = ToolStats(total_calls=5, success_count=4, error_count=1, total_duration=10.0)
        d = stats.to_dict()
        assert d["total_calls"] == 5
        assert d["success_rate_pct"] == 80.0
        assert d["avg_duration_sec"] == 2.0
        assert "last_error" in d


class TestToolAnalytics:
    """Test ToolAnalytics singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        ToolAnalytics.reset()

    def test_singleton_pattern(self):
        a = ToolAnalytics.get_instance()
        b = ToolAnalytics.get_instance()
        assert a is b

    def test_reset(self):
        a = ToolAnalytics.get_instance()
        ToolAnalytics.reset()
        b = ToolAnalytics.get_instance()
        assert a is not b

    def test_record_success(self):
        analytics = ToolAnalytics.get_instance()
        analytics.record("web_search", success=True, duration=1.5)
        stats = analytics.get_tool_stats("web_search")
        assert stats["total_calls"] == 1
        assert stats["success_count"] == 1
        assert stats["error_count"] == 0
        assert stats["success_rate_pct"] == 100.0

    def test_record_error(self):
        analytics = ToolAnalytics.get_instance()
        analytics.record("web_search", success=False, error_msg="timeout")
        stats = analytics.get_tool_stats("web_search")
        assert stats["total_calls"] == 1
        assert stats["error_count"] == 1
        assert stats["last_error"] == "timeout"

    def test_record_multiple(self):
        analytics = ToolAnalytics.get_instance()
        analytics.record("web_search", success=True, duration=1.0)
        analytics.record("web_search", success=True, duration=2.0)
        analytics.record("web_search", success=False, duration=0.5, error_msg="err")
        stats = analytics.get_tool_stats("web_search")
        assert stats["total_calls"] == 3
        assert stats["success_count"] == 2
        assert stats["error_count"] == 1
        assert stats["avg_duration_sec"] == pytest.approx(1.167, abs=0.01)

    def test_record_query(self):
        analytics = ToolAnalytics.get_instance()
        analytics.record_query()
        analytics.record_query()
        summary = analytics.get_summary()
        assert summary["total_queries"] == 2

    def test_get_summary(self):
        analytics = ToolAnalytics.get_instance()
        analytics.record("web_search", success=True, duration=1.0)
        analytics.record("open_app", success=True, duration=0.5)
        analytics.record("web_search", success=True, duration=2.0)
        summary = analytics.get_summary()
        assert summary["total_tool_calls"] == 3
        assert summary["total_errors"] == 0
        assert summary["overall_success_rate_pct"] == 100.0
        assert len(summary["tools"]) == 2
        assert len(summary["top_tools"]) == 2
        # web_search should be first (2 calls > 1 call)
        assert summary["top_tools"][0]["name"] == "web_search"
        assert summary["top_tools"][0]["calls"] == 2

    def test_min_max_duration(self):
        analytics = ToolAnalytics.get_instance()
        analytics.record("test_tool", success=True, duration=3.0)
        analytics.record("test_tool", success=True, duration=1.0)
        analytics.record("test_tool", success=True, duration=5.0)
        stats = analytics.get_tool_stats("test_tool")
        assert stats["min_duration_sec"] == 1.0
        assert stats["max_duration_sec"] == 5.0

    def test_separate_tool_tracking(self):
        analytics = ToolAnalytics.get_instance()
        analytics.record("web_search", success=True)
        analytics.record("open_app", success=False, error_msg="not found")
        ws = analytics.get_tool_stats("web_search")
        oa = analytics.get_tool_stats("open_app")
        assert ws["success_count"] == 1
        assert ws["error_count"] == 0
        assert oa["success_count"] == 0
        assert oa["error_count"] == 1

    def test_executor_imports_analytics(self):
        """Executor should import and use ToolAnalytics."""
        from agent.function_calling_executor import FunctionCallingExecutor
        import inspect
        source = inspect.getsource(FunctionCallingExecutor.execute)
        assert "ToolAnalytics" in source, "Executor should use ToolAnalytics"
        assert "analytics.record" in source, "Executor should record analytics"
