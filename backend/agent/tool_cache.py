"""
JAWIR OS - Tool Result Cache
==============================
TTL-based in-memory cache for tool results.
Reduces redundant API calls (e.g., repeated web searches with same query).

Only caches idempotent tools (tools that return same result for same input).
Mutable tools (gmail_send, calendar_create_event, open_app, etc.) are excluded.

Usage:
    from agent.tool_cache import ToolCache
    cache = ToolCache.get_instance()
    
    # Check cache before executing
    cached = cache.get("web_search", {"query": "python tutorial"})
    if cached is not None:
        return cached  # Cache hit
    
    # Execute tool, then cache result
    result = await tool.ainvoke(args)
    cache.set("web_search", {"query": "python tutorial"}, result, ttl=300)
"""

import hashlib
import json
import logging
import time
from typing import Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("jawir.agent.tool_cache")

# Tools whose results are safe to cache (idempotent/read-only)
CACHEABLE_TOOLS = frozenset({
    "web_search",
    "gmail_search",
    "drive_search",
    "drive_list",
    "calendar_list_events",
})

# Default TTL per tool (in seconds)
DEFAULT_TTLS = {
    "web_search": 300,         # 5 minutes — search results change
    "gmail_search": 120,       # 2 minutes — new emails arrive
    "drive_search": 300,       # 5 minutes
    "drive_list": 300,         # 5 minutes
    "calendar_list_events": 60,  # 1 minute — schedule changes
}

# Global default TTL if tool not in DEFAULT_TTLS
FALLBACK_TTL = 300  # 5 minutes


@dataclass
class CacheEntry:
    """Single cache entry with expiration."""
    value: Any
    created_at: float
    ttl: float
    hit_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl
    
    @property
    def age_seconds(self) -> float:
        return round(time.time() - self.created_at, 1)


class ToolCache:
    """
    TTL-based in-memory cache for tool results.
    
    Singleton pattern. Thread-safe for async usage.
    Stores results keyed by (tool_name, args_hash).
    """
    
    _instance: Optional["ToolCache"] = None
    
    def __init__(self, max_entries: int = 100):
        """
        Args:
            max_entries: Maximum cache entries before eviction (LRU-ish)
        """
        self._cache: dict[str, CacheEntry] = {}
        self._max_entries = max_entries
        self._hits = 0
        self._misses = 0
    
    @classmethod
    def get_instance(cls, max_entries: int = 100) -> "ToolCache":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls(max_entries=max_entries)
            logger.info(f"🗄️ ToolCache initialized (max_entries={max_entries})")
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None
    
    @staticmethod
    def _make_key(tool_name: str, args: dict) -> str:
        """
        Create a deterministic cache key from tool name and arguments.
        
        Sorts args keys to ensure same args in different order → same key.
        """
        args_str = json.dumps(args, sort_keys=True, default=str)
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:12]
        return f"{tool_name}:{args_hash}"
    
    @staticmethod
    def is_cacheable(tool_name: str) -> bool:
        """Check if a tool's results can be cached."""
        return tool_name in CACHEABLE_TOOLS
    
    def get(self, tool_name: str, args: dict) -> Optional[Any]:
        """
        Get a cached result.
        
        Returns None on miss or expired entry.
        """
        if not self.is_cacheable(tool_name):
            return None
        
        key = self._make_key(tool_name, args)
        entry = self._cache.get(key)
        
        if entry is None:
            self._misses += 1
            return None
        
        if entry.is_expired:
            # Clean up expired entry
            del self._cache[key]
            self._misses += 1
            logger.debug(f"🗄️ Cache expired: {tool_name} (age={entry.age_seconds}s)")
            return None
        
        # Cache hit
        entry.hit_count += 1
        self._hits += 1
        logger.debug(f"🗄️ Cache HIT: {tool_name} (age={entry.age_seconds}s, hits={entry.hit_count})")
        return entry.value
    
    def set(
        self,
        tool_name: str,
        args: dict,
        value: Any,
        ttl: Optional[float] = None,
    ) -> bool:
        """
        Cache a tool result.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments (used for cache key)
            value: Result to cache
            ttl: Time-to-live in seconds (None = use default for tool)
            
        Returns:
            True if cached, False if tool not cacheable
        """
        if not self.is_cacheable(tool_name):
            return False
        
        # Evict if at capacity
        if len(self._cache) >= self._max_entries:
            self._evict_oldest()
        
        if ttl is None:
            ttl = DEFAULT_TTLS.get(tool_name, FALLBACK_TTL)
        
        key = self._make_key(tool_name, args)
        self._cache[key] = CacheEntry(
            value=value,
            created_at=time.time(),
            ttl=ttl,
        )
        
        logger.debug(f"🗄️ Cached: {tool_name} (ttl={ttl}s)")
        return True
    
    def invalidate(self, tool_name: str, args: Optional[dict] = None) -> int:
        """
        Invalidate cache entries.
        
        Args:
            tool_name: Tool name to invalidate
            args: If provided, invalidate only this specific entry.
                  If None, invalidate ALL entries for this tool.
                  
        Returns:
            Number of entries invalidated.
        """
        if args is not None:
            key = self._make_key(tool_name, args)
            if key in self._cache:
                del self._cache[key]
                return 1
            return 0
        
        # Invalidate all entries for this tool
        prefix = f"{tool_name}:"
        keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
        for k in keys_to_remove:
            del self._cache[k]
        
        if keys_to_remove:
            logger.info(f"🗄️ Invalidated {len(keys_to_remove)} entries for {tool_name}")
        
        return len(keys_to_remove)
    
    def clear(self) -> int:
        """Clear all cache entries. Returns count of cleared entries."""
        count = len(self._cache)
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info(f"🗄️ Cache cleared ({count} entries)")
        return count
    
    def _evict_oldest(self) -> None:
        """Evict the oldest entry when cache is full."""
        if not self._cache:
            return
        
        oldest_key = min(self._cache, key=lambda k: self._cache[k].created_at)
        del self._cache[oldest_key]
        logger.debug(f"🗄️ Evicted oldest entry: {oldest_key}")
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        expired = [k for k, v in self._cache.items() if v.is_expired]
        for k in expired:
            del self._cache[k]
        if expired:
            logger.debug(f"🗄️ Cleaned up {len(expired)} expired entries")
        return len(expired)
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with hits, misses, hit_rate, size, etc.
        """
        total_requests = self._hits + self._misses
        hit_rate = 0.0
        if total_requests > 0:
            hit_rate = round(self._hits / total_requests * 100, 1)
        
        # Count entries by tool
        tool_counts: dict[str, int] = {}
        for key in self._cache:
            tool_name = key.split(":")[0]
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
        
        return {
            "size": len(self._cache),
            "max_entries": self._max_entries,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_pct": hit_rate,
            "entries_by_tool": tool_counts,
            "cacheable_tools": list(CACHEABLE_TOOLS),
        }
