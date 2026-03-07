"""
JAWIR OS - WebSocket Handler
Manages WebSocket connections and agent communication.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Optional

from fastapi import WebSocket

logger = logging.getLogger("jawir.websocket")


class ConnectionManager:
    """
    Manages WebSocket connections.
    Handles connect, disconnect, and broadcasting.
    """
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.connection_metadata: dict[int, dict] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_metadata[id(websocket)] = {
            "connected_at": datetime.now().isoformat(),
            "session_id": str(uuid.uuid4()),
        }
        logger.info(f"Connection added. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.connection_metadata.pop(id(websocket), None)
        logger.info(f"Connection removed. Total: {len(self.active_connections)}")
    
    async def send_json(self, websocket: WebSocket, data: dict):
        """Send JSON data to a specific client."""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def broadcast(self, data: dict):
        """Send JSON data to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Broadcast failed for a connection: {e}")
    
    def get_session_id(self, websocket: WebSocket) -> str:
        """Get session ID for a connection."""
        metadata = self.connection_metadata.get(id(websocket), {})
        return metadata.get("session_id", str(uuid.uuid4()))


class AgentStatusStreamer:
    """
    Streams agent status updates to WebSocket client.
    Used by agent nodes to report progress.
    """
    
    def __init__(self, websocket: WebSocket, manager: ConnectionManager):
        self.websocket = websocket
        self.manager = manager
    
    async def send_status(
        self,
        status: str,
        message: str,
        details: Optional[dict] = None,
    ):
        """
        Send agent status update.
        
        Args:
            status: Status type (thinking, searching, reading, writing, done, error)
            message: Human-readable status message
            details: Optional additional details
        """
        await self.manager.send_json(self.websocket, {
            "type": "agent_status",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        })
    
    async def send_thinking(self, thought: str):
        """Send agent's current thought (Chain of Thought)."""
        await self.send_status("thinking", thought)
    
    async def send_searching(self, query: str):
        """Send search status."""
        await self.send_status("searching", f"Mencari: {query}", {"query": query})
    
    async def send_reading(self, source: str):
        """Send reading status."""
        await self.send_status("reading", f"Membaca: {source}", {"source": source})
    
    async def send_writing(self):
        """Send writing/synthesizing status."""
        await self.send_status("writing", "Menyusun jawaban...")
    
    async def send_done(self):
        """Send completion status."""
        await self.send_status("done", "Selesai!")
    
    async def send_error(self, error_message: str):
        """Send error status."""
        await self.send_status("error", error_message)
    
    async def send_tool_result(
        self,
        tool_name: str,
        status: str,
        data: dict,
    ):
        """
        Send tool execution result (displayed as card in UI).
        
        Args:
            tool_name: Name of the tool (web_search, scraper, etc.)
            status: success or error
            data: Result data (title, summary, sources, etc.)
        """
        await self.manager.send_json(self.websocket, {
            "type": "tool_result",
            "tool_name": tool_name,
            "status": status,
            "data": data,
            "actions": ["open_url", "save", "retry"],
            "timestamp": datetime.now().isoformat(),
        })
    
    async def send_research_card(
        self,
        title: str,
        summary: str,
        sources: list[dict],
        table_data: Optional[list[dict]] = None,
    ):
        """
        Send research result card for display in workspace.
        
        Args:
            title: Card title
            summary: Research summary
            sources: List of source dictionaries with url, title, snippet
            table_data: Optional comparison table data
        """
        await self.send_tool_result(
            tool_name="web_search",
            status="success",
            data={
                "title": title,
                "summary": summary,
                "sources": sources,
                "table_data": table_data,
                "sources_count": len(sources),
            }
        )
    
    async def send_final_response(
        self,
        content: str,
        thinking_process: list[str],
        sources_used: list[str],
    ):
        """
        Send final agent response.
        
        Args:
            content: The final response text
            thinking_process: List of thinking steps
            sources_used: List of URLs used
        """
        await self.manager.send_json(self.websocket, {
            "type": "agent_response",
            "content": content,
            "thinking_process": thinking_process,
            "sources_used": sources_used,
            "timestamp": datetime.now().isoformat(),
        })


