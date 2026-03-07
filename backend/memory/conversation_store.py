"""
JAWIR OS - Conversation Memory Store
=====================================
Menyimpan dan mengelola conversation history per session.

Features:
- In-memory storage (persist selama server running)
- Auto-summarization setiap 5 pesan menggunakan Gemini Flash
- Limit 10 pesan terakhir + summary
- Thread-safe untuk async usage
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import json

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

logger = logging.getLogger("jawir.memory")


@dataclass
class ConversationSummary:
    """Summary of older messages."""
    content: str
    message_count: int
    created_at: str
    topics: List[str] = field(default_factory=list)


@dataclass
class SessionMemory:
    """Memory for a single session."""
    session_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[ConversationSummary] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    user_info: Dict[str, Any] = field(default_factory=dict)  # nama, preferensi, dll
    

class ConversationStore:
    """
    In-memory conversation store with auto-summarization.
    
    Strategy:
    - Keep last 10 messages in full
    - Every 5 messages, summarize older ones
    - Store user info extracted from conversation (nama, dll)
    """
    
    # Class-level storage (shared across instances, persist during server lifetime)
    _sessions: Dict[str, SessionMemory] = {}
    _lock = asyncio.Lock()
    
    # Config
    MAX_MESSAGES = 10  # Keep last N messages in full
    SUMMARIZE_THRESHOLD = 5  # Summarize every N messages
    
    def __init__(self):
        self._summarizer = None  # Lazy init
    
    async def _get_summarizer(self):
        """Get or create Gemini Flash summarizer."""
        if self._summarizer is None:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                import os
                
                # Use Gemini Flash for summarization (cheaper & faster)
                self._summarizer = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    google_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
                    temperature=0.3,
                )
                logger.info("✅ Gemini Flash summarizer initialized")
            except Exception as e:
                logger.warning(f"⚠️ Could not init summarizer: {e}")
                self._summarizer = None
        return self._summarizer
    
    def _get_or_create_session(self, session_id: str) -> SessionMemory:
        """Get existing session or create new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMemory(session_id=session_id)
            logger.info(f"📝 Created new session: {session_id[:8]}...")
        return self._sessions[session_id]
    
    async def add_message(
        self,
        session_id: str,
        role: str,  # "user" or "assistant"
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a message to session history.
        
        Args:
            session_id: Unique session identifier
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata (tools used, etc)
        """
        async with self._lock:
            session = self._get_or_create_session(session_id)
            
            # Add message
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
            }
            session.messages.append(message)
            session.last_activity = datetime.now().isoformat()
            
            # Extract user info if present
            if role == "user":
                await self._extract_user_info(session, content)
            
            # Check if we need to summarize
            if len(session.messages) > self.MAX_MESSAGES:
                await self._maybe_summarize(session)
            
            logger.debug(f"💬 Added {role} message to session {session_id[:8]}... (total: {len(session.messages)})")
    
    async def _extract_user_info(self, session: SessionMemory, content: str) -> None:
        """Extract user info from message (nama, dll)."""
        content_lower = content.lower()
        
        # Common Indonesian/English words that are NOT names
        non_name_words = {
            "seorang", "adalah", "orang", "yang", "ini", "itu", "dan", "atau",
            "juga", "bisa", "akan", "sudah", "belum", "sedang", "sangat", "sekali",
            "developer", "programmer", "engineer", "mahasiswa", "pelajar", "pekerja",
            "dari", "untuk", "dengan", "pada", "ke", "di", "the", "a", "an", "is", "am", "are",
            "working", "here", "there", "new", "old", "just", "really", "very",
        }
        
        # Specific name patterns (ordered by specificity - most specific first)
        # HANYA pattern yang jelas untuk nama, tidak termasuk "saya" atau "aku" saja
        name_patterns = [
            "nama saya ", "namaku ", "nama ku ", "panggil saya ", "panggil aku ",
            "my name is ", "call me ", "i'm called ", "they call me ",
        ]
        
        for pattern in name_patterns:
            if pattern in content_lower:
                # Extract potential name
                idx = content_lower.find(pattern) + len(pattern)
                remaining = content[idx:].strip()
                
                # Take first word as potential name
                words = remaining.split()
                if not words:
                    continue
                    
                potential_name = words[0].rstrip(",.:;!?")
                
                # Validate: must be alpha, 2+ chars, not a common word
                if (potential_name 
                    and len(potential_name) >= 2 
                    and potential_name.isalpha()
                    and potential_name.lower() not in non_name_words):
                    
                    session.user_info["name"] = potential_name.capitalize()
                    logger.info(f"👤 Extracted user name: {session.user_info['name']}")
                    return  # Exit after first valid extraction
    
    async def _maybe_summarize(self, session: SessionMemory) -> None:
        """Summarize older messages if threshold reached."""
        # Keep last MAX_MESSAGES, summarize the rest
        if len(session.messages) <= self.MAX_MESSAGES:
            return
        
        # Messages to summarize
        to_summarize = session.messages[:-self.MAX_MESSAGES]
        
        # Keep recent messages
        session.messages = session.messages[-self.MAX_MESSAGES:]
        
        # Create summary
        summarizer = await self._get_summarizer()
        if summarizer and to_summarize:
            try:
                # Build conversation text
                conv_text = "\n".join([
                    f"{m['role'].upper()}: {m['content'][:500]}"
                    for m in to_summarize
                ])
                
                # Summarize with Gemini Flash
                prompt = f"""Rangkum percakapan berikut dalam 2-3 kalimat singkat.
Fokus pada: informasi penting, nama user, topik yang dibahas, dan konteks yang perlu diingat.

PERCAKAPAN:
{conv_text}

RANGKUMAN (dalam Bahasa Indonesia):"""

                response = await summarizer.ainvoke([HumanMessage(content=prompt)])
                summary_text = response.content.strip()
                
                # Merge with existing summary if any
                if session.summary:
                    old_summary = session.summary.content
                    merge_prompt = f"""Gabungkan dua rangkuman ini menjadi satu rangkuman singkat (2-3 kalimat):

RANGKUMAN LAMA:
{old_summary}

RANGKUMAN BARU:
{summary_text}

RANGKUMAN GABUNGAN:"""
                    merge_response = await summarizer.ainvoke([HumanMessage(content=merge_prompt)])
                    summary_text = merge_response.content.strip()
                    total_messages = session.summary.message_count + len(to_summarize)
                else:
                    total_messages = len(to_summarize)
                
                session.summary = ConversationSummary(
                    content=summary_text,
                    message_count=total_messages,
                    created_at=datetime.now().isoformat(),
                )
                
                logger.info(f"📋 Summarized {len(to_summarize)} messages for session {session.session_id[:8]}...")
                
            except Exception as e:
                logger.warning(f"⚠️ Summarization failed: {e}")
                # Fallback: just keep a simple summary
                session.summary = ConversationSummary(
                    content=f"[Percakapan sebelumnya: {len(to_summarize)} pesan]",
                    message_count=len(to_summarize),
                    created_at=datetime.now().isoformat(),
                )
    
    def get_history(
        self,
        session_id: str,
        as_langchain: bool = False,
    ) -> List[Any]:
        """
        Get conversation history for session.
        
        Args:
            session_id: Session to retrieve
            as_langchain: If True, return as LangChain messages
            
        Returns:
            List of messages (dict or BaseMessage)
        """
        logger.info(f"📖 get_history called for session {session_id[:8]}...")
        logger.info(f"   Available sessions: {list(self._sessions.keys())}")
        
        session = self._sessions.get(session_id)
        if not session:
            logger.warning(f"   ❌ Session not found!")
            return []
        
        logger.info(f"   ✅ Found session with {len(session.messages)} messages")
        logger.info(f"   User info: {session.user_info}")
        
        messages = []
        
        # Add summary as system context if exists
        if session.summary:
            summary_msg = f"[Konteks percakapan sebelumnya: {session.summary.content}]"
            if as_langchain:
                messages.append(SystemMessage(content=summary_msg))
            else:
                messages.append({"role": "system", "content": summary_msg})
        
        # Add user info as context
        if session.user_info:
            user_context = "Informasi user: " + ", ".join([
                f"{k}={v}" for k, v in session.user_info.items()
            ])
            if as_langchain:
                messages.append(SystemMessage(content=user_context))
            else:
                messages.append({"role": "system", "content": user_context})
        
        # Add recent messages
        for msg in session.messages:
            if as_langchain:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))
            else:
                messages.append(msg)
        
        return messages
    
    def get_user_info(self, session_id: str) -> Dict[str, Any]:
        """Get extracted user info for session."""
        session = self._sessions.get(session_id)
        return session.user_info if session else {}
    
    def clear_session(self, session_id: str) -> bool:
        """Clear all memory for a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"🗑️ Cleared session: {session_id[:8]}...")
            return True
        return False
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        session = self._sessions.get(session_id)
        if not session:
            return {"exists": False}
        
        return {
            "exists": True,
            "message_count": len(session.messages),
            "has_summary": session.summary is not None,
            "summarized_messages": session.summary.message_count if session.summary else 0,
            "user_info": session.user_info,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
        }
    
    def get_all_sessions(self) -> List[str]:
        """Get all active session IDs."""
        return list(self._sessions.keys())
    
    def clear_all(self) -> int:
        """Clear all sessions. Returns count of cleared sessions."""
        count = len(self._sessions)
        self._sessions.clear()
        logger.info(f"🗑️ Cleared all {count} sessions")
        return count


# Singleton instance
_store: Optional[ConversationStore] = None


def get_conversation_store() -> ConversationStore:
    """Get the singleton ConversationStore instance."""
    global _store
    if _store is None:
        _store = ConversationStore()
    return _store
