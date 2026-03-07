"""
JAWIR OS - Supervisor Node
Plans the execution strategy based on user query.
Uses Structured Output (Pydantic) for reliable JSON parsing.
"""

import json
import logging
import re
from typing import Any, Optional, Literal
from pathlib import Path

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from agent.state import JawirState, PlanStep, AgentThinking
from agent.utils import extract_text_from_response
from agent.api_rotator import get_api_key, mark_key_rate_limited, mark_key_disabled

# Try to import json_repair for fallback
try:
    from json_repair import repair_json
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False

logger = logging.getLogger("jawir.agent.supervisor")

# Load system prompt
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "supervisor.txt"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""


# ============================================
# Pydantic Schema for Structured Output
# ============================================
class PlanStepSchema(BaseModel):
    """Schema for a single plan step."""
    step_number: int = Field(description="Nomor urut langkah")
    description: str = Field(description="Deskripsi langkah")
    tool_needed: Optional[str] = Field(default=None, description="Tool yang dibutuhkan: web_search, deep_research, atau null")


class SupervisorOutput(BaseModel):
    """Schema keputusan Supervisor - Structured Output yang reliable."""
    understanding: str = Field(description="Pemahaman tentang apa yang user minta")
    response_type: Literal["direct", "code", "research"] = Field(
        description="Tipe respons: direct=jawab langsung, code=generate kode, research=butuh riset"
    )
    direct_response: Optional[str] = Field(
        default=None, 
        description="Jawaban langsung jika response_type=direct. Kosongkan jika butuh research."
    )
    plan: list[PlanStepSchema] = Field(default=[], description="Langkah-langkah rencana jika butuh research")
    tools_needed: list[str] = Field(default=[], description="Tools yang dibutuhkan: web_search, deep_research")
    notes: Optional[str] = Field(default=None, description="Catatan tambahan")


def get_supervisor_llm() -> ChatGoogleGenerativeAI:
    """Get Gemini model configured for supervisor role with rotated API key."""
    api_key = get_api_key()
    return ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        temperature=0.3,
        convert_system_message_to_human=True,
    ), api_key  # Return key for rate limit tracking


def get_structured_supervisor_llm():
    """Get Gemini model with structured output for reliable parsing."""
    api_key = get_api_key()
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        temperature=0.2,  # Lower for more consistent output
        convert_system_message_to_human=True,
    )
    # Return structured LLM that outputs SupervisorOutput directly
    return llm.with_structured_output(SupervisorOutput), api_key


