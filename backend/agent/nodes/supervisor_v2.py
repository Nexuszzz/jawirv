"""
JAWIR OS - Supervisor Node V2
Uses Structured Output (Pydantic) for 100% reliable JSON parsing.
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
from agent.api_rotator import get_api_key, mark_key_rate_limited, mark_key_disabled

# Try to import json_repair for fallback
try:
    from json_repair import repair_json
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False
    repair_json = None

logger = logging.getLogger("jawir.agent.supervisor")


# ============================================
# Pydantic Schemas for Structured Output
# ============================================
class PlanStepSchema(BaseModel):
    """Schema for a single plan step."""
    step_number: int = Field(description="Nomor urut langkah")
    description: str = Field(description="Deskripsi langkah")
    tool_needed: Optional[str] = Field(default=None, description="Tool: web_search, deep_research, atau null")


class SupervisorOutput(BaseModel):
    """Schema keputusan Supervisor - Output yang reliable."""
    understanding: str = Field(description="Pemahaman tentang permintaan user")
    response_type: Literal["direct", "code", "research", "kicad"] = Field(
        description="direct=jawab langsung (sapaan, identitas, terima kasih), code=generate kode/penjelasan teknis, research=butuh data terkini dari internet, kicad=desain rangkaian elektronika/skematik"
    )
    direct_response: Optional[str] = Field(
        default=None, 
        description="Jawaban langsung jika response_type=direct. WAJIB diisi jika direct. Pakai bahasa Jawa sopan."
    )
    plan: list[PlanStepSchema] = Field(
        default=[], 
        description="Langkah-langkah research jika response_type=research"
    )
    tools_needed: list[str] = Field(
        default=[], 
        description="Tools: web_search atau deep_research. Kosong jika direct/code/kicad."
    )


# ============================================
# Fallback Responses (No LLM needed)
# ============================================
FALLBACK_RESPONSES = {
    "greetings": {
        "keywords": ["halo", "hai", "hello", "hi ", "hey", "selamat pagi", "selamat siang", "selamat sore", "selamat malam"],
        "response": "Sugeng, Lur! Kula JAWIR (Just Another Wise Intelligent Resource), asisten AI pribadi panjenengan. Wonten ingkang saged kula bantu dinten puniki?"
    },
    "identity": {
        # NOTE: Be careful with partial matches! "siapa namaku" should NOT match "siapa nama"
        # Only match when asking about JAWIR's identity, not user's identity
        "keywords": ["siapa kamu", "kamu siapa", "namamu siapa", "who are you", "apa itu jawir", "siapa namamu"],
        "response": "Kula naminipun JAWIR, singkatan saking Just Another Wise Intelligent Resource. Kula asisten AI pribadi ingkang siap mbantu panjenengan kangge riset web, analisis, coding, lan maneka perkawis sanesipun. Monggo, wonten ingkang saged kula bantu?"
    },
    "thanks": {
        "keywords": ["terima kasih", "makasih", "thanks", "thank you", "thx", "trims"],
        "response": "Sami-sami, Lur! Senang sanget saged mbantu panjenengan. Menawi wonten ingkang mbetahaken malih, monggo langsung matur nggih. JAWIR tansah siap!"
    },
    "how_are_you": {
        "keywords": ["apa kabar", "kabarmu", "how are you", "gimana kabar"],
        "response": "Alhamdulillah sae, Lur! Matur nuwun sampun ndangu. Panjenengan pripun? Wonten ingkang saged kula bantu dinten puniki?"
    }
}


def get_fallback_response(query: str) -> Optional[str]:
    """
    Check if query matches any fallback pattern.
    
    IMPORTANT: Only match if the query is PURELY a greeting/thanks/etc.
    If the user says "Halo, buatkan saya X" — that is NOT a greeting,
    that's a real request that starts with a greeting prefix.
    We only match when the meaningful content IS the greeting itself.
    """
    lower_query = query.lower().strip()
    # Remove punctuation for cleaner word comparison
    clean_query = re.sub(r'[^\w\s]', '', lower_query).strip()
    query_words = clean_query.split()
    total_words = len(query_words)
    
    for category, data in FALLBACK_RESPONSES.items():
        for keyword in data["keywords"]:
            keyword_words = keyword.strip().split()
            keyword_len = len(keyword_words)
            
            # Only match if query starts with keyword AND
            # the remaining content is very short (≤ 2 extra words like a name)
            # e.g. "halo jawir" = OK (2 words, greeting + name)
            # e.g. "halo jawir buatkan saya materi" = NOT a greeting (too much after)
            if query_words[:keyword_len] == keyword_words:
                remaining_words = total_words - keyword_len
                # Allow up to 2 extra words (e.g. name/vocative)
                if remaining_words <= 2:
                    return data["response"]
    
    return None


def get_structured_llm():
    """Get Gemini LLM with structured output."""
    api_key = get_api_key()
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        temperature=0.2,
        convert_system_message_to_human=True,
    )
    return llm.with_structured_output(SupervisorOutput), api_key


# Simplified prompt for structured output
STRUCTURED_PROMPT = """Kamu adalah JAWIR (Just Another Wise Intelligent Resource), asisten AI bijaksana dengan sentuhan Jawa yang sopan.

