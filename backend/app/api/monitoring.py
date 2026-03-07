"""
JAWIR OS - Monitoring Dashboard API
=====================================
FastAPI router exposing tool analytics and system health
for the monitoring dashboard (Task 4.3).

Endpoints:
    GET /api/monitoring/health       → System health check
    GET /api/monitoring/analytics    → Full tool analytics summary
    GET /api/monitoring/tools        → Per-tool usage stats
    GET /api/monitoring/tools/{name} → Stats for a specific tool
    POST /api/monitoring/reset       → Reset analytics (dev only)
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings

logger = logging.getLogger("jawir.monitoring")

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

# Track server start time
_server_start_time = time.time()


def _get_analytics():
    """Safely get ToolAnalytics instance (lazy import to avoid circular deps)."""
    try:
        from agent.tool_analytics import ToolAnalytics
        return ToolAnalytics.get_instance()
    except ImportError:
        return None


def _get_cache():
    """Safely get ToolCache instance."""
    try:
        from agent.tool_cache import ToolCache
        return ToolCache.get_instance()
    except ImportError:
        return None


def _get_quota():
    """Safely get ToolQuota instance."""
    try:
        from agent.tool_quota import ToolQuota
        return ToolQuota.get_instance()
    except ImportError:
        return None


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    System health check.
    
    Returns server status, uptime, mode (V1/V2), and basic config.
    """
    uptime = round(time.time() - _server_start_time, 1)
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime,
        "mode": "V2 (Function Calling)" if settings.use_function_calling else "V1 (Legacy)",
        "environment": settings.environment,
        "log_level": settings.log_level,
        "version": "0.1.0",
    }


@router.get("/analytics")
async def get_analytics() -> dict[str, Any]:
    """
    Full tool analytics summary.
    
    Returns session uptime, total queries, total tool calls,
    per-tool stats, and top tools sorted by usage.
    """
    analytics = _get_analytics()
    if analytics is None:
        return {
            "status": "unavailable",
            "message": "ToolAnalytics not available (V1 mode or import error)",
        }
    
    summary = analytics.get_summary()
    summary["status"] = "ok"
    summary["fc_mode_enabled"] = settings.use_function_calling
    
    return summary


@router.get("/tools")
async def get_all_tool_stats() -> dict[str, Any]:
    """
    Per-tool usage statistics.
    
    Returns stats for every tool that has been called at least once.
    """
    analytics = _get_analytics()
    if analytics is None:
        return {"status": "unavailable", "tools": {}}
    
    summary = analytics.get_summary()
    
    return {
        "status": "ok",
        "total_tools_used": len(summary["tools"]),
        "tools": summary["tools"],
    }


@router.get("/tools/{tool_name}")
async def get_tool_stats(tool_name: str) -> dict[str, Any]:
    """
    Stats for a specific tool.
    
    Args:
        tool_name: Name of the tool (e.g., 'web_search', 'gmail_send')
    """
    analytics = _get_analytics()
    if analytics is None:
        raise HTTPException(
            status_code=503,
            detail="ToolAnalytics not available",
        )
    
    stats = analytics.get_tool_stats(tool_name)
    
    # Check if tool has been used
    if stats["total_calls"] == 0:
        return {
            "status": "ok",
            "tool_name": tool_name,
            "message": f"Tool '{tool_name}' belum pernah dipanggil dalam session ini",
            "stats": stats,
        }
    
    return {
        "status": "ok",
        "tool_name": tool_name,
        "stats": stats,
    }


@router.get("/top-tools")
async def get_top_tools(limit: int = 10) -> dict[str, Any]:
    """
    Top tools sorted by usage count.
    
    Args:
        limit: Max number of tools to return (default 10)
    """
    analytics = _get_analytics()
    if analytics is None:
        return {"status": "unavailable", "top_tools": []}
    
    summary = analytics.get_summary()
    
    return {
        "status": "ok",
        "top_tools": summary["top_tools"][:limit],
    }


@router.post("/reset")
async def reset_analytics() -> dict[str, Any]:
    """
    Reset all analytics data.
    
    Only available in development environment.
    """
    if not settings.is_development:
        raise HTTPException(
            status_code=403,
            detail="Analytics reset hanya tersedia di environment development",
        )
    
    analytics = _get_analytics()
    if analytics is None:
        raise HTTPException(
            status_code=503,
            detail="ToolAnalytics not available",
        )
    
    from agent.tool_analytics import ToolAnalytics
    ToolAnalytics.reset()
    
    logger.info("📊 Analytics reset via monitoring API")
    
    return {
        "status": "ok",
        "message": "Analytics data berhasil direset",
    }


@router.get("/summary")
async def get_dashboard_summary() -> dict[str, Any]:
    """
    Dashboard summary combining health + analytics for a single overview.
    
    Designed for frontend dashboard widget consumption.
    """
    uptime = round(time.time() - _server_start_time, 1)
    
    dashboard = {
        "server": {
            "status": "healthy",
            "uptime_seconds": uptime,
            "mode": "V2 (FC)" if settings.use_function_calling else "V1 (Legacy)",
            "environment": settings.environment,
        },
        "analytics": None,
        "cache": None,
        "quota": None,
    }
    
    analytics = _get_analytics()
    if analytics:
        summary = analytics.get_summary()
        dashboard["analytics"] = {
            "session_uptime_seconds": summary["session_uptime_seconds"],
            "total_queries": summary["total_queries"],
            "total_tool_calls": summary["total_tool_calls"],
            "total_errors": summary["total_errors"],
            "overall_success_rate_pct": summary["overall_success_rate_pct"],
            "top_tools": summary["top_tools"][:5],
        }
    
    cache = _get_cache()
    if cache:
        dashboard["cache"] = cache.get_stats()
    
    quota_mgr = _get_quota()
    if quota_mgr:
        quota_summary = quota_mgr.get_summary()
        dashboard["quota"] = {
            "total_blocked_calls": quota_summary["total_blocked_calls"],
            "warning_tools": quota_summary["warning_tools"],
        }
    
    return dashboard