async def handle_system_command(
    websocket: WebSocket,
    manager: ConnectionManager,
    session_id: str,
    command: str,
):
    """
    Handle system commands like /system:clear_memory.
    
    Args:
        websocket: The WebSocket connection
        manager: ConnectionManager instance
        session_id: Current session ID
        command: The system command (e.g., "/system:clear_memory")
    """
    from memory import get_conversation_store
    
    cmd = command.replace("/system:", "").strip()
    memory_store = get_conversation_store()
    
    if cmd == "clear_memory":
        # Clear session memory
        memory_store.clear_session(session_id)
        await manager.send_json(websocket, {
            "type": "agent_response",
            "content": "✅ Memory cleared! Conversation history has been reset.",
            "thinking_process": [],
            "sources_used": [],
            "timestamp": datetime.now().isoformat(),
        })
    
    elif cmd == "memory_status":
        # Get memory stats
        stats = memory_store.get_session_stats(session_id)
        
        if stats.get("exists"):
            status_msg = f"""📊 Memory Status:
- Messages in memory: {stats['message_count']}
- Summarized messages: {stats['summarized_messages']}
- Has summary: {'Yes' if stats['has_summary'] else 'No'}
- User info: {stats['user_info'] or 'None extracted'}
- Session started: {stats['created_at'][:19]}
- Last activity: {stats['last_activity'][:19]}"""
        else:
            status_msg = "📊 Memory Status: No conversation history yet."
        
        await manager.send_json(websocket, {
            "type": "agent_response",
            "content": status_msg,
            "thinking_process": [],
            "sources_used": [],
            "timestamp": datetime.now().isoformat(),
        })
    
    else:
        await manager.send_json(websocket, {
            "type": "error",
            "message": f"Unknown system command: {cmd}",
            "timestamp": datetime.now().isoformat(),
        })


async def handle_websocket_message(
    websocket: WebSocket,
    manager: ConnectionManager,
    data: dict,
):
    """
    Main handler for incoming WebSocket messages.
    Routes messages to appropriate handlers based on type.
    
    Args:
        websocket: The WebSocket connection
        manager: ConnectionManager instance
        data: Received message data
    """
    message_type = data.get("type", "unknown")
    
    if message_type == "user_message":
        await handle_user_message(websocket, manager, data)
    
    elif message_type == "user_message_with_file":
        await handle_user_message_with_file(websocket, manager, data)
    
    elif message_type == "user_message_with_files":
        await handle_user_message_with_files(websocket, manager, data)
    
    elif message_type == "ping":
        await manager.send_json(websocket, {
            "type": "pong",
            "timestamp": datetime.now().isoformat(),
        })
    
    elif message_type == "cancel":
        # TODO: Implement cancellation
        await manager.send_json(websocket, {
            "type": "cancelled",
            "message": "Request cancelled",
            "timestamp": datetime.now().isoformat(),
        })
    
    else:
        logger.warning(f"Unknown message type: {message_type}")
        await manager.send_json(websocket, {
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.now().isoformat(),
        })


async def handle_user_message(
    websocket: WebSocket,
    manager: ConnectionManager,
    data: dict,
):
    """
    Handle user message and invoke agent.
    
    Args:
        websocket: The WebSocket connection
        manager: ConnectionManager instance
        data: Message data with 'data.content' field
    """
    # Extract content from nested data structure
    message_data = data.get("data", {})
    content = message_data.get("content", "").strip() if isinstance(message_data, dict) else ""
    
    # Use client-provided session_id if available, otherwise generate
    client_session_id = message_data.get("session_id") if isinstance(message_data, dict) else None
    session_id = client_session_id or manager.get_session_id(websocket)
    
    # ============================================
    # Handle System Commands
    # ============================================
    if content.startswith("/system:"):
        await handle_system_command(websocket, manager, session_id, content)
        return
    
    if not content:
        await manager.send_json(websocket, {
            "type": "error",
            "message": "Pesan kosong. Silakan ketik pertanyaan Anda.",
            "timestamp": datetime.now().isoformat(),
        })
        return
    
    logger.info(f"📩 User message ({session_id}): {content[:100]}...")
    
    # Create status streamer
    streamer = AgentStatusStreamer(websocket, manager)
    
    try:
        # Import agent graph (lazy import to avoid circular imports)
        from agent.graph import invoke_agent
        
        # Invoke the agent with streaming
        result = await invoke_agent(
            user_query=content,
            session_id=session_id,
            streamer=streamer,
        )
        
        # Send final response
        await streamer.send_final_response(
            content=result.get("final_response", "Maaf, saya tidak bisa memproses permintaan ini."),
            thinking_process=result.get("thinking_process", []),
            sources_used=result.get("sources_used", []),
        )
        
    except ImportError as e:
        # Agent not yet implemented, send mock response
        logger.warning(f"Agent not implemented yet: {e}")
        
        await streamer.send_thinking("Memahami permintaan Anda...")
        await streamer.send_searching(content)
        
        # Mock response for testing
        await streamer.send_final_response(
            content=f"Terima kasih atas pertanyaan: '{content}'. "
                    f"Agent sedang dalam pengembangan. Mohon tunggu implementasi lengkap.",
            thinking_process=["Menerima pertanyaan", "Menganalisis", "Menyusun respons"],
            sources_used=[],
        )
    
    except Exception as e:
        logger.error(f"Agent error: {e}")
        await streamer.send_error(f"Terjadi kesalahan: {str(e)}")


