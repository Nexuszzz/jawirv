"""
JAWIR OS - Tool Registry (Modular)
====================================
Aggregator yang mengumpulkan semua tools dari modul per-kategori.

Modules:
    - tools.web: Web search (Tavily)
    - tools.kicad: KiCad schematic design
    - tools.python_exec: Python code execution
    - tools.google: Gmail, Drive, Calendar (6 tools)
    - tools.desktop: Open/close apps, open URL (3 tools)

Usage:
    from agent.tools import get_all_tools, get_tool_names
    tools = get_all_tools()  # Returns 12 StructuredTool objects
"""

import logging
from langchain_core.tools import StructuredTool

logger = logging.getLogger("jawir.agent.tools")


def get_all_tools() -> list[StructuredTool]:
    """
    Get all available tools for Gemini function calling.
    Aggregates tools from all category modules.
    
    Returns:
        List of LangChain StructuredTool objects (12 tools)
    """
    tools = []

    # --- Web Search ---
    try:
        from agent.tools.web import create_web_search_tool
        tools.append(create_web_search_tool())
        logger.info("✅ Registered: web_search")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register web_search: {e}")

    # --- KiCad ---
    try:
        from agent.tools.kicad import create_kicad_tool
        tools.append(create_kicad_tool())
        logger.info("✅ Registered: generate_kicad_schematic")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register kicad: {e}")

    # --- Python Executor ---
    try:
        from agent.tools.python_exec import create_python_executor_tool
        tools.append(create_python_executor_tool())
        logger.info("✅ Registered: run_python_code")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register python_executor: {e}")

    # --- Google Workspace (6 tools) ---
    try:
        from agent.tools.google import (
            create_gmail_search_tool,
            create_gmail_send_tool,
            create_drive_search_tool,
            create_drive_list_tool,
            create_calendar_list_tool,
            create_calendar_create_tool,
        )
        tools.append(create_gmail_search_tool())
        logger.info("✅ Registered: gmail_search")
        tools.append(create_gmail_send_tool())
        logger.info("✅ Registered: gmail_send")
        tools.append(create_drive_search_tool())
        logger.info("✅ Registered: drive_search")
        tools.append(create_drive_list_tool())
        logger.info("✅ Registered: drive_list")
        tools.append(create_calendar_list_tool())
        logger.info("✅ Registered: calendar_list_events")
        tools.append(create_calendar_create_tool())
        logger.info("✅ Registered: calendar_create_event")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register Google Workspace tools: {e}")

    # --- Google Sheets (3 tools) ---
    try:
        from agent.tools.google import (
            create_sheets_read_tool,
            create_sheets_write_tool,
            create_sheets_create_tool,
        )
        tools.append(create_sheets_read_tool())
        logger.info("✅ Registered: sheets_read")
        tools.append(create_sheets_write_tool())
        logger.info("✅ Registered: sheets_write")
        tools.append(create_sheets_create_tool())
        logger.info("✅ Registered: sheets_create")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register Sheets tools: {e}")

    # --- Google Docs (2 tools) ---
    try:
        from agent.tools.google import (
            create_docs_read_tool,
            create_docs_create_tool,
        )
        tools.append(create_docs_read_tool())
        logger.info("✅ Registered: docs_read")
        tools.append(create_docs_create_tool())
        logger.info("✅ Registered: docs_create")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register Docs tools: {e}")

    # --- Google Forms (3 tools) ---
    try:
        from agent.tools.google import (
            create_forms_read_tool,
            create_forms_create_tool,
            create_forms_add_question_tool,
        )
        tools.append(create_forms_read_tool())
        logger.info("✅ Registered: forms_read")
        tools.append(create_forms_create_tool())
        logger.info("✅ Registered: forms_create")
        tools.append(create_forms_add_question_tool())
        logger.info("✅ Registered: forms_add_question")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register Forms tools: {e}")

    # --- Desktop Control (3 tools) ---
    try:
        from agent.tools.desktop import (
            create_open_app_tool,
            create_open_url_tool,
            create_close_app_tool,
        )
        tools.append(create_open_app_tool())
        logger.info("✅ Registered: open_app")
        tools.append(create_open_url_tool())
        logger.info("✅ Registered: open_url")
        tools.append(create_close_app_tool())
        logger.info("✅ Registered: close_app")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register Desktop Control tools: {e}")

    # --- WhatsApp via GoWA (5 tools) ---
    try:
        from agent.tools.whatsapp import get_whatsapp_tools
        whatsapp_tools = get_whatsapp_tools()
        tools.extend(whatsapp_tools)
        for tool in whatsapp_tools:
            logger.info(f"✅ Registered: {tool.name}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register WhatsApp tools: {e}")

    # --- Polinema SIAKAD (2 tools) ---
    # Note: LMS tool removed - not implemented, use akademik instead
    try:
        from agent.tools.polinema import (
            create_polinema_biodata_tool,
            create_polinema_akademik_tool,
        )
        tools.append(create_polinema_biodata_tool())
        logger.info("✅ Registered: polinema_get_biodata")
        tools.append(create_polinema_akademik_tool())
        logger.info("✅ Registered: polinema_get_akademik")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register Polinema tools: {e}")

    # --- IoT Integration (5 tools, conditional) ---
    try:
        from agent.tools.iot import get_iot_tools
        iot_tools = get_iot_tools()  # Returns empty list if IOT_ENABLED=false
        if iot_tools:
            tools.extend(iot_tools)
            for tool in iot_tools:
                logger.info(f"✅ Registered: {tool.name}")
        else:
            logger.info("ℹ️ IoT tools skipped (disabled)")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register IoT tools: {e}")

    logger.info(f"🔧 Tool Registry: {len(tools)} tools registered")
    return tools


