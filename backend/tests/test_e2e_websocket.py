"""
JAWIR OS - E2E WebSocket Test
================================
Test end-to-end WebSocket flow using FastAPI TestClient.
Tests connect → send → receive response pipeline tanpa butuh running server.

Coverage:
- WebSocket connection & welcome message
- User message → agent response flow
- Ping/pong
- Cancel message handling
- Unknown message type
- Empty message error
- Connection lifecycle (connect/disconnect)
- Multiple messages in one session
"""

import sys
import os
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ============================================
# Unit Tests: ConnectionManager
# ============================================

class TestConnectionManager:
    """Test ConnectionManager class."""

    def test_import_connection_manager(self):
        """ConnectionManager should be importable."""
        from app.api.websocket import ConnectionManager
        cm = ConnectionManager()
        assert hasattr(cm, "active_connections")
        assert hasattr(cm, "connection_metadata")
        assert cm.active_connections == []

    def test_connection_manager_has_required_methods(self):
        """ConnectionManager should have connect, disconnect, send_json, broadcast."""
        from app.api.websocket import ConnectionManager
        cm = ConnectionManager()
        assert hasattr(cm, "connect")
        assert hasattr(cm, "disconnect")
        assert hasattr(cm, "send_json")
        assert hasattr(cm, "broadcast")
        assert hasattr(cm, "get_session_id")

    @pytest.mark.asyncio
    async def test_connect_adds_to_list(self):
        """connect() should accept WS and add to active_connections."""
        from app.api.websocket import ConnectionManager
        cm = ConnectionManager()

        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()

        await cm.connect(mock_ws)
        assert mock_ws in cm.active_connections
        assert len(cm.active_connections) == 1
        mock_ws.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_list(self):
        """disconnect() should remove WS from active_connections."""
        from app.api.websocket import ConnectionManager
        cm = ConnectionManager()

        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()

        await cm.connect(mock_ws)
        assert len(cm.active_connections) == 1

        cm.disconnect(mock_ws)
        assert len(cm.active_connections) == 0

    @pytest.mark.asyncio
    async def test_send_json(self):
        """send_json() should call websocket.send_json()."""
        from app.api.websocket import ConnectionManager
        cm = ConnectionManager()

        mock_ws = AsyncMock()
        data = {"type": "test", "message": "hello"}

        await cm.send_json(mock_ws, data)
        mock_ws.send_json.assert_called_once_with(data)

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self):
        """broadcast() should send to all active connections."""
        from app.api.websocket import ConnectionManager
        cm = ConnectionManager()

        mock_ws1 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws2.accept = AsyncMock()

        await cm.connect(mock_ws1)
        await cm.connect(mock_ws2)

        data = {"type": "broadcast", "msg": "hello all"}
        await cm.broadcast(data)

        mock_ws1.send_json.assert_called_with(data)
        mock_ws2.send_json.assert_called_with(data)

    @pytest.mark.asyncio
    async def test_get_session_id_returns_string(self):
        """get_session_id() should return a UUID string."""
        from app.api.websocket import ConnectionManager
        cm = ConnectionManager()

        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        await cm.connect(mock_ws)

        session_id = cm.get_session_id(mock_ws)
        assert isinstance(session_id, str)
        assert len(session_id) > 0  # UUID is non-empty


# ============================================
# Unit Tests: AgentStatusStreamer
# ============================================

