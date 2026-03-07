"""
JAWIR OS - Deep Research Skill
Implements recursive research with breadth and depth control.
Based on GPT-Researcher's DeepResearchSkill pattern.
"""

import asyncio
import logging
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from tools.web_search import TavilySearchTool
from app.config import settings

logger = logging.getLogger("jawir.agent.skills.deep_research")

# Constants
MAX_CONTEXT_WORDS = 25000


@dataclass
class ResearchProgress:
    """Track deep research progress for UI updates."""
    current_depth: int = 1
    total_depth: int = 2
    current_breadth: int = 0
    total_breadth: int = 4
    current_query: Optional[str] = None
    completed_queries: int = 0
    total_queries: int = 0
    
    def to_dict(self) -> dict:
        return {
            "current_depth": self.current_depth,
            "total_depth": self.total_depth,
            "current_breadth": self.current_breadth,
            "total_breadth": self.total_breadth,
            "current_query": self.current_query,
            "completed_queries": self.completed_queries,
            "total_queries": self.total_queries,
            "progress_percent": (
                self.completed_queries / self.total_queries * 100
                if self.total_queries > 0 else 0
            ),
        }


@dataclass
class DeepResearchResult:
    """Result from deep research."""
    query: str
    learnings: List[str] = field(default_factory=list)
    sources: List[dict] = field(default_factory=list)
    context: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    depth_completed: int = 0
    
    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "learnings": self.learnings,
            "sources": self.sources,
            "context": self.context[:5],  # Limit for JSON
            "follow_up_questions": self.follow_up_questions,
            "depth_completed": self.depth_completed,
        }


def trim_context_to_word_limit(
    context_list: List[str],
    max_words: int = MAX_CONTEXT_WORDS,
) -> List[str]:
    """
    Trim context to prevent token overflow.
    Prioritizes most recent items (end of list).
    
    Args:
        context_list: List of context strings
        max_words: Maximum total words allowed
    
    Returns:
        Trimmed list of context strings
    """
    total_words = 0
    trimmed = []
    
    # Iterate from end (most recent) to beginning
    for item in reversed(context_list):
        words = len(item.split())
        if total_words + words <= max_words:
            trimmed.insert(0, item)
            total_words += words
        else:
            # If first item is too long, truncate it
            if not trimmed:
                remaining_words = max_words - total_words
                truncated = " ".join(item.split()[:remaining_words])
                trimmed.insert(0, truncated + "...")
            break
    
    return trimmed


class DeepResearchSkill:
    """
    Deep Research skill for comprehensive multi-source research.
    Implements recursive research with breadth (sub-queries) and depth (follow-ups).
    """
    
    def __init__(
        self,
        tavily_api_key: str,
        google_api_key: str,
        breadth: int = 4,
        depth: int = 2,
        concurrency_limit: int = 2,
    ):
        """
        Initialize Deep Research skill.
        
        Args:
            tavily_api_key: Tavily API key
            google_api_key: Google API key for Gemini
            breadth: Number of sub-queries per level (default 4)
            depth: Research depth levels (default 2)
            concurrency_limit: Max concurrent searches (default 2)
        """
        self.search_tool = TavilySearchTool(api_key=tavily_api_key)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",
            google_api_key=google_api_key,
            temperature=0.5,
        )
        self.breadth = breadth
        self.depth = depth
        self.concurrency_limit = concurrency_limit
        
        # Accumulated data
        self.learnings: List[str] = []
        self.context: List[str] = []
        self.sources: List[dict] = []
        self.progress = ResearchProgress(total_depth=depth, total_breadth=breadth)
        
        # Callback for progress updates
        self.on_progress: Optional[callable] = None
    
    async def generate_sub_queries(
        self,
        query: str,
        num_queries: int = 4,
    ) -> List[str]:
        """
        Generate sub-queries for breadth-first research.
        
        Args:
            query: Main research query
            num_queries: Number of sub-queries to generate
        
        Returns:
            List of sub-query strings
        """
        prompt = f"""Given this research topic: "{query}"

Generate {num_queries} specific sub-questions that would help comprehensively research this topic.
Each question should explore a different aspect.

Return as a JSON array of strings. Example:
["question 1", "question 2", "question 3", "question 4"]

Only return the JSON array, nothing else.
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            text = response.content
            
            # Parse JSON array
            import json
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                queries = json.loads(text[start:end])
                return queries[:num_queries]
        except Exception as e:
            logger.error(f"Failed to generate sub-queries: {e}")
        
        # Fallback: return variations of original query
        return [
            f"{query} overview",
            f"{query} details",
            f"{query} examples",
            f"{query} best practices",
        ][:num_queries]
    
    async def extract_learnings(
        self,
        query: str,
        search_results: List[dict],
    ) -> List[str]:
        """
        Extract key learnings from search results.
        
        Args:
            query: The search query
            search_results: List of search result dicts
        
        Returns:
            List of learning strings
        """
        if not search_results:
            return []
        
        context = "\n\n".join([
            f"Source: {r.get('title', 'Unknown')}\n{r.get('content', '')[:500]}"
            for r in search_results[:5]
        ])
        
        prompt = f"""Based on this search for "{query}":

{context}

Extract 3-5 key learnings or facts. Return as JSON array of strings.
Example: ["learning 1", "learning 2", "learning 3"]

