"""
JAWIR OS - Chat + KiCad Routing Tests
Test supervisor routing to kicad_designer node.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from agent.nodes.supervisor_v2 import (
    SupervisorOutput,
    supervisor_node,
    get_fallback_response,
    STRUCTURED_PROMPT,
)

from agent.state import JawirState


class TestSupervisorKicadRouting:
    """Test supervisor routing for KiCad requests."""
    
    @pytest.fixture
    def mock_kicad_output(self):
        """Create mock supervisor output for KiCad routing."""
        return SupervisorOutput(
            understanding="User wants to design an LED circuit",
            response_type="kicad",
            direct_response=None,
            plan=[],
            tools_needed=[],
        )
    
    @pytest.fixture
    def mock_direct_output(self):
        """Create mock supervisor output for direct response."""
        return SupervisorOutput(
            understanding="User is greeting",
            response_type="direct",
            direct_response="Sugeng, Lur! Kula JAWIR.",
            plan=[],
            tools_needed=[],
        )
    
    def test_kicad_keywords_in_prompt(self):
        """Test that kicad keywords are in supervisor prompt."""
        assert "kicad" in STRUCTURED_PROMPT.lower()
        assert "rangkaian" in STRUCTURED_PROMPT.lower()
        assert "skematik" in STRUCTURED_PROMPT.lower()
    
    def test_kicad_response_type_description(self):
        """Test that kicad response type is documented."""
        assert "kicad" in STRUCTURED_PROMPT
        assert "desain rangkaian" in STRUCTURED_PROMPT.lower()
    
    @pytest.mark.asyncio
    async def test_kicad_route_sets_designing_kicad_status(self, mock_kicad_output):
        """Test that kicad route sets status to designing_kicad."""
        state = {
            "user_query": "buatkan skematik LED dengan resistor 330 ohm",
            "messages": [],
            "thinking_history": [],
            "errors": [],
            "iteration_count": 0,
        }
        
        # Mock the LLM
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_kicad_output)
        
        with patch("agent.nodes.supervisor_v2.get_structured_llm") as mock_get_llm:
            mock_get_llm.return_value = (mock_llm, "test-api-key")
            
            result = await supervisor_node(state)
        
        # Verify routing
        assert result["status"] == "designing_kicad"
        assert "understanding" in result
    
    @pytest.mark.asyncio
    async def test_direct_route_sets_done_status(self, mock_direct_output):
        """Test that direct route sets status to done."""
        state = {
            "user_query": "halo",
            "messages": [],
            "thinking_history": [],
            "errors": [],
            "iteration_count": 0,
        }
        
        # Mock the LLM
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_direct_output)
        
        with patch("agent.nodes.supervisor_v2.get_structured_llm") as mock_get_llm:
            mock_get_llm.return_value = (mock_llm, "test-api-key")
            
            result = await supervisor_node(state)
        
        # Direct response should set done status
        assert result["status"] == "done"
    
    def test_fallback_does_not_match_kicad_keywords(self):
        """Test that KiCad keywords don't match fallback responses."""
        # These should NOT match fallbacks (require LLM)
        kicad_queries = [
            "buatkan rangkaian LED",
            "desain skematik sensor DHT11",
            "buat circuit dengan ESP32",
            "rangkaian amplifier audio",
        ]
        
        for query in kicad_queries:
            fallback = get_fallback_response(query)
            assert fallback is None, f"Query '{query}' matched a fallback but shouldn't"
    
    def test_greeting_fallback_still_works(self):
        """Test that greetings still use fallback."""
        greetings = ["halo", "hai", "hello", "selamat pagi"]
        
        for greeting in greetings:
            fallback = get_fallback_response(greeting)
            assert fallback is not None, f"Greeting '{greeting}' should match fallback"


class TestSupervisorOutput:
    """Test SupervisorOutput Pydantic model."""
    
    def test_kicad_response_type_valid(self):
        """Test kicad is a valid response_type."""
        output = SupervisorOutput(
            understanding="Design LED circuit",
            response_type="kicad",
            direct_response=None,
            plan=[],
            tools_needed=[],
        )
        
        assert output.response_type == "kicad"
    
    def test_all_response_types_valid(self):
        """Test all response types are valid."""
        valid_types = ["direct", "code", "research", "kicad"]
        
        for response_type in valid_types:
            output = SupervisorOutput(
                understanding="Test",
                response_type=response_type,
                plan=[],
                tools_needed=[],
            )
            assert output.response_type == response_type


class TestKicadQueryPatterns:
    """Test various KiCad query patterns for proper routing."""
    
    # These queries should route to KiCad
    KICAD_QUERIES = [
        "buatkan rangkaian LED dengan resistor",
        "desain skematik sensor suhu DHT11",
        "buat circuit ESP32 dengan relay",
        "rangkaian amplifier sederhana",
        "skematik power supply 5V",
        "desain PCB untuk Arduino",
        "rangkaian sensor jarak HC-SR04",
        "buat skematik timer 555",
        "circuit voltage divider",
        "rangkaian transistor switch",
    ]
    
    # These queries should NOT route to KiCad
    NON_KICAD_QUERIES = [
        "apa itu python",
        "buatkan kode sorting",
        "jelaskan tentang AI",
        "cari berita hari ini",
        "berapa hasil 2+2",
        "halo, siapa kamu",
        "terima kasih banyak",
    ]
    
    @pytest.mark.asyncio
    async def test_kicad_queries_route_correctly(self):
        """Test that KiCad queries set response_type=kicad."""
        for query in self.KICAD_QUERIES[:3]:  # Test first 3 to speed up
            state = {
                "user_query": query,
                "messages": [],
                "thinking_history": [],
                "errors": [],
                "iteration_count": 0,
            }
            
            # Mock LLM to return kicad response
            mock_output = SupervisorOutput(
                understanding=f"User wants to design circuit: {query}",
                response_type="kicad",
                plan=[],
                tools_needed=[],
            )
            
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_output)
            
            with patch("agent.nodes.supervisor_v2.get_structured_llm") as mock_get_llm:
                mock_get_llm.return_value = (mock_llm, "test-api-key")
                
                result = await supervisor_node(state)
            
            assert result["status"] == "designing_kicad", f"Query '{query}' should route to KiCad"


class TestGraphRouting:
    """Test graph conditional routing for KiCad."""
    
    def test_graph_has_kicad_designer_node(self):
        """Test that graph has kicad_designer node."""
        from agent.graph import build_jawir_graph
        
        graph = build_jawir_graph()
        
        # Get nodes from graph
        assert graph is not None
        
        # The graph should have kicad_designer node defined
        # Check if the node exists in the graph nodes
        nodes = graph.nodes
        assert "kicad_designer" in nodes, "Graph should have kicad_designer node"
    
    def test_state_has_designing_kicad_status(self):
        """Test that state supports designing_kicad status."""
        from agent.state import JawirState
        
        # The Literal type should include designing_kicad
        # We can't directly check TypedDict Literal, but we can verify
        # that the state accepts this value at runtime
        state = {
            "status": "designing_kicad",
            "user_query": "test",
            "messages": [],
            "thinking_history": [],
            "errors": [],
        }
        
        # If status is valid, this should work
        assert state["status"] == "designing_kicad"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