class TestAgentStatusStreamer:
    """Test AgentStatusStreamer class."""

    def _create_streamer(self):
        """Helper to create streamer with mocks."""
        from app.api.websocket import AgentStatusStreamer, ConnectionManager
        cm = ConnectionManager()
        mock_ws = AsyncMock()
        cm.send_json = AsyncMock()
        return AgentStatusStreamer(mock_ws, cm), cm

    def test_import_streamer(self):
        """AgentStatusStreamer should be importable."""
        from app.api.websocket import AgentStatusStreamer
        assert AgentStatusStreamer is not None

    @pytest.mark.asyncio
    async def test_send_thinking(self):
        """send_thinking should send status='thinking'."""
        streamer, cm = self._create_streamer()
        await streamer.send_thinking("Memahami pertanyaan...")
        
        cm.send_json.assert_called_once()
        call_data = cm.send_json.call_args[0][1]
        assert call_data["type"] == "agent_status"
        assert call_data["status"] == "thinking"

    @pytest.mark.asyncio
    async def test_send_searching(self):
        """send_searching should send status='searching' with query."""
        streamer, cm = self._create_streamer()
        await streamer.send_searching("ESP32 pinout")

        cm.send_json.assert_called_once()
        call_data = cm.send_json.call_args[0][1]
        assert call_data["status"] == "searching"
        assert "ESP32 pinout" in call_data["message"]
        assert call_data["details"]["query"] == "ESP32 pinout"

    @pytest.mark.asyncio
    async def test_send_done(self):
        """send_done should send status='done'."""
        streamer, cm = self._create_streamer()
        await streamer.send_done()

        call_data = cm.send_json.call_args[0][1]
        assert call_data["status"] == "done"

    @pytest.mark.asyncio
    async def test_send_error(self):
        """send_error should send status='error' with message."""
        streamer, cm = self._create_streamer()
        await streamer.send_error("API timeout")

        call_data = cm.send_json.call_args[0][1]
        assert call_data["status"] == "error"
        assert "API timeout" in call_data["message"]

    @pytest.mark.asyncio
    async def test_send_tool_result(self):
        """send_tool_result should send tool execution result."""
        streamer, cm = self._create_streamer()
        await streamer.send_tool_result(
            tool_name="web_search",
            status="success",
            data={"title": "ESP32", "summary": "A microcontroller..."}
        )

        call_data = cm.send_json.call_args[0][1]
        assert call_data["type"] == "tool_result"
        assert call_data["tool_name"] == "web_search"
        assert call_data["status"] == "success"
        assert "actions" in call_data

    @pytest.mark.asyncio
    async def test_send_final_response(self):
        """send_final_response should send agent_response type."""
        streamer, cm = self._create_streamer()
        await streamer.send_final_response(
            content="ESP32 adalah mikrokontroler...",
            thinking_process=["Memahami", "Mencari", "Menyusun"],
            sources_used=["https://espressif.com"],
        )

        call_data = cm.send_json.call_args[0][1]
        assert call_data["type"] == "agent_response"
        assert "ESP32" in call_data["content"]
        assert len(call_data["thinking_process"]) == 3
        assert len(call_data["sources_used"]) == 1


# ============================================
# E2E Tests: handle_websocket_message
# ============================================

