"""
JAWIR OS - Tool Usage Quota
==============================
Per-tool usage quota to prevent excessive API calls.
Protects against:
- Infinite loops calling web_search repeatedly
- Accidental mass email sending
- Exceeding external API rate limits

Usage:
    from agent.tool_quota import ToolQuota
    quota = ToolQuota.get_instance()
    
    if not quota.check(tool_name):
        return "Quota exceeded for {tool_name}"
    
    quota.consume(tool_name)
    # ... execute tool ...
"""

import logging
import time
from typing import Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("jawir.agent.tool_quota")


# Default quotas per tool per session
# Higher for read-only tools, lower for mutating tools
DEFAULT_QUOTAS: dict[str, int] = {
    "web_search": 15,               # 15 searches per session
    "gmail_search": 10,             # 10 email searches
    "gmail_send": 5,                # 5 emails per session (safety!)
    "drive_search": 10,             # 10 drive searches
    "drive_list": 10,               # 10 drive listings
    "calendar_list_events": 10,     # 10 calendar queries
    "calendar_create_event": 5,     # 5 events per session
    "generate_kicad_schematic": 10, # 10 schematics
    "run_python_code": 20,          # 20 code executions
    "open_app": 10,                 # 10 app opens
    "open_url": 10,                 # 10 URL opens
    "close_app": 10,                # 10 app closes
}

# Global default for tools not in DEFAULT_QUOTAS
GLOBAL_DEFAULT_QUOTA = 20


@dataclass
class QuotaInfo:
    """Quota information for a single tool."""
    limit: int
    used: int = 0
    
    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)
    
    @property
    def is_exceeded(self) -> bool:
        return self.used >= self.limit
    
    @property
    def usage_pct(self) -> float:
        if self.limit == 0:
            return 100.0
        return round(self.used / self.limit * 100, 1)
    
    def to_dict(self) -> dict:
        return {
            "limit": self.limit,
            "used": self.used,
            "remaining": self.remaining,
            "is_exceeded": self.is_exceeded,
            "usage_pct": self.usage_pct,
        }


class ToolQuota:
    """
    Per-tool usage quota manager.
    
    Singleton pattern. Resets on server restart.
    Each tool has a configurable maximum number of calls per session.
    """
    
    _instance: Optional["ToolQuota"] = None
    
    def __init__(self, custom_quotas: Optional[dict[str, int]] = None):
        """
        Args:
            custom_quotas: Override default quotas. Keys = tool names, values = max calls.
        """
        self._quotas: dict[str, QuotaInfo] = {}
        self._custom_quotas = custom_quotas or {}
        self._total_blocked = 0
        self._session_start = time.time()
    
    @classmethod
    def get_instance(cls, custom_quotas: Optional[dict[str, int]] = None) -> "ToolQuota":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls(custom_quotas=custom_quotas)
            logger.info("🔒 ToolQuota initialized")
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None
    
    def _get_limit(self, tool_name: str) -> int:
        """Get the quota limit for a tool."""
        # Custom overrides > defaults > global default
        if tool_name in self._custom_quotas:
            return self._custom_quotas[tool_name]
        return DEFAULT_QUOTAS.get(tool_name, GLOBAL_DEFAULT_QUOTA)
    
    def _ensure_quota(self, tool_name: str) -> QuotaInfo:
        """Ensure a QuotaInfo exists for the tool."""
        if tool_name not in self._quotas:
            self._quotas[tool_name] = QuotaInfo(limit=self._get_limit(tool_name))
        return self._quotas[tool_name]
    
    def check(self, tool_name: str) -> bool:
        """
        Check if a tool call is allowed (within quota).
        
        Returns True if allowed, False if quota exceeded.
        Does NOT consume quota — call consume() separately.
        """
        quota = self._ensure_quota(tool_name)
        return not quota.is_exceeded
    
    def consume(self, tool_name: str) -> bool:
        """
        Consume one unit of quota for a tool.
        
        Returns True if consumed, False if quota was already exceeded.
        """
        quota = self._ensure_quota(tool_name)
        
        if quota.is_exceeded:
            self._total_blocked += 1
            logger.warning(
                f"🔒 Quota EXCEEDED for {tool_name}: "
                f"{quota.used}/{quota.limit} (blocked)"
            )
            return False
        
        quota.used += 1
        
        # Warn when approaching limit
        if quota.remaining <= 2 and quota.remaining > 0:
            logger.warning(
                f"⚠️ Quota WARNING for {tool_name}: "
                f"{quota.used}/{quota.limit} (only {quota.remaining} remaining)"
            )
        elif quota.is_exceeded:
            logger.warning(
                f"🔒 Quota REACHED for {tool_name}: "
                f"{quota.used}/{quota.limit}"
            )
        
        return True
    
    def check_and_consume(self, tool_name: str) -> bool:
        """
        Check and consume in one call. Returns True if allowed.
        
        Convenience method combining check() + consume().
        """
        if not self.check(tool_name):
            self._total_blocked += 1
            return False
        return self.consume(tool_name)
    
    def get_quota_info(self, tool_name: str) -> dict:
        """Get quota info for a specific tool."""
        quota = self._ensure_quota(tool_name)
        return quota.to_dict()
    
    def get_summary(self) -> dict[str, Any]:
        """
        Get full quota summary.
        
        Returns all tools' quotas and their usage.
        """
        uptime = round(time.time() - self._session_start, 1)
        
        # Include all configured tools (even unused ones)
        all_tools = set(DEFAULT_QUOTAS.keys()) | set(self._custom_quotas.keys()) | set(self._quotas.keys())
        
        tools_info = {}
        for tool_name in sorted(all_tools):
            quota = self._ensure_quota(tool_name)
            tools_info[tool_name] = quota.to_dict()
        
        # Tools at or near limit
        warning_tools = [
            name for name, info in tools_info.items()
            if info["usage_pct"] >= 80 and info["used"] > 0
        ]
        
        return {
            "session_uptime_seconds": uptime,
            "total_blocked_calls": self._total_blocked,
            "tools": tools_info,
            "warning_tools": warning_tools,
        }