async def handle_user_message_with_file(
    websocket: WebSocket,
    manager: ConnectionManager,
    data: dict,
):
    """
    Handle user message with attached file.
    
    Args:
        websocket: The WebSocket connection
        manager: ConnectionManager instance
        data: Message data with 'data.content' and 'data.file_id' fields
    """
    message_data = data.get("data", {})
    content = message_data.get("content", "").strip() if isinstance(message_data, dict) else ""
    file_id = message_data.get("file_id", "")
    session_id = manager.get_session_id(websocket)
    
    logger.info(f"📩 User message with file ({session_id}): {content[:50]}... file={file_id}")
    
    # Create status streamer
    streamer = AgentStatusStreamer(websocket, manager)
    
    try:
        # Get file data
        from app.api.upload import get_file_for_agent
        
        file_data = get_file_for_agent(file_id) if file_id else None
        
        if file_id and not file_data:
            await streamer.send_error(f"File tidak ditemukan: {file_id}")
            return
        
        await streamer.send_status("thinking", "Memahami permintaan Anda...")
        
        if file_data:
            file_type = file_data.get("type", "unknown")
            filename = file_data.get("filename", "file")
            
            if file_type == "pdf":
                await streamer.send_status("reading", f"Membaca PDF: {filename}")
                pdf_content = file_data.get("content", "")
                
                # Append PDF content to user query
                enhanced_query = f"{content}\n\n[Isi dokumen PDF '{filename}']\n{pdf_content[:10000]}"
                if len(pdf_content) > 10000:
                    enhanced_query += "\n... [dokumen terpotong]"
            
            elif file_type == "docx":
                await streamer.send_status("reading", f"Membaca dokumen Word: {filename}")
                docx_content = file_data.get("content", "")
                
                # Append Word content to user query
                enhanced_query = f"{content}\n\n[Isi dokumen Word '{filename}']\n{docx_content[:10000]}"
                if len(docx_content) > 10000:
                    enhanced_query += "\n... [dokumen terpotong]"
            
            elif file_type == "excel":
                await streamer.send_status("reading", f"Membaca spreadsheet: {filename}")
                excel_content = file_data.get("content", "")
                
                # Append Excel content to user query
                enhanced_query = f"{content}\n\n[Isi spreadsheet '{filename}']\n{excel_content[:10000]}"
                if len(excel_content) > 10000:
                    enhanced_query += "\n... [dokumen terpotong]"
            
            elif file_type == "text":
                await streamer.send_status("reading", f"Membaca file teks: {filename}")
                text_content = file_data.get("content", "")
                
                # Append text content to user query
                enhanced_query = f"{content}\n\n[Isi file '{filename}']\n{text_content[:10000]}"
                if len(text_content) > 10000:
                    enhanced_query += "\n... [dokumen terpotong]"
            
            elif file_type == "image":
                await streamer.send_status("reading", f"Menganalisis gambar: {filename}")
                # For images, we'll pass to Gemini's multimodal API
                enhanced_query = content
                # File data will be passed separately
            else:
                enhanced_query = content
        else:
            enhanced_query = content
        
        # Import agent graph
        from agent.graph import invoke_agent
        
        # Invoke the agent
        result = await invoke_agent(
            user_query=enhanced_query,
            session_id=session_id,
            streamer=streamer,
            file_data=file_data,  # Pass file data for multimodal
        )
        
        # Send final response
        await streamer.send_final_response(
            content=result.get("final_response", "Maaf, saya tidak bisa memproses permintaan ini."),
            thinking_process=result.get("thinking_process", []),
            sources_used=result.get("sources_used", []),
        )
        
    except Exception as e:
        logger.error(f"Agent error with file: {e}")
        import traceback
        traceback.print_exc()
        await streamer.send_error(f"Terjadi kesalahan: {str(e)}")