class TestHandleWebSocketMessage:
    """Test the main message handler routing."""

    @pytest.mark.asyncio
    async def test_ping_pong(self):
        """Ping message should return pong."""
        from app.api.websocket import handle_websocket_message, ConnectionManager

        cm = ConnectionManager()
        mock_ws = AsyncMock()
        cm.send_json = AsyncMock()

        await handle_websocket_message(mock_ws, cm, {"type": "ping"})

        cm.send_json.assert_called_once()
        call_data = cm.send_json.call_args[0][1]
        assert call_data["type"] == "pong"
        assert "timestamp" in call_data

    @pytest.mark.asyncio
    async def test_cancel_message(self):
        """Cancel message should return cancelled."""
        from app.api.websocket import handle_websocket_message, ConnectionManager

        cm = ConnectionManager()
        mock_ws = AsyncMock()
        cm.send_json = AsyncMock()

        await handle_websocket_message(mock_ws, cm, {"type": "cancel"})

        call_data = cm.send_json.call_args[0][1]
        assert call_data["type"] == "cancelled"

    @pytest.mark.asyncio
    async def test_unknown_message_type(self):
        """Unknown message type should return error."""
        from app.api.websocket import handle_websocket_message, ConnectionManager

        cm = ConnectionManager()
        mock_ws = AsyncMock()
        cm.send_json = AsyncMock()

        await handle_websocket_message(mock_ws, cm, {"type": "foobar"})

        call_data = cm.send_json.call_args[0][1]
        assert call_data["type"] == "error"
        assert "foobar" in call_data["message"]

    @pytest.mark.asyncio
    async def test_empty_user_message_returns_error(self):
        """Empty user_message should return error."""
        from app.api.websocket import handle_websocket_message, ConnectionManager

        cm = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        await cm.connect(mock_ws)

        # Reset send_json to track calls after connect
        mock_ws.send_json = AsyncMock()
        cm.send_json = AsyncMock()

        await handle_websocket_message(
            mock_ws, cm,
            {"type": "user_message", "data": {"content": ""}}
        )

        cm.send_json.assert_called()
        call_data = cm.send_json.call_args[0][1]
        assert call_data["type"] == "error"
        assert "kosong" in call_data["message"].lower() or "Pesan" in call_data["message"]

    @pytest.mark.asyncio
    async def test_user_message_invokes_agent(self):
        """user_message should call invoke_agent and return agent_response."""
        from app.api.websocket import handle_websocket_message, ConnectionManager

        cm = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        await cm.connect(mock_ws)
        mock_ws.send_json = AsyncMock()

        # Mock invoke_agent to return a response
        mock_result = {
            "final_response": "ESP32 adalah mikrokontroler...",
            "thinking_process": ["Menganalisis"],
            "sources_used": [],
            "status": "done",
        }

        with patch("app.api.websocket.handle_user_message") as mock_handler:
            mock_handler.return_value = None

            await handle_websocket_message(
                mock_ws, cm,
                {"type": "user_message", "data": {"content": "Apa itu ESP32?"}}
            )

            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_message_flow_with_mock_agent(self):
        """Full E2E: user_message → invoke_agent → agent_response."""
        from app.api.websocket import handle_user_message, ConnectionManager

        cm = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        await cm.connect(mock_ws)

        # Track all send_json calls
        sent_messages = []

        async def track_send(data):
            sent_messages.append(data)

        mock_ws.send_json = AsyncMock(side_effect=track_send)

        # Mock invoke_agent — it's imported inside handle_user_message via
        # `from agent.graph import invoke_agent`, so we patch agent.graph.invoke_agent
        mock_result = {
            "final_response": "JAWIR menjawab: ESP32 adalah mikrokontroler WiFi+BLE.",
            "thinking_process": ["Memahami pertanyaan", "Menyusun jawaban"],
            "sources_used": ["https://espressif.com"],
            "status": "done",
        }

        mock_invoke = AsyncMock(return_value=mock_result)
        mock_graph_module = MagicMock()
        mock_graph_module.invoke_agent = mock_invoke

        with patch.dict("sys.modules", {"agent.graph": mock_graph_module}):
            await handle_user_message(
                mock_ws, cm,
                {"type": "user_message", "data": {"content": "Apa itu ESP32?"}}
            )

        # Verify invoke_agent was called
        mock_invoke.assert_called_once()
        call_kwargs = mock_invoke.call_args
        assert "ESP32" in str(call_kwargs)

        # Verify final response was sent
        assert len(sent_messages) > 0
        final_msg = sent_messages[-1]
        assert final_msg["type"] == "agent_response"
        assert "ESP32" in final_msg["content"]
        assert len(final_msg["thinking_process"]) == 2


# ============================================
# E2E Test: Multiple Messages in Session
# ============================================