def get_tool_names() -> list[str]:
    """Get names of all registered tools."""
    return [t.name for t in get_all_tools()]


# Re-export input schemas for backward compatibility
from agent.tools.web import WebSearchInput
from agent.tools.kicad import KicadDesignInput
from agent.tools.python_exec import PythonCodeInput
from agent.tools.google import (
    GmailSearchInput,
    GmailSendInput,
    DriveSearchInput,
    DriveListInput,
    CalendarListEventsInput,
    CalendarCreateEventInput,
    SheetsReadInput,
    SheetsWriteInput,
    SheetsCreateInput,
    DocsReadInput,
    DocsCreateInput,
    FormsReadInput,
    FormsCreateInput,
)
from agent.tools.desktop import (
    OpenAppInput,
    OpenUrlInput,
    CloseAppInput,
)
from agent.tools.whatsapp import (
    WhatsAppCheckNumberInput,
    WhatsAppListChatsInput,
    WhatsAppSendMessageInput,
    WhatsAppListContactsInput,
    WhatsAppListGroupsInput,
)
from agent.tools.polinema import (
    PolinemaBiodataInput,
    PolinemaAkademikInput,
    PolinemaLMSInput,
)

__all__ = [
    "get_all_tools",
    "get_tool_names",
    # Input schemas
    "WebSearchInput",
    "KicadDesignInput",
    "PythonCodeInput",
    "GmailSearchInput",
    "GmailSendInput",
    "DriveSearchInput",
    "DriveListInput",
    "CalendarListEventsInput",
    "CalendarCreateEventInput",
    "SheetsReadInput",
    "SheetsWriteInput",
    "SheetsCreateInput",
    "DocsReadInput",
    "DocsCreateInput",
    "FormsReadInput",
    "FormsCreateInput",
    "OpenAppInput",
    "OpenUrlInput",
    "CloseAppInput",
    "WhatsAppCheckNumberInput",
    "WhatsAppListChatsInput",
    "WhatsAppSendMessageInput",
    "WhatsAppListContactsInput",
    "WhatsAppListGroupsInput",
    "PolinemaBiodataInput",
    "PolinemaAkademikInput",
    "PolinemaLMSInput",
]
