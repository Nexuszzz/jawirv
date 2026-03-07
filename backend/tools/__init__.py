# JAWIR OS - Tools Module
# Web search, scraper, Google Workspace, and other tools

from .web_search import TavilySearchTool, SearchResult

# Google Workspace MCP Integration
try:
    from .google_workspace import GoogleWorkspaceMCP
except ImportError:
    GoogleWorkspaceMCP = None

__all__ = [
    "TavilySearchTool",
    "SearchResult",
    "GoogleWorkspaceMCP",
]
