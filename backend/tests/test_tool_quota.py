"""
Tests for ToolQuota (agent/tool_quota.py)
"""

import pytest
from agent.tool_quota import ToolQuota, QuotaInfo, DEFAULT_QUOTAS, GLOBAL_DEFAULT_QUOTA


class TestQuotaInfo:
    """Tests for QuotaInfo dataclass."""

    def test_initial_state(self):
        qi = QuotaInfo(limit=10)
        assert qi.used == 0
        assert qi.remaining == 10
        assert not qi.is_exceeded
        assert qi.usage_pct == 0.0

    def test_fully_used(self):
        qi = QuotaInfo(limit=3, used=3)
        assert qi.remaining == 0
        assert qi.is_exceeded
        assert qi.usage_pct == 100.0

    def test_partially_used(self):
        qi = QuotaInfo(limit=10, used=4)
        assert qi.remaining == 6
        assert not qi.is_exceeded
        assert qi.usage_pct == 40.0

    def test_to_dict(self):
        qi = QuotaInfo(limit=5, used=2)
        d = qi.to_dict()
        assert d["limit"] == 5
        assert d["used"] == 2
        assert d["remaining"] == 3
        assert d["is_exceeded"] is False


class TestToolQuota:
    """Tests for ToolQuota singleton."""

    def setup_method(self):
        ToolQuota.reset()

    def test_singleton_pattern(self):
        q1 = ToolQuota.get_instance()
        q2 = ToolQuota.get_instance()
        assert q1 is q2

    def test_reset(self):
        q1 = ToolQuota.get_instance()
        ToolQuota.reset()
        q2 = ToolQuota.get_instance()
        assert q1 is not q2

    def test_default_quotas_defined(self):
        assert "web_search" in DEFAULT_QUOTAS
        assert "gmail_send" in DEFAULT_QUOTAS
        assert DEFAULT_QUOTAS["gmail_send"] == 5  # Low for safety

    def test_check_within_quota(self):
        quota = ToolQuota.get_instance()
        assert quota.check("web_search") is True

    def test_consume_within_quota(self):
        quota = ToolQuota.get_instance()
        assert quota.consume("web_search") is True

    def test_consume_until_exceeded(self):
        quota = ToolQuota.get_instance(custom_quotas={"web_search": 2})
        ToolQuota.reset()
        quota = ToolQuota.get_instance(custom_quotas={"web_search": 2})
        assert quota.consume("web_search") is True  # 1/2
        assert quota.consume("web_search") is True  # 2/2
        assert quota.consume("web_search") is False  # exceeded

    def test_check_and_consume(self):
        quota = ToolQuota.get_instance(custom_quotas={"test_tool": 1})
        ToolQuota.reset()
        quota = ToolQuota.get_instance(custom_quotas={"test_tool": 1})
        assert quota.check_and_consume("test_tool") is True
        assert quota.check_and_consume("test_tool") is False

    def test_custom_quotas_override(self):
        ToolQuota.reset()
        quota = ToolQuota.get_instance(custom_quotas={"web_search": 3})
        info = quota.get_quota_info("web_search")
        assert info["limit"] == 3

    def test_unknown_tool_uses_global_default(self):
        quota = ToolQuota.get_instance()
        info = quota.get_quota_info("unknown_tool_xyz")
        assert info["limit"] == GLOBAL_DEFAULT_QUOTA

    def test_get_quota_info(self):
        quota = ToolQuota.get_instance()
        quota.consume("web_search")
        info = quota.get_quota_info("web_search")
        assert info["used"] == 1
        assert info["remaining"] == DEFAULT_QUOTAS["web_search"] - 1

    def test_get_summary(self):
        quota = ToolQuota.get_instance()
        quota.consume("web_search")
        summary = quota.get_summary()
        assert "tools" in summary
        assert "web_search" in summary["tools"]
        assert "total_blocked_calls" in summary
        assert "warning_tools" in summary
        assert "session_uptime_seconds" in summary

    def test_blocked_counter(self):
        ToolQuota.reset()
        quota = ToolQuota.get_instance(custom_quotas={"tiny": 1})
        quota.check_and_consume("tiny")  # OK
        quota.check_and_consume("tiny")  # blocked
        quota.check_and_consume("tiny")  # blocked
        summary = quota.get_summary()
        assert summary["total_blocked_calls"] == 2

    def test_warning_tools_in_summary(self):
        ToolQuota.reset()
        quota = ToolQuota.get_instance(custom_quotas={"tight": 5})
        for _ in range(4):  # 80% usage
            quota.consume("tight")
        summary = quota.get_summary()
        assert "tight" in summary["warning_tools"]

    def test_executor_imports_tool_quota(self):
        """Verify executor imports ToolQuota."""
        import agent.function_calling_executor as executor_mod
        source = open(executor_mod.__file__, encoding="utf-8").read()
        assert "from agent.tool_quota import ToolQuota" in source
        assert "quota" in source.lower()