async def handle_user_message_with_files(
    websocket: WebSocket,
    manager: ConnectionManager,
    data: dict,
):
    """
    Handle user message with multiple attached files.
    
    Args:
        websocket: The WebSocket connection
        manager: ConnectionManager instance
        data: Message data with 'data.content' and 'data.files' array
    """
    message_data = data.get("data", {})
    content = message_data.get("content", "").strip() if isinstance(message_data, dict) else ""
    files = message_data.get("files", [])
    session_id = manager.get_session_id(websocket)
    
    file_names = [f.get("filename", "unknown") for f in files]
    logger.info(f"📩 User message with {len(files)} files ({session_id}): {content[:50]}... files={file_names}")
    
    # Create status streamer
    streamer = AgentStatusStreamer(websocket, manager)
    
    try:
        from app.api.upload import get_file_for_agent
        
        await streamer.send_status("thinking", "Memahami permintaan Anda...")
        
        # Process all files and build enhanced query
        enhanced_query = content
        all_file_data = []
        image_file_data = None  # Keep track of first image for multimodal
        
        for i, file_info in enumerate(files):
            file_id = file_info.get("file_id", "")
            filename = file_info.get("filename", "unknown")
            
            await streamer.send_status("reading", f"Membaca file {i+1}/{len(files)}: {filename}")
            
            file_data = get_file_for_agent(file_id) if file_id else None
            
            if not file_data:
                enhanced_query += f"\n\n[File tidak ditemukan: {filename}]"
                continue
            
            all_file_data.append(file_data)
            file_type = file_data.get("type", "unknown")
            
            if file_type == "pdf":
                pdf_content = file_data.get("content", "")
                enhanced_query += f"\n\n[Isi dokumen PDF '{filename}']\n{pdf_content[:8000]}"
                if len(pdf_content) > 8000:
                    enhanced_query += "\n... [dokumen terpotong]"
            
            elif file_type == "docx":
                docx_content = file_data.get("content", "")
                enhanced_query += f"\n\n[Isi dokumen Word '{filename}']\n{docx_content[:8000]}"
                if len(docx_content) > 8000:
                    enhanced_query += "\n... [dokumen terpotong]"
            
            elif file_type == "excel":
                excel_content = file_data.get("content", "")
                enhanced_query += f"\n\n[Isi spreadsheet '{filename}']\n{excel_content[:8000]}"
                if len(excel_content) > 8000:
                    enhanced_query += "\n... [dokumen terpotong]"
            
            elif file_type == "text":
                text_content = file_data.get("content", "")
                enhanced_query += f"\n\n[Isi file '{filename}']\n{text_content[:8000]}"
                if len(text_content) > 8000:
                    enhanced_query += "\n... [dokumen terpotong]"
            
            elif file_type == "image":
                # Keep first image for multimodal processing
                if image_file_data is None:
                    image_file_data = file_data
                enhanced_query += f"\n\n[Gambar: {filename}]"
        
        await streamer.send_status("thinking", f"Memproses {len(all_file_data)} file...")
        
        # Import agent graph
        from agent.graph import invoke_agent
        
        # Invoke the agent - pass first image for multimodal if present
        result = await invoke_agent(
            user_query=enhanced_query,
            session_id=session_id,
            streamer=streamer,
            file_data=image_file_data,  # Pass first image for multimodal
        )
        
        # Send final response
        await streamer.send_final_response(
            content=result.get("final_response", "Maaf, saya tidak bisa memproses permintaan ini."),
            thinking_process=result.get("thinking_process", []),
            sources_used=result.get("sources_used", []),
        )
        
    except Exception as e:
        logger.error(f"Agent error with files: {e}")
        import traceback
        traceback.print_exc()
        await streamer.send_error(f"Terjadi kesalahan: {str(e)}")