Only return the JSON array.
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            text = response.content
            
            import json
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except Exception as e:
            logger.error(f"Failed to extract learnings: {e}")
        
        return []
    
    async def generate_follow_up_questions(
        self,
        query: str,
        learnings: List[str],
    ) -> List[str]:
        """
        Generate follow-up questions based on learnings.
        
        Args:
            query: Original query
            learnings: Current learnings
        
        Returns:
            List of follow-up question strings
        """
        if not learnings:
            return []
        
        prompt = f"""Given the research topic "{query}" and these learnings:
{chr(10).join([f"- {l}" for l in learnings[:5]])}

Generate 2-3 follow-up questions to go deeper. Return as JSON array.
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            text = response.content
            
            import json
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except:
            pass
        
        return []
    
    async def research_single_query(self, query: str) -> dict:
        """Research a single query and return results."""
        logger.info(f"🔍 Deep research: {query}")
        
        self.progress.current_query = query
        if self.on_progress:
            await self.on_progress(self.progress.to_dict())
        
        try:
            results = await self.search_tool.search(query, max_results=5)
            
            result_dicts = [r.to_dict() for r in results]
            learnings = await self.extract_learnings(query, result_dicts)
            
            self.progress.completed_queries += 1
            
            return {
                "query": query,
                "results": result_dicts,
                "learnings": learnings,
            }
        except Exception as e:
            logger.error(f"Research failed for '{query}': {e}")
            self.progress.completed_queries += 1
            return {"query": query, "results": [], "learnings": []}
    
    async def deep_research(
        self,
        query: str,
        current_depth: int = 1,
        learnings: Optional[List[str]] = None,
    ) -> DeepResearchResult:
        """
        Perform deep recursive research.
        
        Args:
            query: Main research query
            current_depth: Current depth level (1 = first level)
            learnings: Accumulated learnings from previous levels
        
        Returns:
            DeepResearchResult with all findings
        """
        logger.info(f"📚 Deep research depth {current_depth}/{self.depth}: {query}")
        
        learnings = learnings or []
        result = DeepResearchResult(query=query)
        
        # Update progress
        self.progress.current_depth = current_depth
        self.progress.total_queries = self.breadth * current_depth
        
        # Generate sub-queries for breadth
        sub_queries = await self.generate_sub_queries(query, self.breadth)
        
        # Research each sub-query (with concurrency limit)
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        
        async def bounded_research(q):
            async with semaphore:
                return await self.research_single_query(q)
        
        tasks = [bounded_research(q) for q in sub_queries]
        sub_results = await asyncio.gather(*tasks)
        
        # Collect results
        for sub_result in sub_results:
            result.learnings.extend(sub_result.get("learnings", []))
            
            for r in sub_result.get("results", []):
                result.sources.append({
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                })
                result.context.append(
                    f"[{r.get('title', 'Source')}]: {r.get('content', '')}"
                )
        
        # Trim context to prevent overflow
        result.context = trim_context_to_word_limit(result.context)
        
        # Accumulate global learnings
        self.learnings.extend(result.learnings)
        self.context.extend(result.context)
        self.sources.extend(result.sources)
        
        # Recurse deeper if depth allows
        if current_depth < self.depth:
            # Generate follow-up questions
            follow_ups = await self.generate_follow_up_questions(
                query, result.learnings
            )
            result.follow_up_questions = follow_ups
            
            # Research follow-ups at next depth
            for follow_up in follow_ups[:2]:  # Limit follow-ups
                deeper_result = await self.deep_research(
                    follow_up,
                    current_depth + 1,
                    self.learnings,
                )
                result.learnings.extend(deeper_result.learnings)
                result.sources.extend(deeper_result.sources)
        
        result.depth_completed = current_depth
        
        # Trim final context
        self.context = trim_context_to_word_limit(self.context)
        
        return result
    
    async def research(
        self,
        query: str,
        on_progress: Optional[callable] = None,
    ) -> DeepResearchResult:
        """
        Main entry point for deep research.
        
        Args:
            query: Research query
            on_progress: Optional callback for progress updates
        
        Returns:
            DeepResearchResult with comprehensive findings
        """
        self.on_progress = on_progress
        
        # Reset accumulated data
        self.learnings = []
        self.context = []
        self.sources = []
        self.progress = ResearchProgress(
            total_depth=self.depth,
            total_breadth=self.breadth,
        )
        
        result = await self.deep_research(query)
        
        # Deduplicate sources by URL
        seen_urls = set()
        unique_sources = []
        for source in result.sources:
            url = source.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        result.sources = unique_sources
        
        logger.info(
            f"✅ Deep research complete: {len(result.learnings)} learnings, "
            f"{len(result.sources)} sources"
        )
        
        return result


# ============================================
# Test Function
# ============================================

async def test_deep_research():
    """Test deep research with a sample query."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    skill = DeepResearchSkill(
        tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
        google_api_key=os.getenv("GOOGLE_API_KEY", ""),
        breadth=2,  # Reduced for testing
        depth=1,    # Reduced for testing
    )
    
    async def on_progress(progress):
        print(f"Progress: {progress}")
    
    result = await skill.research(
        "ESP32 vs STM32 for IoT projects",
        on_progress=on_progress,
    )
    
    print("\n" + "="*60)
    print("Deep Research Result")
    print("="*60)
    print(f"\nLearnings ({len(result.learnings)}):")
    for i, learning in enumerate(result.learnings[:10], 1):
        print(f"  {i}. {learning}")
    print(f"\nSources ({len(result.sources)}):")
    for source in result.sources[:5]:
        print(f"  - {source.get('title', 'Unknown')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_deep_research())
