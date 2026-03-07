"""
Tests for ToolCache (agent/tool_cache.py)
"""

import time
import pytest
from agent.tool_cache import ToolCache, CacheEntry, CACHEABLE_TOOLS, DEFAULT_TTLS


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_not_expired(self):
        entry = CacheEntry(value="test", created_at=time.time(), ttl=60)
        assert not entry.is_expired

    def test_expired(self):
        entry = CacheEntry(value="test", created_at=time.time() - 100, ttl=60)
        assert entry.is_expired

    def test_age_seconds(self):
        entry = CacheEntry(value="test", created_at=time.time() - 5, ttl=60)
        assert entry.age_seconds >= 4.9  # Allow small floating point diff

    def test_hit_count_default(self):
        entry = CacheEntry(value="data", created_at=time.time(), ttl=60)
        assert entry.hit_count == 0


class TestToolCache:
    """Tests for ToolCache singleton."""

    def setup_method(self):
        ToolCache.reset()

    def test_singleton_pattern(self):
        c1 = ToolCache.get_instance()
        c2 = ToolCache.get_instance()
        assert c1 is c2

    def test_reset(self):
        c1 = ToolCache.get_instance()
        ToolCache.reset()
        c2 = ToolCache.get_instance()
        assert c1 is not c2

    def test_cacheable_tools_defined(self):
        assert "web_search" in CACHEABLE_TOOLS
        assert "gmail_search" in CACHEABLE_TOOLS
        assert "drive_search" in CACHEABLE_TOOLS

    def test_non_cacheable_tools(self):
        assert "gmail_send" not in CACHEABLE_TOOLS
        assert "open_app" not in CACHEABLE_TOOLS
        assert "calendar_create_event" not in CACHEABLE_TOOLS

    def test_is_cacheable(self):
        cache = ToolCache.get_instance()
        assert cache.is_cacheable("web_search") is True
        assert cache.is_cacheable("gmail_send") is False

    def test_set_and_get_cacheable(self):
        cache = ToolCache.get_instance()
        args = {"query": "python tutorial"}
        assert cache.set("web_search", args, "result123") is True
        assert cache.get("web_search", args) == "result123"

    def test_set_non_cacheable_returns_false(self):
        cache = ToolCache.get_instance()
        assert cache.set("gmail_send", {"to": "x"}, "sent") is False

    def test_get_non_cacheable_returns_none(self):
        cache = ToolCache.get_instance()
        assert cache.get("gmail_send", {"to": "x"}) is None

    def test_cache_miss_returns_none(self):
        cache = ToolCache.get_instance()
        assert cache.get("web_search", {"query": "nonexistent"}) is None

    def test_cache_expiry(self):
        cache = ToolCache.get_instance()
        args = {"query": "test"}
        # Set with very short TTL
        cache.set("web_search", args, "data", ttl=0.01)
        time.sleep(0.02)
        assert cache.get("web_search", args) is None

    def test_same_args_different_order(self):
        cache = ToolCache.get_instance()
        args1 = {"query": "test", "max_results": 5}
        args2 = {"max_results": 5, "query": "test"}
        cache.set("web_search", args1, "result")
        # Same args in different order should hit cache
        assert cache.get("web_search", args2) == "result"

    def test_different_args_different_keys(self):
        cache = ToolCache.get_instance()
        cache.set("web_search", {"query": "a"}, "result_a")
        cache.set("web_search", {"query": "b"}, "result_b")
        assert cache.get("web_search", {"query": "a"}) == "result_a"
        assert cache.get("web_search", {"query": "b"}) == "result_b"

    def test_invalidate_specific(self):
        cache = ToolCache.get_instance()
        args = {"query": "test"}
        cache.set("web_search", args, "data")
        assert cache.invalidate("web_search", args) == 1
        assert cache.get("web_search", args) is None

    def test_invalidate_all_for_tool(self):
        cache = ToolCache.get_instance()
        cache.set("web_search", {"query": "a"}, "1")
        cache.set("web_search", {"query": "b"}, "2")
        assert cache.invalidate("web_search") == 2

    def test_clear(self):
        cache = ToolCache.get_instance()
        cache.set("web_search", {"query": "x"}, "v")
        count = cache.clear()
        assert count == 1
        assert cache.get("web_search", {"query": "x"}) is None

    def test_max_entries_eviction(self):
        cache = ToolCache.get_instance(max_entries=3)
        ToolCache.reset()
        cache = ToolCache.get_instance(max_entries=3)
        for i in range(4):
            cache.set("web_search", {"query": f"q{i}"}, f"r{i}")
        # Should have evicted the oldest (q0)
        stats = cache.get_stats()
        assert stats["size"] <= 3

    def test_get_stats(self):
        cache = ToolCache.get_instance()
        cache.set("web_search", {"query": "test"}, "data")
        cache.get("web_search", {"query": "test"})  # hit
        cache.get("web_search", {"query": "miss"})  # miss
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate_pct"] == 50.0
        assert "web_search" in stats["entries_by_tool"]

    def test_cleanup_expired(self):
        cache = ToolCache.get_instance()
        cache.set("web_search", {"query": "old"}, "data", ttl=0.01)
        time.sleep(0.02)
        removed = cache.cleanup_expired()
        assert removed == 1

    def test_default_ttls_defined(self):
        assert DEFAULT_TTLS["web_search"] == 300
        assert DEFAULT_TTLS["gmail_search"] == 120

    def test_executor_imports_tool_cache(self):
        """Verify executor imports ToolCache."""
        import agent.function_calling_executor as executor_mod
        source = open(executor_mod.__file__, encoding="utf-8").read()
        assert "from agent.tool_cache import ToolCache" in source
        assert "cache.get(" in source or "cached_result" in source
