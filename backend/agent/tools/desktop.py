"""
JAWIR OS - Desktop Control Tools
==================================
Tools untuk membuka/menutup aplikasi desktop dan URL.
"""

import logging
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger("jawir.agent.tools.desktop")


# ============================================
# INPUT SCHEMAS
# ============================================

class OpenAppInput(BaseModel):
    """Input schema for opening a desktop application."""
    app_name: str = Field(description="Nama aplikasi yang akan dibuka. Contoh: 'chrome', 'spotify', 'calculator', 'notepad', 'vscode', 'word', 'excel'")
    args: list[str] = Field(default_factory=list, description="Argumen tambahan untuk aplikasi (opsional)")


class OpenUrlInput(BaseModel):
    """Input schema for opening a URL in browser."""
    url: str = Field(description="URL yang akan dibuka. Contoh: 'https://google.com'")
    browser: str = Field(default="", description="Browser spesifik: 'chrome', 'firefox', 'edge'. Kosongkan untuk default browser.")


class CloseAppInput(BaseModel):
    """Input schema for closing a desktop application."""
    app_name: str = Field(description="Nama aplikasi yang akan ditutup. Contoh: 'chrome', 'notepad', 'spotify'")


# ============================================
# TOOL FACTORIES
# ============================================

def create_open_app_tool() -> StructuredTool:
    """Create desktop app opener tool."""

    async def _open_app(app_name: str, args: list[str] = None) -> str:
        """Open a desktop application."""
        try:
            from tools.python_interpreter.desktop_control import DesktopController
            dc = DesktopController()
            result = dc.open_app(app_name, args=args or [])

            if result.get("success"):
                return f"✅ {result.get('message', f'Opened {app_name}')}"
            else:
                return f"❌ {result.get('message', f'Failed to open {app_name}')}"
        except Exception as e:
            return f"❌ Error opening app: {str(e)}"

    return StructuredTool.from_function(
        func=_open_app,
        coroutine=_open_app,
        name="open_app",
        description=(
            "Buka aplikasi desktop di Windows. Aplikasi tersedia: chrome, firefox, edge, "
            "spotify, vlc, calculator, notepad, paint, explorer, cmd, powershell, "
            "word, excel, powerpoint, vscode, kicad. "
            "Contoh: open_app('chrome') atau open_app('spotify')."
        ),
        args_schema=OpenAppInput,
    )


def create_open_url_tool() -> StructuredTool:
    """Create URL opener tool."""

    async def _open_url(url: str, browser: str = "") -> str:
        """Open a URL in browser."""
        try:
            from tools.python_interpreter.desktop_control import DesktopController
            dc = DesktopController()
            result = dc.open_url(url, browser=browser or None)

            if result.get("success"):
                return f"✅ {result.get('message', f'Opened {url}')}"
            else:
                return f"❌ {result.get('message', f'Failed to open {url}')}"
        except Exception as e:
            return f"❌ Error opening URL: {str(e)}"

    return StructuredTool.from_function(
        func=_open_url,
        coroutine=_open_url,
        name="open_url",
        description=(
            "Buka URL di browser. Gunakan ketika user minta buka website. "
            "Bisa pilih browser spesifik (chrome/firefox/edge) atau default browser."
        ),
        args_schema=OpenUrlInput,
    )


def create_close_app_tool() -> StructuredTool:
    """Create desktop app closer tool."""

    async def _close_app(app_name: str) -> str:
        """Close a desktop application."""
        try:
            from tools.python_interpreter.desktop_control import DesktopController
            dc = DesktopController()
            result = dc.close_app(app_name)

            if result.get("success"):
                return f"✅ {result.get('message', f'Closed {app_name}')}"
            else:
                return f"❌ {result.get('message', f'Failed to close {app_name}')}"
        except Exception as e:
            return f"❌ Error closing app: {str(e)}"

    return StructuredTool.from_function(
        func=_close_app,
        coroutine=_close_app,
        name="close_app",
        description=(
            "Tutup aplikasi desktop yang sedang berjalan. "
            "Contoh: close_app('chrome'), close_app('notepad')."
        ),
        args_schema=CloseAppInput,
    )
