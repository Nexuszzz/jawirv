"""
JAWIR OS - Validator Node
Validates research quality and decides if retry is needed.
"""

import logging
from typing import Any, Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from agent.state import JawirState, AgentThinking
from agent.utils import extract_text_from_response
from agent.api_rotator import get_api_key, mark_key_rate_limited, mark_key_disabled
from app.config import settings

logger = logging.getLogger("jawir.agent.validator")


def get_validator_llm() -> tuple[ChatGoogleGenerativeAI, str]:
    """Get Gemini model configured for validator role with rotated API key."""
    api_key = get_api_key()
    return ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        temperature=0,
        convert_system_message_to_human=True,
    ), api_key


async def validator_node(state: JawirState) -> dict[str, Any]:
    """
    Validator Node: Checks if research is sufficient.
    
    This node:
    1. Evaluates the quality of gathered sources
    2. Checks if the question can be answered
    3. Decides if more research is needed
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with validation feedback
    """
    logger.info("✅ Validator checking results...")
    
    sources = state.get("research_sources", [])
    errors = state.get("errors", [])
    retry_count = state.get("retry_count", 0)
    user_query = state.get("user_query", "")
    research_summary = state.get("research_summary", "")
    
    # Quick checks
    if retry_count >= settings.max_retry_count:
        logger.warning(f"Max retries ({settings.max_retry_count}) reached")
        return {
            "validation_feedback": "Max retries reached, synthesizing with available data",
            "status": "synthesizing",
        }
    
    if not sources:
        logger.warning("No sources found")
        return {
            "validation_feedback": "No sources found",
            "status": "synthesizing",  # Go to synthesizer anyway
            "retry_count": retry_count + 1,
            "errors": errors + ["No sources found in research"],
        }
    
    # Use LLM to evaluate quality
    llm, current_key = get_validator_llm()
    
    validation_prompt = f"""
Evaluate if the following research is SUFFICIENT to answer the user's question.

USER QUESTION: {user_query}

SOURCES FOUND ({len(sources)} total):
{chr(10).join([f"- {s['title']}: {s['content'][:200]}..." for s in sources[:5]])}

RESEARCH SUMMARY:
{research_summary[:500]}

Evaluate and respond with ONLY one of these:
- "SUFFICIENT" - if the data is enough to provide a good answer
- "NEED_MORE" - if more research is needed (explain what's missing)
- "ACCEPTABLE" - if not perfect but workable

Your response:
"""
    
    try:
        response = await llm.ainvoke([HumanMessage(content=validation_prompt)])
        evaluation = extract_text_from_response(response.content).strip().upper()
        
        logger.info(f"Validation result: {evaluation}")
        
        # Parse evaluation
        if "SUFFICIENT" in evaluation or "ACCEPTABLE" in evaluation:
            thinking = AgentThinking(
                thought="Hasil penelitian sudah cukup",
                evaluation=f"Ditemukan {len(sources)} sumber yang relevan",
                memory=None,
                next_goal="Menyusun jawaban final",
            )
            
            return {
                "validation_feedback": "Research sufficient",
                "status": "synthesizing",
                "thinking_history": state.get("thinking_history", []) + [thinking],
                "current_thinking": thinking,
            }
        
        elif "NEED_MORE" in evaluation:
            # Need more research
            thinking = AgentThinking(
                thought="Perlu penelitian tambahan",
                evaluation=evaluation,
                memory=f"Retry count: {retry_count + 1}",
                next_goal="Mencari sumber tambahan",
            )
            
            return {
                "validation_feedback": evaluation,
                "status": "researching",
                "retry_count": retry_count + 1,
                "thinking_history": state.get("thinking_history", []) + [thinking],
                "current_thinking": thinking,
            }
        
        else:
            # Default to synthesizing
            return {
                "validation_feedback": evaluation,
                "status": "synthesizing",
            }
            
    except Exception as e:
        import re
        error_msg = str(e)
        logger.error(f"Validation error: {e}")
        
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
        
        # On error, proceed to synthesizing
        return {
            "validation_feedback": f"Validation error: {e}",
            "status": "synthesizing",
            "errors": errors + [f"Validation error: {e}"],
        }


def should_continue(state: JawirState) -> Literal["researcher", "synthesizer"]:
    """
    Conditional edge function for ReAct loop.
    
    This is the KEY function that enables the ReAct pattern:
    - If more research needed → loop back to researcher
    - If sufficient → proceed to synthesizer
    
    Args:
        state: Current agent state
    
    Returns:
        Next node name: "researcher" or "synthesizer"
    """
    status = state.get("status", "")
    retry_count = state.get("retry_count", 0)
    
    # Check max retries
    if retry_count >= settings.max_retry_count:
        logger.info(f"Max retries reached ({retry_count}), going to synthesizer")
        return "synthesizer"
    
    # Check status
    if status == "researching":
        logger.info("Need more research, looping back to researcher")
        return "researcher"
    
    logger.info("Research complete, proceeding to synthesizer")
    return "synthesizer"
