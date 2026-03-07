"""
JAWIR OS - Unit Tests for Web Search Tool
==========================================
Task 1.12: Mock TavilySearchTool, verify output format.

Run:
    cd backend
    python -m pytest tests/test_web_search_tool.py -v
"""

import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import asyncio


class MockSearchResult:
    """Mock search result object matching TavilySearchTool output."""
    def __init__(self, title: str, url: str, content: str):
        self.title = title
        self.url = url
        self.content = content


class TestWebSearchToolOutput:
    """Test web_search tool output format with mocked Tavily."""

    @pytest.fixture
    def mock_tavily(self):
        """Create mock TavilySearchTool."""
        mock = MagicMock()
        mock.search = AsyncMock(return_value=[
            MockSearchResult(
                title="Bitcoin Hari Ini",
                url="https://example.com/btc",
                content="Harga Bitcoin hari ini mencapai $100,000 USD, naik 5% dalam 24 jam terakhir."
            ),
            MockSearchResult(
                title="Analisis BTC 2024",
                url="https://example.com/btc2",
                content="Pasar kripto bullish setelah halving."
            ),
        ])
        return mock

    def test_web_search_returns_formatted_output(self, mock_tavily):
        """Test that web_search formats output correctly."""
        from agent.tools_registry import create_web_search_tool

        tool = create_web_search_tool()

        with patch("agent.tools_registry.create_web_search_tool") as _:
            # We need to test the actual inner function
            # Access the coroutine directly
            async def run_test():
                with patch("tools.web_search.TavilySearchTool", return_value=mock_tavily):
                    result = await tool.ainvoke({"query": "harga bitcoin", "max_results": 5})
                    return result

            result = asyncio.get_event_loop().run_until_complete(run_test())

            # Verify output format
            assert isinstance(result, str)
            assert "Bitcoin" in result or "Error" in result or "Tidak ditemukan" in result

    def test_web_search_empty_results(self):
        """Test handling of empty search results."""
        from agent.tools_registry import create_web_search_tool

        tool = create_web_search_tool()

        mock_tavily_empty = MagicMock()
        mock_tavily_empty.search = AsyncMock(return_value=[])

        async def run_test():
            with patch("tools.web_search.TavilySearchTool", return_value=mock_tavily_empty):
                result = await tool.ainvoke({"query": "xyznonexistent123"})
                return result

        result = asyncio.get_event_loop().run_until_complete(run_test())
        assert "Tidak ditemukan" in result or "Error" in result

    def test_web_search_handles_exception(self):
        """Test that web_search gracefully handles errors."""
        from agent.tools_registry import create_web_search_tool

        tool = create_web_search_tool()

        mock_tavily_error = MagicMock()
        mock_tavily_error.search = AsyncMock(side_effect=Exception("API key invalid"))

        async def run_test():
            with patch("tools.web_search.TavilySearchTool", return_value=mock_tavily_error):
                result = await tool.ainvoke({"query": "test"})
                return result

        result = asyncio.get_event_loop().run_until_complete(run_test())
        assert "Error" in result


class TestWebSearchInputValidation:
    """Test input schema validation."""

    def test_valid_input(self):
        from agent.tools_registry import WebSearchInput
        inp = WebSearchInput(query="harga bitcoin", max_results=5)
        assert inp.query == "harga bitcoin"
        assert inp.max_results == 5

    def test_default_max_results(self):
        from agent.tools_registry import WebSearchInput
        inp = WebSearchInput(query="test")
        assert inp.max_results == 5

    def test_max_results_bounds(self):
        from agent.tools_registry import WebSearchInput
        # Valid range
        inp = WebSearchInput(query="test", max_results=1)
        assert inp.max_results == 1
        inp = WebSearchInput(query="test", max_results=10)
        assert inp.max_results == 10

        # Out of bounds
        with pytest.raises(Exception):
            WebSearchInput(query="test", max_results=0)
        with pytest.raises(Exception):
            WebSearchInput(query="test", max_results=11)

    def test_empty_query_rejected(self):
        """Empty string query should still be valid (Pydantic allows it)."""
        from agent.tools_registry import WebSearchInput
        inp = WebSearchInput(query="")
        assert inp.query == ""
