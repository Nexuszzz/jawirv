"""
Tests for Monitoring Dashboard API (app/api/monitoring.py)
"""

import pytest


class TestMonitoringModule:
    """Tests for monitoring module structure and imports."""

    def test_module_imports(self):
        """Verify monitoring module can be imported."""
        from app.api import monitoring
        assert hasattr(monitoring, "router")

    def test_router_has_prefix(self):
        """Verify router has the correct prefix."""
        from app.api.monitoring import router
        assert router.prefix == "/api/monitoring"

    def test_router_has_tag(self):
        """Verify router has monitoring tag."""
        from app.api.monitoring import router
        assert "monitoring" in router.tags

    def test_router_routes_defined(self):
        """Verify all expected routes exist."""
        from app.api.monitoring import router
        route_paths = [r.path for r in router.routes]
        assert "/api/monitoring/health" in route_paths
        assert "/api/monitoring/analytics" in route_paths
        assert "/api/monitoring/tools" in route_paths
        assert "/api/monitoring/tools/{tool_name}" in route_paths
        assert "/api/monitoring/top-tools" in route_paths
        assert "/api/monitoring/reset" in route_paths
        assert "/api/monitoring/summary" in route_paths

    def test_router_registered_in_main(self):
        """Verify monitoring router is included in main app."""
        import os
        main_path = os.path.join(os.path.dirname(__file__), "..", "app", "main.py")
        source = open(main_path, encoding="utf-8").read()
        assert "from app.api.monitoring import router as monitoring_router" in source
        assert "app.include_router(monitoring_router)" in source

    def test_health_endpoint_exists(self):
        """Verify health check endpoint function exists."""
        from app.api.monitoring import health_check
        assert callable(health_check)

    def test_analytics_endpoint_exists(self):
        """Verify analytics endpoint function exists."""
        from app.api.monitoring import get_analytics
        assert callable(get_analytics)

    def test_summary_endpoint_exists(self):
        """Verify summary endpoint function exists."""
        from app.api.monitoring import get_dashboard_summary
        assert callable(get_dashboard_summary)

    def test_get_analytics_helper_callable(self):
        """Verify _get_analytics helper works."""
        from app.api.monitoring import _get_analytics
        analytics = _get_analytics()
        # Should return ToolAnalytics instance or None
        if analytics is not None:
            assert hasattr(analytics, "get_summary")

    def test_get_cache_helper_callable(self):
        """Verify _get_cache helper works."""
        from app.api.monitoring import _get_cache
        cache = _get_cache()
        if cache is not None:
            assert hasattr(cache, "get_stats")

    def test_get_quota_helper_callable(self):
        """Verify _get_quota helper works."""
        from app.api.monitoring import _get_quota
        quota = _get_quota()
        if quota is not None:
            assert hasattr(quota, "get_summary")