TUGAS: Analisis permintaan user dan tentukan tipe respons.

ATURAN RESPONSE_TYPE:
1. "direct" → Untuk: sapaan (halo, hai), identitas (siapa kamu), terima kasih, apa kabar
   - WAJIB isi direct_response dengan jawaban lengkap dalam bahasa Indonesia + sentuhan Jawa
   
2. "code" → Untuk: pertanyaan konsep (apa itu X), minta code, jelaskan cara kerja
   - Biarkan direct_response kosong, akan dijawab oleh synthesizer
   
3. "research" → Untuk: butuh data terkini (harga, berita, cuaca, kurs, produk terbaru)
   - Isi plan dan tools_needed

4. "kicad" → Untuk: desain rangkaian elektronika, skematik, PCB, komponen elektronik
   - Keywords: skematik, rangkaian, circuit, LED, resistor, kapasitor, ESP32, Arduino, sensor
   - Biarkan direct_response kosong, akan dijawab oleh kicad_designer

CONTOH:
- "halo" → direct, direct_response="Sugeng, Lur! Kula JAWIR..."
- "apa itu React?" → code (synthesizer akan jawab)
- "harga iPhone 16" → research, tools_needed=["web_search"]
- "buatkan skematik LED dengan resistor" → kicad
- "desain rangkaian sensor suhu DHT11" → kicad
"""


async def supervisor_node(state: JawirState) -> dict[str, Any]:
    """
    Supervisor Node V2: Uses structured output for reliable parsing.
    """
    query = state['user_query']
    logger.info(f"📋 Supervisor processing: {query[:50]}...")
    
    # ============================================
    # Level 0: Check fallback responses first (no LLM call)
    # ============================================
    fallback = get_fallback_response(query)
    if fallback:
        logger.info("✅ Using fallback response (no LLM needed)")
        return {
            "understanding": "Query sederhana",
            "plan": [],
            "tools_needed": [],
            "current_step": 0,
            "pending_tools": [],
            "status": "done",
            "final_response": fallback,
            "sources_used": [],
            "messages": state.get("messages", []) + [
                HumanMessage(content=query),
                AIMessage(content=fallback),
            ],
        }
    
    # ============================================
    # Level 2: Use structured output
    # ============================================
    try:
        structured_llm, current_key = get_structured_llm()
        
        messages = [
            SystemMessage(content=STRUCTURED_PROMPT),
            HumanMessage(content=f"User: {query}"),
        ]
        
        # Invoke with structured output - returns SupervisorOutput object directly
        result: SupervisorOutput = await structured_llm.ainvoke(messages)
        
        logger.info(f"✅ Structured output: type={result.response_type}")
        
        # Handle based on response type
        if result.response_type == "direct" and result.direct_response:
            return {
                "understanding": result.understanding,
                "plan": [],
                "tools_needed": [],
                "current_step": 0,
                "pending_tools": [],
                "status": "done",
                "final_response": result.direct_response,
                "sources_used": [],
                "messages": state.get("messages", []) + [
                    HumanMessage(content=query),
                    AIMessage(content=result.direct_response),
                ],
            }
        
        elif result.response_type == "code":
            # Route to synthesizer for code/knowledge
            thinking = AgentThinking(
                thought=f"Pertanyaan {result.response_type}, jawab langsung",
                evaluation=None,
                memory=None,
                next_goal="Generate jawaban di synthesizer",
            )
            return {
                "understanding": result.understanding,
                "plan": [],
                "tools_needed": [],
                "current_step": 0,
                "pending_tools": [],
                "thinking_history": state.get("thinking_history", []) + [thinking],
                "current_thinking": thinking,
                "status": "synthesizing",
                "messages": state.get("messages", []) + [
                    HumanMessage(content=query),
                ],
            }
        
        elif result.response_type == "kicad":
            # Route to kicad_designer for electronic schematics
            thinking = AgentThinking(
                thought=f"Permintaan desain rangkaian elektronika",
                evaluation=None,
                memory=None,
                next_goal="Desain skematik di kicad_designer",
            )
            return {
                "understanding": result.understanding,
                "plan": [],
                "tools_needed": [],
                "current_step": 0,
                "pending_tools": [],
                "thinking_history": state.get("thinking_history", []) + [thinking],
                "current_thinking": thinking,
                "status": "designing_kicad",
                "messages": state.get("messages", []) + [
                    HumanMessage(content=query),
                ],
            }
        
        else:  # research
            plan_steps = [
                PlanStep(
                    step_number=s.step_number,
                    description=s.description,
                    tool_needed=s.tool_needed,
                    status="pending",
                )
                for s in result.plan
            ]
            
            tools_needed = result.tools_needed or ["web_search"]
            
            thinking = AgentThinking(
                thought=f"Memahami: {result.understanding}",
                evaluation=None,
                memory=None,
                next_goal=f"Research dengan {tools_needed}",
            )
            
            return {
                "understanding": result.understanding,
                "plan": plan_steps,
                "tools_needed": tools_needed,
                "current_step": 0,
                "pending_tools": tools_needed.copy(),
                "thinking_history": state.get("thinking_history", []) + [thinking],
                "current_thinking": thinking,
                "status": "researching",
                "messages": state.get("messages", []) + [
                    HumanMessage(content=query),
                ],
            }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Supervisor error: {e}")
        
        # Handle API errors
        if "PERMISSION_DENIED" in error_msg or "leaked" in error_msg.lower():
            mark_key_disabled(current_key, "PERMISSION_DENIED")
        elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            retry_match = re.search(r'retry in (\d+)', error_msg.lower())
            retry_seconds = int(retry_match.group(1)) if retry_match else 60
            mark_key_rate_limited(current_key, retry_seconds)
        
        # ============================================
        # Level 3: Smart fallback based on query type
        # ============================================
        lower_query = query.lower().strip()
        
        # Simple knowledge queries - route to synthesizer
        simple_keywords = ["apa itu", "jelaskan", "buatkan", "buat function", 
                          "buat code", "bagaimana cara", "cara kerja"]
        needs_research = any(kw in lower_query for kw in 
                            ["harga", "berita", "terbaru", "hari ini", "sekarang", "kurs"])
        
        if any(kw in lower_query for kw in simple_keywords) and not needs_research:
            logger.info("📝 Error fallback: routing to synthesizer")
            return {
                "understanding": query,
                "plan": [],
                "tools_needed": [],
                "status": "synthesizing",
                "messages": state.get("messages", []) + [HumanMessage(content=query)],
            }
        
        # Default: try web search
        logger.info("📝 Error fallback: routing to researcher")
        return {
            "understanding": query,
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
            "errors": state.get("errors", []) + [f"Supervisor error: {e}"],
        }