def parse_json_with_repair(text: str) -> dict:
    """Parse JSON with repair fallback."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if HAS_JSON_REPAIR:
            logger.warning("⚠️ JSON rusak, mencoba memperbaiki dengan json_repair...")
            repaired = repair_json(text)
            return json.loads(repaired)
        raise


async def supervisor_node(state: JawirState) -> dict[str, Any]:
    """
    Supervisor Node: Analyzes user query and creates execution plan.
    
    This is the first node in the graph. It:
    1. Understands the user's request
    2. Determines complexity
    3. Creates a step-by-step plan
    4. Identifies required tools
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with plan and tools_needed
    """
    logger.info(f"📋 Supervisor processing: {state['user_query'][:50]}...")
    
    llm, current_key = get_supervisor_llm()
    
    # Build messages
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"User request: {state['user_query']}"),
    ]
    
    try:
        # Get response from Gemini
        response = await llm.ainvoke(messages)
        response_text = extract_text_from_response(response.content)
        
        logger.debug(f"Supervisor response: {response_text[:500]}...")
        
        # Parse JSON from response - handle nested code blocks carefully
        json_str = ""
        
        # Try to extract JSON from markdown code block if present
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            # Find the LAST ``` to handle nested code blocks in direct_response
            remaining = response_text[json_start:]
            # Count ``` occurrences - we need to find the matching closing one
            parts = remaining.split("```")
            # Reconstruct - take odd-indexed parts as code, even as outside
            # First part is always the JSON content up to first ```
            # We need to be smarter - find the JSON structure end
            try:
                # Try parsing incrementally
                depth = 0
                in_string = False
                escape_next = False
                json_end_idx = 0
                
                for i, char in enumerate(remaining):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\' and in_string:
                        escape_next = True
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                    if not in_string:
                        if char == '{':
                            depth += 1
                        elif char == '}':
                            depth -= 1
                            if depth == 0:
                                json_end_idx = i + 1
                                break
                
                if json_end_idx > 0:
                    json_str = remaining[:json_end_idx]
                else:
                    # Fallback - find first ```
                    json_end = remaining.find("```")
                    json_str = remaining[:json_end].strip() if json_end > 0 else remaining.strip()
            except:
                json_end = remaining.find("```")
                json_str = remaining[:json_end].strip() if json_end > 0 else remaining.strip()
                
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        else:
            # Try to find JSON object directly
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
        
        plan_data = json.loads(json_str)
        
        # Check if this is a direct response (no research needed)
        response_type = plan_data.get("response_type", "")
        direct_response = plan_data.get("direct_response", "")
        
        if response_type == "direct" and direct_response:
            # Simple chat - respond directly without research
            logger.info("✅ Direct response mode - no research needed")
            
            thinking = AgentThinking(
                thought=f"Ini pertanyaan sederhana, bisa dijawab langsung",
                evaluation=None,
                memory=None,
                next_goal="Kirim respons langsung",
            )
            
            return {
                "understanding": plan_data.get("understanding", ""),
                "plan": [],
                "tools_needed": [],
                "current_step": 0,
                "pending_tools": [],
                "thinking_history": state.get("thinking_history", []) + [thinking],
                "current_thinking": thinking,
                "status": "done",
                "final_response": direct_response,
                "sources_used": [],
                "messages": state.get("messages", []) + [
                    HumanMessage(content=state["user_query"]),
                    AIMessage(content=direct_response),
                ],
            }
        
        # Code generation - route to synthesizer (avoid JSON issues with code blocks)
        if response_type == "code":
            logger.info("✅ Code generation mode - routing to synthesizer")
            
            thinking = AgentThinking(
                thought=f"Pertanyaan coding, generate langsung tanpa research",
                evaluation=None,
                memory=plan_data.get("notes"),
                next_goal="Generate code di synthesizer",
            )
            
            return {
                "understanding": plan_data.get("understanding", ""),
                "plan": [],
                "tools_needed": [],
                "current_step": 0,
                "pending_tools": [],
                "thinking_history": state.get("thinking_history", []) + [thinking],
                "current_thinking": thinking,
                "status": "synthesizing",
                "messages": state.get("messages", []) + [
                    HumanMessage(content=state["user_query"]),
                ],
            }
        
        # Extract plan steps for research queries
        plan_steps: list[PlanStep] = []
        for step in plan_data.get("plan", []):
            plan_steps.append(PlanStep(
                step_number=step.get("step_number", len(plan_steps) + 1),
                description=step.get("description", ""),
                tool_needed=step.get("tool_needed"),
                status="pending",
            ))
        
        # Extract tools needed
        tools_needed = plan_data.get("tools_needed", [])
        
        # Create thinking record
        thinking = AgentThinking(
            thought=f"Memahami permintaan: {plan_data.get('understanding', '')}",
            evaluation=None,
            memory=plan_data.get("notes"),
            next_goal=f"Eksekusi {len(plan_steps)} langkah dengan tools: {tools_needed}",
        )
        
        logger.info(f"✅ Plan created: {len(plan_steps)} steps, tools: {tools_needed}")
        
        return {
            "understanding": plan_data.get("understanding", ""),
            "plan": plan_steps,
            "tools_needed": tools_needed,
            "current_step": 0,
            "pending_tools": tools_needed.copy(),
            "thinking_history": state.get("thinking_history", []) + [thinking],
            "current_thinking": thinking,
            "status": "researching" if tools_needed else "synthesizing",
            "messages": state.get("messages", []) + [
                HumanMessage(content=state["user_query"]),
                AIMessage(content=f"Plan: {json.dumps(plan_data, ensure_ascii=False)}"),
            ],
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse supervisor response: {e}")
        logger.debug(f"Response was: {response_text if 'response_text' in dir() else 'N/A'}")
        
        # Try to detect if it was meant to be direct response
        lower_query = state["user_query"].lower().strip()
        
        # Simple greetings - respond directly without another LLM call
        greeting_responses = {
            "halo": "Sugeng, Lur! Kula JAWIR, asisten AI panjenengan. Wonten ingkang saged kula bantu?",
            "hai": "Hai juga, Lur! Kula JAWIR, siap membantu panjenengan. Ada yang bisa kula bantu?",
            "hello": "Hello, Lur! Kula JAWIR, asisten AI ingkang siap mbantu. Monggo, ada yang bisa kula bantu?",
            "halo jawir": "Sugeng, Lur! Nggih, kula JAWIR. Wonten ingkang saged kula bantu dinten puniki?",
        }
        
        # Check for exact greeting match
        for greeting, response in greeting_responses.items():
            if lower_query == greeting or lower_query.startswith(greeting + " "):
                logger.info(f"📝 Using fallback greeting response for: {lower_query}")
                return {
                    "understanding": "Sapaan sederhana",
                    "plan": [],
                    "tools_needed": [],
                    "current_step": 0,
                    "pending_tools": [],
                    "status": "done",
                    "final_response": response,
                    "sources_used": [],
                    "messages": state.get("messages", []) + [
                        HumanMessage(content=state["user_query"]),
                        AIMessage(content=response),
                    ],
                }
        
        # Identity questions
        identity_keywords = ["siapa kamu", "siapa nama", "kamu siapa", "namamu siapa", "who are you"]
        if any(kw in lower_query for kw in identity_keywords):
            identity_response = "Kula naminipun JAWIR, singkatan saking Just Another Wise Intelligent Resource. Kula asisten AI pribadi ingkang siap mbantu panjenengan kangge riset web, analisis, coding, lan maneka perkawis sanesipun. Monggo, wonten ingkang saged kula bantu?"
            logger.info(f"📝 Using fallback identity response")
            return {
                "understanding": "Pertanyaan identitas",
                "plan": [],
                "tools_needed": [],
                "current_step": 0,
                "pending_tools": [],
                "status": "done",
                "final_response": identity_response,
                "sources_used": [],
                "messages": state.get("messages", []) + [
                    HumanMessage(content=state["user_query"]),
                    AIMessage(content=identity_response),
                ],
            }
        
        # Thank you responses
        thank_keywords = ["terima kasih", "makasih", "thanks", "thank you", "thx"]
        if any(kw in lower_query for kw in thank_keywords):
            thank_response = "Sami-sami, Lur! Senang sanget saged mbantu panjenengan. Menawi wonten ingkang mbetahaken malih, monggo langsung matur nggih. JAWIR tansah siap!"
            logger.info(f"📝 Using fallback thank you response")
            return {
                "understanding": "Ucapan terima kasih",
                "plan": [],
                "tools_needed": [],
                "current_step": 0,
                "pending_tools": [],
                "status": "done",
                "final_response": thank_response,
                "sources_used": [],
                "messages": state.get("messages", []) + [
                    HumanMessage(content=state["user_query"]),
                    AIMessage(content=thank_response),
                ],
            }
        
        # Check other simple query keywords - route to synthesizer
        simple_keywords = ["apa itu", "jelaskan", "buatkan", "buat function", "buat code", 
                          "bagaimana cara", "tolong jelaskan", "apa yang dimaksud"]
        needs_research = any(kw in lower_query for kw in 
                            ["harga", "berita", "terbaru", "hari ini", "sekarang", "kurs", "cuaca"])
        is_simple_query = any(kw in lower_query for kw in simple_keywords)
        
        if is_simple_query and not needs_research:
            # Route to synthesizer for knowledge questions
            logger.info("📝 JSON parse failed but query seems simple, will synthesize directly")
            
            thinking = AgentThinking(
                thought=f"Parsing gagal tapi query sederhana, jawab langsung",
                evaluation=None,
                memory=None,
                next_goal="Sintesis jawaban langsung",
            )
            
            return {
                "understanding": state["user_query"],
                "plan": [],
                "tools_needed": [],
                "current_step": 0,
                "pending_tools": [],
                "thinking_history": state.get("thinking_history", []) + [thinking],
                "current_thinking": thinking,
                "status": "synthesizing",  # Go to synthesizer to generate answer
                "messages": state.get("messages", []) + [
                    HumanMessage(content=state["user_query"]),
                ],
            }
        
        # Fallback: simple research plan for queries that need data
        return {
            "understanding": state["user_query"],
            "plan": [PlanStep(
                step_number=1,
                description="Mencari informasi",
                tool_needed="web_search",
                status="pending",
            )],
            "tools_needed": ["web_search"],
            "current_step": 0,
            "pending_tools": ["web_search"],
            "status": "researching",
            "errors": state.get("errors", []) + [f"Plan parsing error: {e}"],
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Supervisor error: {e}")
        
        # Handle PERMISSION_DENIED (leaked/invalid key)
        if "PERMISSION_DENIED" in error_msg or "leaked" in error_msg.lower():
            mark_key_disabled(current_key, "PERMISSION_DENIED - possibly leaked")
            logger.error(f"🚫 Key disabled due to PERMISSION_DENIED")
        # Handle rate limit error
        elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            # Extract retry time if available
            retry_match = re.search(r'retry in (\d+)', error_msg.lower())
            retry_seconds = int(retry_match.group(1)) if retry_match else 60
            mark_key_rate_limited(current_key, retry_seconds)
            logger.warning(f"🔄 Key rate limited, marked for {retry_seconds}s cooldown")
        
        # Try fallback for simple queries even on LLM error
        lower_query = state["user_query"].lower().strip()
        
        # Greeting fallbacks
        if any(g in lower_query for g in ["halo", "hai", "hello"]):
            return {
                "understanding": "Sapaan sederhana",
                "plan": [],
                "tools_needed": [],
                "status": "done",
                "final_response": "Sugeng, Lur! Kula JAWIR. Wonten ingkang saged kula bantu?",
                "sources_used": [],
            }
        
        # Identity fallbacks
        if any(k in lower_query for k in ["siapa kamu", "siapa nama", "who are you"]):
            return {
                "understanding": "Pertanyaan identitas",
                "plan": [],
                "tools_needed": [],
                "status": "done",
                "final_response": "Kula JAWIR (Just Another Wise Intelligent Resource), asisten AI pribadi panjenengan. Monggo, wonten ingkang saged kula bantu?",
                "sources_used": [],
            }
        
        # Thank you fallbacks
        if any(k in lower_query for k in ["terima kasih", "makasih", "thanks"]):
            return {
                "understanding": "Ucapan terima kasih",
                "plan": [],
                "tools_needed": [],
                "status": "done",
                "final_response": "Sami-sami, Lur! Senang saged mbantu. Monggo menawi wonten ingkang dipunbetahaken malih.",
                "sources_used": [],
            }
        
        # For other queries, return error
        return {
            "status": "error",
            "errors": state.get("errors", []) + [f"Supervisor error: {e}"],
        }
