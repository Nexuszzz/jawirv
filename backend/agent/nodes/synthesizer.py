"""
JAWIR OS - Synthesizer Node
Creates the final response from research results.
"""

import logging
from typing import Any
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

from agent.state import JawirState, AgentThinking
from agent.utils import extract_text_from_response
from agent.api_rotator import get_api_key, mark_key_rate_limited, mark_key_disabled
from app.config import settings

logger = logging.getLogger("jawir.agent.synthesizer")


def get_synthesizer_llm() -> tuple[ChatGoogleGenerativeAI, str]:
    """Get Gemini model configured for synthesizer role with rotated API key."""
    api_key = get_api_key()
    return ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        temperature=0.7,
        convert_system_message_to_human=True,
    ), api_key


async def synthesizer_node(state: JawirState) -> dict[str, Any]:
    """
    Synthesizer Node: Creates final response from research.
    
    This node:
    1. Gathers all research findings
    2. Creates a comprehensive, well-structured response
    3. Includes source citations
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with final_response
    """
    logger.info("📝 Synthesizer creating final response...")
    
    user_query = state.get("user_query", "")
    sources = state.get("research_sources", [])
    research_summary = state.get("research_summary", "")
    understanding = state.get("understanding", "")
    
    # Check if already has final response (direct mode from supervisor)
    if state.get("final_response") and state.get("status") == "done":
        logger.info("✅ Using direct response from supervisor")
        return {}  # No updates needed
    
    llm, current_key = get_synthesizer_llm()
    
    # Build context from sources
    if sources:
        sources_context = "\n\n".join([
            f"[Sumber {i+1}] {s['title']}\n{s['content']}"
            for i, s in enumerate(sources[:10])
        ])
        
        synthesis_prompt = f"""Kamu adalah JAWIR, asisten AI yang bijaksana dengan sentuhan Jawa yang sopan.

PERTANYAAN USER:
{user_query}

PEMAHAMAN AWAL:
{understanding}

HASIL PENELITIAN:
{research_summary}

SUMBER-SUMBER:
{sources_context}

---

Tugas: Buatlah jawaban yang komprehensif, informatif, dan mudah dipahami.

ATURAN:
1. Gunakan bahasa Indonesia yang baik dengan sentuhan Jawa yang sopan
2. Jawaban harus berdasarkan FAKTA dari sumber yang ada
3. Jika ada data angka/spesifikasi, tampilkan dalam format yang jelas
4. Jika membandingkan sesuatu, buat tabel perbandingan jika memungkinkan
5. Akhiri dengan kesimpulan atau rekomendasi praktis
6. Jangan membuat informasi yang tidak ada di sumber

FORMAT:
- Mulai dengan sapaan singkat
- Jelaskan temuan utama
- Berikan detail yang relevan
- Tutup dengan kesimpulan/saran

Berikan jawaban:
"""
    else:
        # No sources - answer from knowledge (simple questions)
        synthesis_prompt = f"""Kamu adalah JAWIR, asisten AI yang bijaksana dengan sentuhan Jawa yang sopan.

PERTANYAAN/PESAN USER:
{user_query}

---

Tugasmu adalah menjawab atau merespons pesan user dengan ramah.

ATURAN:
1. Gunakan bahasa Indonesia yang baik dengan sentuhan Jawa yang sopan (misalnya: Sugeng, Lur, monggo, sami-sami)
2. Jika user menyapa, balas sapaannya dengan ramah
3. Jika user bertanya hal sederhana, jawab langsung dengan pengetahuanmu
4. Jika user berterima kasih, sampaikan dengan hangat
5. Selalu tawarkan bantuan lebih lanjut

Berikan respons:
"""
    
    try:
        response = await llm.ainvoke([HumanMessage(content=synthesis_prompt)])
        final_response = extract_text_from_response(response.content)
        
        # Extract source URLs used
        sources_used = list(set(s["url"] for s in sources)) if sources else []
        
        # Create thinking record
        thinking = AgentThinking(
            thought="Menyusun jawaban final",
            evaluation=f"Menggunakan {len(sources)} sumber",
            memory=None,
            next_goal=None,
        )
        
        # Extract thinking process for transparency
        thinking_process = [
            t.get("thought", "") for t in state.get("thinking_history", [])
        ]
        thinking_process.append("Menyintesis jawaban dari hasil penelitian")
        
        logger.info(f"✅ Final response created ({len(final_response)} chars)")
        
        return {
            "final_response": final_response,
            "sources_used": sources_used,
            "status": "done",
            "thinking_history": state.get("thinking_history", []) + [thinking],
            "current_thinking": thinking,
            "messages": state.get("messages", []) + [
                AIMessage(content=final_response),
            ],
        }
        
    except Exception as e:
        import re
        error_msg = str(e)
        logger.error(f"Synthesizer error: {e}")
        
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
        
        # Fallback response
        fallback = (
            f"Mohon maaf, terjadi kendala dalam menyusun jawaban. "
            f"Berdasarkan penelitian singkat, berikut informasi yang tersedia:\n\n"
            f"{research_summary or 'Tidak ada informasi yang berhasil dikumpulkan.'}\n\n"
            f"Silakan coba lagi atau ajukan pertanyaan dengan cara berbeda."
        )
        
        return {
            "final_response": fallback,
            "sources_used": [],
            "status": "done",
            "errors": state.get("errors", []) + [f"Synthesizer error: {e}"],
        }
