"""
JAWIR OS - Tavily Web Search Tool
Wrapper for Tavily API with error handling and retry logic.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

from tavily import TavilyClient
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("jawir.tools.web_search")


@dataclass
class SearchResult:
    """Single search result from Tavily."""
    url: str
    title: str
    content: str
    score: float
    raw_content: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "score": self.score,
            "raw_content": self.raw_content,
        }


class TavilySearchTool:
    """
    Tavily Search Tool wrapper for JAWIR OS.
    Provides web search with automatic retry on failure.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Tavily client.
        
        Args:
            api_key: Tavily API key
        """
        self.client = TavilyClient(api_key=api_key)
        logger.info("TavilySearchTool initialized")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_raw_content: bool = False,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """
        Perform web search using Tavily API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results (default 5)
            search_depth: "basic" or "advanced" (default "basic")
            include_raw_content: Include full page content (default False)
            include_domains: Only search these domains
            exclude_domains: Exclude these domains
        
        Returns:
            List of SearchResult objects
        
        Raises:
            Exception: If search fails after retries
        """
        logger.info(f"🔍 Searching: '{query}' (max_results={max_results}, depth={search_depth})")
        
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_raw_content=include_raw_content,
                include_domains=include_domains or [],
                exclude_domains=exclude_domains or [],
            )
            
            results = []
            for item in response.get("results", []):
                result = SearchResult(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                    raw_content=item.get("raw_content") if include_raw_content else None,
                )
                results.append(result)
            
            logger.info(f"✅ Found {len(results)} results for: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed for '{query}': {e}")
            raise
    
    async def search_with_context(
        self,
        query: str,
        max_results: int = 5,
    ) -> dict:
        """
        Search and return formatted context for LLM.
        
        Args:
            query: Search query
            max_results: Maximum results
        
        Returns:
            Dictionary with results and formatted context string
        """
        results = await self.search(query, max_results=max_results)
        
        # Format context for LLM
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Source {i}] {result.title}\n"
                f"URL: {result.url}\n"
                f"Content: {result.content}\n"
            )
        
        return {
            "results": results,
            "context": "\n---\n".join(context_parts),
            "sources": [r.url for r in results],
            "query": query,
            "timestamp": datetime.now().isoformat(),
        }
    
    def search_sync(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
    ) -> List[SearchResult]:
        """
        Synchronous version of search for non-async contexts.
        """
        logger.info(f"🔍 Searching (sync): '{query}'")
        
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
            )
            
            results = []
            for item in response.get("results", []):
                result = SearchResult(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                )
                results.append(result)
            
            logger.info(f"✅ Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Sync search failed: {e}")
            raise


# ============================================
# LangChain Tool Wrapper
# ============================================

def create_tavily_tool(api_key: str):
    """
    Create a LangChain-compatible tool for Tavily search.
    
    Args:
        api_key: Tavily API key
    
    Returns:
        LangChain Tool instance
    """
    from langchain_core.tools import tool
    
    client = TavilyClient(api_key=api_key)
    
    @tool
    def web_search(query: str) -> str:
        """
        Search the web for information about a topic.
        Use this when you need to find current information, facts, or data from the internet.
        
        Args:
            query: The search query to look up
        
        Returns:
            Search results with titles, URLs, and content snippets
        """
        try:
            response = client.search(query=query, max_results=5)
            
            results_text = []
            for i, item in enumerate(response.get("results", []), 1):
                results_text.append(
                    f"[{i}] {item.get('title', 'No title')}\n"
                    f"    URL: {item.get('url', '')}\n"
                    f"    {item.get('content', 'No content')[:500]}..."
                )
            
            return "\n\n".join(results_text) if results_text else "No results found."
            
        except Exception as e:
            return f"Search error: {str(e)}"
    
    return web_search


# ============================================
# Test Function
# ============================================

if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def test_search():
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            print("❌ TAVILY_API_KEY not found in environment")
            return
        
        tool = TavilySearchTool(api_key=api_key)
        
        # Test search
        query = "ESP32 specifications and features 2024"
        print(f"\n🔍 Testing search: '{query}'\n")
        
        try:
            results = await tool.search(query)
            
            print(f"✅ Found {len(results)} results:\n")
            for i, r in enumerate(results, 1):
                print(f"[{i}] {r.title}")
                print(f"    URL: {r.url}")
                print(f"    Score: {r.score:.3f}")
                print(f"    Content: {r.content[:200]}...")
                print()
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    asyncio.run(test_search())
