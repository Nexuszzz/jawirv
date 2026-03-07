"""
JAWIR OS - Tool Registry for Gemini Function Calling
=====================================================
Registry semua tools yang available untuk Gemini function calling.

NOTE: This module is now a backward-compatible wrapper around
the modular `agent.tools` package. All tool implementations
have been split into category-based modules:

    agent/tools/web.py         - Web search (Tavily)
    agent/tools/kicad.py       - KiCad schematic design
    agent/tools/python_exec.py - Python code execution
    agent/tools/google.py      - Google Workspace (6 tools)
    agent/tools/desktop.py     - Desktop control (3 tools)
    agent/tools/__init__.py    - Aggregator

Usage (unchanged):
    from agent.tools_registry import get_all_tools
    tools = get_all_tools()  # Returns 12 StructuredTool objects
    
    # OR use modular import:
    from agent.tools import get_all_tools
"""

import logging
from typing import Optional

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

logger = logging.getLogger("jawir.agent.tools_registry")

# Re-export everything from modular package for backward compatibility
from agent.tools import (
    get_all_tools,
    get_tool_names,
    WebSearchInput,
    KicadDesignInput,
    PythonCodeInput,
    GmailSearchInput,
    GmailSendInput,
    DriveSearchInput,
    DriveListInput,
    CalendarListEventsInput,
    CalendarCreateEventInput,
    OpenAppInput,
    OpenUrlInput,
    CloseAppInput,
)

# Also re-export factory functions for backward compatibility
from agent.tools.web import create_web_search_tool
from agent.tools.kicad import create_kicad_tool
from agent.tools.python_exec import create_python_executor_tool
from agent.tools.google import (
    create_gmail_search_tool,
    create_gmail_send_tool,
    create_drive_search_tool,
    create_drive_list_tool,
    create_calendar_list_tool,
    create_calendar_create_tool,
)
from agent.tools.desktop import (
    create_open_app_tool,
    create_open_url_tool,
    create_close_app_tool,
)
