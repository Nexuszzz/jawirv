"""
JAWIR OS - KiCad Integration Tests
Test the KiCad designer node with mock LLM responses.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from tools.kicad import (
    SchematicPlan,
    ComponentPlacement,
    WireConnection,
    PinReference,
    Position,
    GenerationResult,
    save_schematic,
    get_template,
    get_available_templates,
    KICAD_OUTPUT_DIR,
)

from agent.nodes.kicad_designer import (
    KicadDesignOutput,
    parse_design_to_plan,
    kicad_designer_node,
    KICAD_DESIGNER_PROMPT,
)

from agent.state import JawirState


class TestParseDesignToPlan:
    """Test conversion from AI output to SchematicPlan."""
    
    def test_parse_simple_design(self):
        """Test parsing a simple design with one component."""
        design = KicadDesignOutput(
            project="test_project",
            description="Test circuit",
            use_template=None,
            components=[
                {
                    "type": "resistor",
                    "reference": "R1",
                    "value": "1k",
                    "position": {"x": 100, "y": 100},
                    "rotation": 0,
                }
            ],
            wires=[],
            labels=[],
            open_kicad=False,
            explanation="Simple resistor test",
        )
        
        plan = parse_design_to_plan(design)
        
        assert plan.project == "test_project"
        assert plan.description == "Test circuit"
        assert len(plan.components) == 1
        assert plan.components[0].type == "resistor"
        assert plan.components[0].reference == "R1"
        assert plan.components[0].value == "1k"
        assert plan.components[0].position.x == 100
        assert plan.components[0].position.y == 100
    
    def test_parse_design_with_wires(self):
        """Test parsing design with wire connections."""
        design = KicadDesignOutput(
            project="led_circuit",
            description="LED with resistor",
            use_template=None,
            components=[
                {
                    "type": "resistor",
                    "reference": "R1",
                    "value": "330",
                    "position": {"x": 127, "y": 80},
                },
                {
                    "type": "led",
                    "reference": "D1",
                    "value": "Red",
                    "position": {"x": 127, "y": 100},
                },
            ],
            wires=[
                {
                    "from": {"component": "VCC", "pin": 1},
                    "to": {"component": "R1", "pin": 1},
                },
                {
                    "from": {"component": "R1", "pin": 2},
                    "to": {"component": "D1", "pin": 2},
                },
                {
                    "from": {"component": "D1", "pin": 1},
                    "to": {"component": "GND", "pin": 1},
                },
            ],
            labels=[],
            open_kicad=False,
            explanation="LED circuit with current limiting resistor",
        )
        
        plan = parse_design_to_plan(design)
        
        assert len(plan.components) == 2
        assert len(plan.wires) == 3
        
        # Check wire connections
        wire1 = plan.wires[0]
        assert wire1.from_.component == "VCC"
        assert wire1.from_.pin == 1
        assert wire1.to.component == "R1"
        assert wire1.to.pin == 1
    
    def test_parse_design_with_labels(self):
        """Test parsing design with power labels."""
        design = KicadDesignOutput(
            project="power_test",
            description="Power test",
            use_template=None,
            components=[
                {
                    "type": "capacitor",
                    "reference": "C1",
                    "value": "100n",
                    "position": {"x": 127, "y": 100},
                },
            ],
            wires=[],
            labels=[
                {"name": "VCC", "x": 127, "y": 80},
                {"name": "GND", "x": 127, "y": 120},
            ],
            open_kicad=False,
            explanation="Power supply with decoupling cap",
        )
        
        plan = parse_design_to_plan(design)
        
        assert plan.labels is not None
        assert len(plan.labels) == 2
        assert plan.labels[0].name == "VCC"
        assert plan.labels[1].name == "GND"


class TestKicadDesignOutput:
    """Test KicadDesignOutput Pydantic model."""
    
    def test_minimal_output(self):
        """Test minimal required fields."""
        output = KicadDesignOutput(
            project="minimal",
            explanation="Minimal test",
        )
        
        assert output.project == "minimal"
        assert output.components == []
        assert output.wires == []
        assert output.labels == []
        assert output.open_kicad is False
    
    def test_full_output(self):
        """Test full output with all fields."""
        output = KicadDesignOutput(
            project="full_project",
            description="Full description",
            use_template="led_indicator",
            components=[],
            wires=[],
            labels=[],
            open_kicad=True,
            explanation="Full explanation",
        )
        
        assert output.use_template == "led_indicator"
        assert output.open_kicad is True


class TestTemplateIntegration:
    """Test template-based schematic generation."""
    
    def test_led_indicator_template(self):
        """Test LED indicator template generates valid schematic."""
        template = get_template("led_indicator")
        assert template is not None
        
        result = save_schematic(template)
        
        assert result.success
        assert result.component_count > 0
        assert result.wire_count > 0
        assert os.path.exists(result.file_path)
        
        # Clean up
        os.remove(result.file_path)
    
    def test_voltage_divider_template(self):
        """Test voltage divider template generates valid schematic."""
        template = get_template("voltage_divider")
        assert template is not None
        
        result = save_schematic(template)
        
        assert result.success
        assert result.component_count > 0
        assert os.path.exists(result.file_path)
        
        # Clean up
        os.remove(result.file_path)
    
    def test_all_templates_generate(self):
        """Test all available templates generate valid schematics."""
        templates = get_available_templates()
        
        for template_name in templates:
            template = get_template(template_name)
            assert template is not None, f"Template {template_name} not found"
            
            result = save_schematic(template)
            assert result.success, f"Template {template_name} failed: {result.message}"
            assert os.path.exists(result.file_path), f"File not created for {template_name}"
            
            # Verify file content
            with open(result.file_path, 'r') as f:
                content = f.read()
            assert "(kicad_sch" in content
            assert "(symbol" in content or "(wire" in content
            
            # Clean up
            os.remove(result.file_path)


class TestKicadDesignerNode:
    """Test the kicad_designer_node async function."""
    
    @pytest.fixture
    def mock_state(self):
        """Create a mock JawirState."""
        return {
            "user_query": "buatkan rangkaian LED dengan resistor 330 ohm",
            "messages": [],
            "thinking_history": [],
            "errors": [],
        }
    
    @pytest.fixture
    def template_state(self):
        """Create a state for template request."""
        return {
            "user_query": "buatkan rangkaian led indicator",
            "messages": [],
            "thinking_history": [],
            "errors": [],
        }
    
    @pytest.mark.asyncio
    async def test_template_match_led_indicator(self, template_state):
        """Test that 'led indicator' query matches template."""
        # The node should detect "led indicator" and use template
        result = await kicad_designer_node(template_state)
        
        assert result["status"] == "done"
        assert "berhasil" in result["final_response"].lower()
        assert "led_indicator" in result["final_response"]
        
        # Clean up generated file
        file_path = None
        for line in result["final_response"].split("\n"):
            if "File:" in line:
                file_path = line.split("`")[1] if "`" in line else None
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    
    @pytest.mark.asyncio
    async def test_custom_design_with_mock(self, mock_state):
        """Test custom design flow with mocked LLM."""
        # Mock the LLM response
        mock_design = KicadDesignOutput(
            project="led_resistor_test",
            description="LED dengan resistor 330 ohm",
            use_template=None,
            components=[
                {
                    "type": "resistor",
                    "reference": "R1",
                    "value": "330",
                    "position": {"x": 127, "y": 80},
                },
                {
                    "type": "led",
                    "reference": "D1",
                    "value": "Red",
                    "position": {"x": 127, "y": 100},
                },
            ],
            wires=[
                {
                    "from": {"component": "VCC", "pin": 1},
                    "to": {"component": "R1", "pin": 1},
                },
                {
                    "from": {"component": "R1", "pin": 2},
                    "to": {"component": "D1", "pin": 2},
                },
                {
                    "from": {"component": "D1", "pin": 1},
                    "to": {"component": "GND", "pin": 1},
                },
            ],
            labels=[],
            open_kicad=False,
            explanation="Rangkaian LED sederhana dengan resistor 330 ohm untuk membatasi arus",
        )
        
        # Create mock LLM
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_design)
        
        with patch("agent.nodes.kicad_designer.get_kicad_llm") as mock_get_llm:
            mock_get_llm.return_value = (mock_llm, "test-api-key")
            
            result = await kicad_designer_node(mock_state)
        
        assert result["status"] == "done"
        assert "berhasil" in result["final_response"].lower()
        assert "led_resistor_test" in result["final_response"]
        
        # Clean up
        if "File:" in result["final_response"]:
            for line in result["final_response"].split("\n"):
                if "File:" in line and "`" in line:
                    file_path = line.split("`")[1]
                    if os.path.exists(file_path):
                        os.remove(file_path)


class TestPromptContent:
    """Test the KICAD_DESIGNER_PROMPT content."""
    
    def test_prompt_has_component_placeholder(self):
        """Test prompt has component_info placeholder."""
        assert "{component_info}" in KICAD_DESIGNER_PROMPT
    
    def test_prompt_has_template_placeholder(self):
        """Test prompt has template_info placeholder."""
        assert "{template_info}" in KICAD_DESIGNER_PROMPT
    
    def test_prompt_has_design_rules(self):
        """Test prompt contains design rules."""
        assert "ATURAN" in KICAD_DESIGNER_PROMPT
        assert "rotation" in KICAD_DESIGNER_PROMPT.lower()
    
    def test_prompt_has_example(self):
        """Test prompt contains example."""
        assert "CONTOH" in KICAD_DESIGNER_PROMPT
        assert "components" in KICAD_DESIGNER_PROMPT


class TestEndToEndFlow:
    """Test complete end-to-end flow without mocking LLM."""
    
    def test_template_to_schematic_file(self):
        """Test complete flow from template to file."""
        # Get template
        plan = get_template("npn_switch")
        assert plan is not None
        
        # Generate schematic
        result = save_schematic(plan)
        
        # Verify result
        assert result.success
        assert result.file_path is not None
        assert os.path.exists(result.file_path)
        
        # Verify file content structure
        with open(result.file_path, 'r') as f:
            content = f.read()
        
        # Check KiCad file structure
        assert content.startswith("(kicad_sch")
        assert "(version" in content
        assert "(uuid" in content
        
        # Check components are present (V2 generator format)
        assert "(symbol" in content and "lib_id" in content
        
        # Clean up
        os.remove(result.file_path)
    
    def test_custom_plan_to_schematic_file(self):
        """Test creating schematic from custom plan."""
        # Create custom plan
        plan = SchematicPlan(
            project="integration_test_custom",
            description="Custom integration test schematic",
            components=[
                ComponentPlacement(
                    type="resistor",
                    reference="R1",
                    value="10k",
                    position=Position(x=127, y=80),
                ),
                ComponentPlacement(
                    type="resistor",
                    reference="R2",
                    value="10k",
                    position=Position(x=152, y=80),
                ),
                ComponentPlacement(
                    type="capacitor",
                    reference="C1",
                    value="100n",
                    position=Position(x=140, y=100),
                ),
            ],
            wires=[
                WireConnection(
                    **{"from": PinReference(component="R1", pin=2)},
                    to=PinReference(component="R2", pin=1),
                ),
            ],
        )
        
        # Generate schematic
        result = save_schematic(plan)
        
        # Verify
        assert result.success
        assert result.component_count == 3
        assert result.wire_count == 1
        assert os.path.exists(result.file_path)
        
        # Read and verify content
        with open(result.file_path, 'r') as f:
            content = f.read()
        
        assert "R1" in content
        assert "R2" in content
        assert "C1" in content
        assert "(wire" in content
        
        # Clean up
        os.remove(result.file_path)


class TestErrorHandling:
    """Test error handling in KiCad designer."""
    
    def test_invalid_component_type(self):
        """Test handling of invalid component type."""
        plan = SchematicPlan(
            project="error_test",
            components=[
                ComponentPlacement(
                    type="invalid_component_xyz",
                    reference="X1",
                    position=Position(x=100, y=100),
                ),
            ],
            wires=[],
        )
        
        result = save_schematic(plan)
        
        # Should still generate but with warning/error
        # The generator should handle unknown components gracefully
        assert result is not None
        if not result.success:
            assert "invalid" in result.message.lower() or result.errors
    
    def test_missing_component_for_wire(self):
        """Test wire referencing non-existent component."""
        plan = SchematicPlan(
            project="wire_error_test",
            components=[
                ComponentPlacement(
                    type="resistor",
                    reference="R1",
                    position=Position(x=100, y=100),
                ),
            ],
            wires=[
                WireConnection(
                    **{"from": PinReference(component="R1", pin=1)},
                    to=PinReference(component="R_NONEXISTENT", pin=1),
                ),
            ],
        )
        
        result = save_schematic(plan)
        
        # Should handle gracefully - either fail or generate with warning
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
