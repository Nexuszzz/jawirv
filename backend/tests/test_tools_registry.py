"""
JAWIR OS - Unit Tests for Tool Registry
========================================
Task 1.11: Verify get_all_tools() returns correct count and types.

Run:
    cd backend
    python -m pytest tests/test_tools_registry.py -v
"""

import sys
import os

# Setup path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from langchain_core.tools import StructuredTool
from pydantic import BaseModel


class TestToolRegistryImport:
    """Test that tools_registry module imports correctly."""

    def test_import_get_all_tools(self):
        from agent.tools_registry import get_all_tools
        assert callable(get_all_tools)

    def test_import_get_tool_names(self):
        from agent.tools_registry import get_tool_names
        assert callable(get_tool_names)


class TestGetAllTools:
    """Test get_all_tools() returns correct tools."""

    def test_returns_list(self):
        from agent.tools_registry import get_all_tools
        tools = get_all_tools()
        assert isinstance(tools, list)

    def test_returns_12_tools(self):
        from agent.tools_registry import get_all_tools
        tools = get_all_tools()
        assert len(tools) == 12, f"Expected 12 tools, got {len(tools)}: {[t.name for t in tools]}"

    def test_all_structured_tools(self):
        from agent.tools_registry import get_all_tools
        tools = get_all_tools()
        for tool in tools:
            assert isinstance(tool, StructuredTool), f"{tool} is not a StructuredTool"

    def test_tool_names_unique(self):
        from agent.tools_registry import get_all_tools
        tools = get_all_tools()
        names = [t.name for t in tools]
        assert len(names) == len(set(names)), f"Duplicate tool names found: {names}"


class TestToolNames:
    """Test that expected tools are present."""

    EXPECTED_TOOLS = [
        "web_search",
        "generate_kicad_schematic",
        "run_python_code",
        "gmail_search",
        "gmail_send",
        "drive_search",
        "drive_list",
        "calendar_list_events",
        "calendar_create_event",
        "open_app",
        "open_url",
        "close_app",
    ]

    def test_get_tool_names(self):
        from agent.tools_registry import get_tool_names
        names = get_tool_names()
        assert isinstance(names, list)
        assert len(names) == 12

    def test_expected_tools_present(self):
        from agent.tools_registry import get_tool_names
        names = get_tool_names()
        for expected in self.EXPECTED_TOOLS:
            assert expected in names, f"Missing tool: {expected}"


class TestToolSchemas:
    """Test that all tools have proper Pydantic input schemas."""

    def test_all_tools_have_args_schema(self):
        from agent.tools_registry import get_all_tools
        tools = get_all_tools()
        for tool in tools:
            assert tool.args_schema is not None, f"Tool '{tool.name}' missing args_schema"
            assert issubclass(tool.args_schema, BaseModel), (
                f"Tool '{tool.name}' args_schema is not a Pydantic BaseModel"
            )

    def test_all_tools_have_description(self):
        from agent.tools_registry import get_all_tools
        tools = get_all_tools()
        for tool in tools:
            assert tool.description, f"Tool '{tool.name}' has empty description"
            assert len(tool.description) > 10, (
                f"Tool '{tool.name}' description too short: '{tool.description}'"
            )

    def test_all_tools_have_coroutine(self):
        """All tools must have async coroutine for LangGraph compatibility."""
        from agent.tools_registry import get_all_tools
        tools = get_all_tools()
        for tool in tools:
            assert tool.coroutine is not None, f"Tool '{tool.name}' missing async coroutine"


class TestInputSchemaFields:
    """Test specific input schema fields for critical tools."""

    def test_web_search_schema(self):
        from agent.tools_registry import WebSearchInput
        schema = WebSearchInput.model_json_schema()
        assert "query" in schema["properties"]
        assert "max_results" in schema["properties"]

    def test_gmail_search_schema(self):
        from agent.tools_registry import GmailSearchInput
        schema = GmailSearchInput.model_json_schema()
        assert "query" in schema["properties"]
        assert "max_results" in schema["properties"]

    def test_gmail_send_schema(self):
        from agent.tools_registry import GmailSendInput
        schema = GmailSendInput.model_json_schema()
        assert "to" in schema["properties"]
        assert "subject" in schema["properties"]
        assert "body" in schema["properties"]

    def test_kicad_schema(self):
        from agent.tools_registry import KicadDesignInput
        schema = KicadDesignInput.model_json_schema()
        assert "description" in schema["properties"]
        assert "project_name" in schema["properties"]

    def test_open_app_schema(self):
        from agent.tools_registry import OpenAppInput
        schema = OpenAppInput.model_json_schema()
        assert "app_name" in schema["properties"]

    def test_calendar_create_schema(self):
        from agent.tools_registry import CalendarCreateEventInput
        schema = CalendarCreateEventInput.model_json_schema()
        assert "summary" in schema["properties"]
        assert "start_time" in schema["properties"]
        assert "end_time" in schema["properties"]

    def test_drive_search_schema(self):
        from agent.tools_registry import DriveSearchInput
        schema = DriveSearchInput.model_json_schema()
        assert "query" in schema["properties"]


class TestToolFactoryFunctions:
    """Test individual tool factory functions."""

    def test_create_web_search_tool(self):
        from agent.tools_registry import create_web_search_tool
        tool = create_web_search_tool()
        assert tool.name == "web_search"
        assert isinstance(tool, StructuredTool)

    def test_create_kicad_tool(self):
        from agent.tools_registry import create_kicad_tool
        tool = create_kicad_tool()
        assert tool.name == "generate_kicad_schematic"

    def test_create_python_executor_tool(self):
        from agent.tools_registry import create_python_executor_tool
        tool = create_python_executor_tool()
        assert tool.name == "run_python_code"

    def test_create_gmail_search_tool(self):
        from agent.tools_registry import create_gmail_search_tool
        tool = create_gmail_search_tool()
        assert tool.name == "gmail_search"

    def test_create_gmail_send_tool(self):
        from agent.tools_registry import create_gmail_send_tool
        tool = create_gmail_send_tool()
        assert tool.name == "gmail_send"

    def test_create_drive_search_tool(self):
        from agent.tools_registry import create_drive_search_tool
        tool = create_drive_search_tool()
        assert tool.name == "drive_search"

    def test_create_drive_list_tool(self):
        from agent.tools_registry import create_drive_list_tool
        tool = create_drive_list_tool()
        assert tool.name == "drive_list"

    def test_create_calendar_list_tool(self):
        from agent.tools_registry import create_calendar_list_tool
        tool = create_calendar_list_tool()
        assert tool.name == "calendar_list_events"

    def test_create_calendar_create_tool(self):
        from agent.tools_registry import create_calendar_create_tool
        tool = create_calendar_create_tool()
        assert tool.name == "calendar_create_event"

    def test_create_open_app_tool(self):
        from agent.tools_registry import create_open_app_tool
        tool = create_open_app_tool()
        assert tool.name == "open_app"

    def test_create_open_url_tool(self):
        from agent.tools_registry import create_open_url_tool
        tool = create_open_url_tool()
        assert tool.name == "open_url"

    def test_create_close_app_tool(self):
        from agent.tools_registry import create_close_app_tool
        tool = create_close_app_tool()
        assert tool.name == "close_app"
