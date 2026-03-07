"""
JAWIR OS - Researcher Node
Executes web searches and gathers information.
"""

import json
import logging
from datetime import datetime
from typing import Any
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from agent.state import JawirState, ResearchSource, ToolResult, AgentThinking
from agent.utils import extract_text_from_response
from agent.api_rotator import get_api_key, mark_key_rate_limited, mark_key_disabled
from tools.web_search import TavilySearchTool
from app.config import settings

logger = logging.getLogger("jawir.agent.researcher")

# Load system prompt
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "researcher.txt"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""


def get_researcher_llm() -> tuple[ChatGoogleGenerativeAI, str]:
    """Get Gemini model configured for researcher role with rotated API key."""
    api_key = get_api_key()
    return ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        temperature=0.5,
        convert_system_message_to_human=True,
    ), api_key


async def researcher_node(state: JawirState) -> dict[str, Any]:
    """
    Researcher Node: Executes web searches based on plan.
    
    This node:
    1. Gets the current plan step
    2. Formulates search queries
    3. Executes web search via Tavily
    4. Collects and summarizes results
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with research_sources and tool_results
    """
    logger.info("🔍 Researcher executing search...")
    
    # Get current plan step
    current_step = state.get("current_step", 0)
    plan = state.get("plan", [])
    
    if current_step >= len(plan):
        logger.info("No more steps to execute")
        return {"status": "validating"}
    
    step = plan[current_step]
    step_description = step.get("description", state["user_query"])
    
    # Initialize search tool
    search_tool = TavilySearchTool(api_key=settings.tavily_api_key)
    
    # Generate search queries based on step
    llm, current_key = get_researcher_llm()
    
    try:
        # Ask LLM for optimal search queries
        query_prompt = f"""
Based on this research task: "{step_description}"
And the original user question: "{state['user_query']}"

Generate 1-3 search queries that would best find relevant information.
Return as JSON array of strings.
Example: ["query 1", "query 2"]
"""
        
        query_response = await llm.ainvoke([HumanMessage(content=query_prompt)])
        
        # Parse queries
        try:
            query_text = extract_text_from_response(query_response.content)
            if "[" in query_text:
                start = query_text.find("[")
                end = query_text.rfind("]") + 1
                queries = json.loads(query_text[start:end])
            else:
                queries = [step_description]
        except:
            queries = [step_description]
        
        logger.info(f"📝 Queries: {queries}")
        
        # Execute searches
        all_sources: list[ResearchSource] = state.get("research_sources", []).copy()
        tool_results: list[ToolResult] = state.get("tool_results", []).copy()
        
        for query in queries[:3]:  # Max 3 queries per step
            try:
                results = await search_tool.search(query, max_results=5)
                
                for result in results:
                    source = ResearchSource(
                        url=result.url,
                        title=result.title,
                        content=result.content,
                        relevance_score=result.score,
                        retrieved_at=datetime.now().isoformat(),
                    )
                    all_sources.append(source)
                
                tool_results.append(ToolResult(
                    tool_name="web_search",
                    status="success",
                    data={
                        "query": query,
                        "results_count": len(results),
                        "sources": [r.to_dict() for r in results],
                    },
                    error_message=None,
                    executed_at=datetime.now().isoformat(),
                ))
                
                logger.info(f"✅ Found {len(results)} results for: {query}")
                
            except Exception as e:
                logger.error(f"Search failed for '{query}': {e}")
                tool_results.append(ToolResult(
                    tool_name="web_search",
                    status="error",
                    data={"query": query},
                    error_message=str(e),
                    executed_at=datetime.now().isoformat(),
                ))
        
        # Generate summary of findings
        if all_sources:
            summary_prompt = f"""
Summarize the following research findings in 2-3 paragraphs:

Original question: {state['user_query']}

Sources found:
{chr(10).join([f"- {s['title']}: {s['content'][:300]}..." for s in all_sources[-10:]])}

Provide a clear, factual summary in Indonesian.
"""
            summary_response = await llm.ainvoke([HumanMessage(content=summary_prompt)])
            research_summary = extract_text_from_response(summary_response.content)
        else:
            research_summary = "Tidak ditemukan sumber yang relevan."
        
        # Update plan step status
        updated_plan = plan.copy()
        if current_step < len(updated_plan):
            updated_plan[current_step] = {
                **updated_plan[current_step],
                "status": "completed",
            }
        
        # Create thinking record
        thinking = AgentThinking(
            thought=f"Meneliti: {step_description}",
            evaluation=f"Ditemukan {len(all_sources)} sumber",
            memory=f"Queries: {queries}",
            next_goal="Validasi hasil penelitian",
        )
        
        # Check if more steps need research
        next_step = current_step + 1
        has_more_research = any(
            s.get("tool_needed") in ["web_search", "deep_research"]
            for s in plan[next_step:]
        ) if next_step < len(plan) else False
        
        return {
            "research_sources": all_sources,
            "research_summary": research_summary,
            "tool_results": tool_results,
            "plan": updated_plan,
            "current_step": next_step,
            "thinking_history": state.get("thinking_history", []) + [thinking],
            "current_thinking": thinking,
            "status": "researching" if has_more_research else "validating",
            "sources_used": list(set(s["url"] for s in all_sources)),
        }
        
    except Exception as e:
        import re
        error_msg = str(e)
        logger.error(f"Researcher error: {e}")
        
        # Handle PERMISSION_DENIED (leaked/invalid key)
        if "PERMISSION_DENIED" in error_msg or "leaked" in error_msg.lower():
            mark_key_disabled(current_key, "PERMISSION_DENIED - possibly leaked")
            logger.error(f"🚫 Key disabled due to PERMISSION_DENIED")
        # Handle rate limit error
        elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            retry_match = re.search(r'retry in (\d+)', error_msg.lower())
            retry_seconds = int(retry_match.group(1)) if retry_match else 60
            mark_key_rate_limited(current_key, retry_seconds)
            logger.warning(f"🔄 Key rate limited, marked for {retry_seconds}s cooldown")
        
        return {
            "status": "validating",
            "errors": state.get("errors", []) + [f"Research error: {e}"],
            "current_step": current_step + 1,
        }
