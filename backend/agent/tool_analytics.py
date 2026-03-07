"""
JAWIR OS - Tool Analytics
===========================
Per-tool usage analytics for monitoring and optimization.
Tracks tool usage counts, success rates, average execution times.

Usage:
    from agent.tool_analytics import ToolAnalytics
    analytics = ToolAnalytics.get_instance()
    analytics.record("web_search", success=True, duration=1.23)
    analytics.get_summary()
"""

import logging
import time
from collections import defaultdict
from typing import Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("jawir.agent.tool_analytics")


@dataclass
class ToolStats:
    """Statistics for a single tool."""
    total_calls: int = 0
    success_count: int = 0
    error_count: int = 0
    total_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0
    last_called: Optional[float] = None
    last_error: Optional[str] = None
    
    @property
    def avg_duration(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return round(self.total_duration / self.total_calls, 3)
    
    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return round(self.success_count / self.total_calls * 100, 1)
    
    def to_dict(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate_pct": self.success_rate,
            "avg_duration_sec": self.avg_duration,
            "min_duration_sec": round(self.min_duration, 3) if self.min_duration != float("inf") else 0,
            "max_duration_sec": round(self.max_duration, 3),
            "last_called": self.last_called,
            "last_error": self.last_error,
        }


class ToolAnalytics:
    """
    Singleton analytics tracker for tool usage.
    
    Thread-safe for async usage. Stores in-memory only.
    Reset on server restart.
    """
    
    _instance: Optional["ToolAnalytics"] = None
    
    def __init__(self):
        self._stats: dict[str, ToolStats] = defaultdict(ToolStats)
        self._session_start = time.time()
        self._total_queries = 0
    
    @classmethod
    def get_instance(cls) -> "ToolAnalytics":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            logger.info("📊 ToolAnalytics initialized")
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None
    
    def record(
        self,
        tool_name: str,
        success: bool = True,
        duration: float = 0.0,
        error_msg: Optional[str] = None,
    ) -> None:
        """
        Record a tool execution.
        
        Args:
            tool_name: Name of the tool
            success: Whether execution succeeded
            duration: Execution time in seconds
            error_msg: Error message if failed
        """
        stats = self._stats[tool_name]
        stats.total_calls += 1
        stats.total_duration += duration
        stats.last_called = time.time()
        
        if duration < stats.min_duration:
            stats.min_duration = duration
        if duration > stats.max_duration:
            stats.max_duration = duration
        
        if success:
            stats.success_count += 1
        else:
            stats.error_count += 1
            stats.last_error = error_msg
        
        logger.debug(
            f"📊 Recorded: {tool_name} ({'✅' if success else '❌'}) "
            f"duration={duration:.3f}s"
        )
    
    def record_query(self) -> None:
        """Increment total query counter."""
        self._total_queries += 1
    
    def get_tool_stats(self, tool_name: str) -> dict:
        """Get stats for a specific tool."""
        return self._stats[tool_name].to_dict()
    
    def get_summary(self) -> dict[str, Any]:
        """
        Get full analytics summary.
        
        Returns:
            Dictionary with:
                - session_uptime_seconds: Time since analytics started
                - total_queries: Number of user queries processed
                - total_tool_calls: Total tool executions
                - total_errors: Total failed executions
                - overall_success_rate_pct: Overall success rate
                - tools: Per-tool statistics
                - top_tools: Sorted by usage (descending)
        """
        uptime = round(time.time() - self._session_start, 1)
        total_calls = sum(s.total_calls for s in self._stats.values())
        total_errors = sum(s.error_count for s in self._stats.values())
        
        overall_success = 0.0
        if total_calls > 0:
            overall_success = round((total_calls - total_errors) / total_calls * 100, 1)
        
        # Sort by usage count
        top_tools = sorted(
            self._stats.items(),
            key=lambda x: x[1].total_calls,
            reverse=True,
        )
        
        return {
            "session_uptime_seconds": uptime,
            "total_queries": self._total_queries,
            "total_tool_calls": total_calls,
            "total_errors": total_errors,
            "overall_success_rate_pct": overall_success,
            "tools": {name: stats.to_dict() for name, stats in self._stats.items()},
            "top_tools": [
                {"name": name, "calls": stats.total_calls, "success_rate": stats.success_rate}
                for name, stats in top_tools
            ],
        }
    
    def log_summary(self) -> None:
        """Log a human-readable summary."""
        summary = self.get_summary()
        logger.info(
            f"📊 Analytics Summary: "
            f"queries={summary['total_queries']}, "
            f"tool_calls={summary['total_tool_calls']}, "
            f"errors={summary['total_errors']}, "
            f"success_rate={summary['overall_success_rate_pct']}%, "
            f"uptime={summary['session_uptime_seconds']}s"
        )
        for entry in summary["top_tools"]:
            logger.info(
                f"  🔧 {entry['name']}: "
                f"{entry['calls']} calls, "
                f"{entry['success_rate']}% success"
            )