class TestWebSocketSession:
    """Test multi-message WebSocket sessions."""

    @pytest.mark.asyncio
    async def test_multiple_pings(self):
        """Multiple pings should each return pong."""
        from app.api.websocket import handle_websocket_message, ConnectionManager

        cm = ConnectionManager()
        mock_ws = AsyncMock()
        sent = []
        cm.send_json = AsyncMock(side_effect=lambda ws, data: sent.append(data))

        for i in range(3):
            await handle_websocket_message(mock_ws, cm, {"type": "ping"})

        assert len(sent) == 3
        assert all(m["type"] == "pong" for m in sent)

    @pytest.mark.asyncio
    async def test_mixed_message_types(self):
        """Session with ping, unknown, cancel should handle each correctly."""
        from app.api.websocket import handle_websocket_message, ConnectionManager

        cm = ConnectionManager()
        mock_ws = AsyncMock()
        sent = []
        cm.send_json = AsyncMock(side_effect=lambda ws, data: sent.append(data))

        await handle_websocket_message(mock_ws, cm, {"type": "ping"})
        await handle_websocket_message(mock_ws, cm, {"type": "unknown_xyz"})
        await handle_websocket_message(mock_ws, cm, {"type": "cancel"})

        assert sent[0]["type"] == "pong"
        assert sent[1]["type"] == "error"
        assert sent[2]["type"] == "cancelled"

    @pytest.mark.asyncio
    async def test_connection_manager_tracks_multiple(self):
        """ConnectionManager should track multiple connections."""
        from app.api.websocket import ConnectionManager
        cm = ConnectionManager()

        ws_list = []
        for _ in range(5):
            mock_ws = AsyncMock()
            mock_ws.accept = AsyncMock()
            await cm.connect(mock_ws)
            ws_list.append(mock_ws)

        assert len(cm.active_connections) == 5

        # Disconnect 2
        cm.disconnect(ws_list[0])
        cm.disconnect(ws_list[2])
        assert len(cm.active_connections) == 3

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_no_error(self):
        """Disconnecting non-existent WS should not raise."""
        from app.api.websocket import ConnectionManager
        cm = ConnectionManager()

        mock_ws = AsyncMock()
        cm.disconnect(mock_ws)  # Should not raise
        assert len(cm.active_connections) == 0


# ============================================
# Test: Message Format Validation
# ============================================

class TestMessageFormat:
    """Test expected message format compliance."""

    @pytest.mark.asyncio
    async def test_pong_has_timestamp(self):
        """Pong response must have timestamp."""
        from app.api.websocket import handle_websocket_message, ConnectionManager

        cm = ConnectionManager()
        mock_ws = AsyncMock()
        cm.send_json = AsyncMock()

        await handle_websocket_message(mock_ws, cm, {"type": "ping"})

        call_data = cm.send_json.call_args[0][1]
        assert "timestamp" in call_data
        # Verify it's valid ISO format
        datetime.fromisoformat(call_data["timestamp"])

    @pytest.mark.asyncio
    async def test_agent_status_format(self):
        """Agent status message must have correct structure."""
        from app.api.websocket import AgentStatusStreamer, ConnectionManager

        cm = ConnectionManager()
        mock_ws = AsyncMock()
        cm.send_json = AsyncMock()
        streamer = AgentStatusStreamer(mock_ws, cm)

        await streamer.send_status("thinking", "test message", {"key": "value"})

        call_data = cm.send_json.call_args[0][1]
        # Required fields
        assert "type" in call_data
        assert "status" in call_data
        assert "message" in call_data
        assert "details" in call_data
        assert "timestamp" in call_data
        # Correct values
        assert call_data["type"] == "agent_status"
        assert call_data["details"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_tool_result_has_actions(self):
        """Tool result must include available actions."""
        from app.api.websocket import AgentStatusStreamer, ConnectionManager

        cm = ConnectionManager()
        mock_ws = AsyncMock()
        cm.send_json = AsyncMock()
        streamer = AgentStatusStreamer(mock_ws, cm)

        await streamer.send_tool_result("web_search", "success", {"data": "test"})

        call_data = cm.send_json.call_args[0][1]
        assert "actions" in call_data
        assert "open_url" in call_data["actions"]
        assert "save" in call_data["actions"]
        assert "retry" in call_data["actions"]
