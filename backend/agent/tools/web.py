"""
JAWIR OS - Web Search Tool
===========================
Tool untuk internet search via Tavily API.
"""

import logging
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger("jawir.agent.tools.web")


class WebSearchInput(BaseModel):
    """Input schema for web search tool."""
    query: str = Field(description="Search query untuk mencari informasi terkini di internet")
    max_results: int = Field(default=5, description="Maksimal jumlah hasil pencarian (1-10)", ge=1, le=10)


def create_web_search_tool() -> StructuredTool:
    """Create web search tool wrapping TavilySearchTool."""

    async def _web_search(query: str, max_results: int = 5) -> str:
        """Search internet untuk informasi terkini."""
        from tools.web_search import TavilySearchTool
        from app.config import settings

        try:
            search_tool = TavilySearchTool(api_key=settings.tavily_api_key)
            results = await search_tool.search(query, max_results=max_results)

            if not results:
                return f"Tidak ditemukan hasil untuk: '{query}'"

            output_parts = []
            for i, r in enumerate(results, 1):
                output_parts.append(
                    f"[{i}] {r.title}\n"
                    f"    URL: {r.url}\n"
                    f"    {r.content[:500]}"
                )

            return "\n\n".join(output_parts)

        except Exception as e:
            return f"Error saat mencari '{query}': {str(e)}"

    return StructuredTool.from_function(
        func=_web_search,
        coroutine=_web_search,
        name="web_search",
        description=(
            "Search internet untuk informasi terkini (berita, harga, data real-time, fakta). "
            "Gunakan tool ini ketika user bertanya tentang hal yang butuh data terbaru dari internet. "
            "Contoh: harga produk, berita terkini, cuaca, kurs mata uang, jadwal."
        ),
        args_schema=WebSearchInput,
    )
