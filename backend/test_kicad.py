"""
JAWIR OS - KiCad Tools Unit Tests
Test component library, generator, and templates.
"""

import pytest
import os
import tempfile
from pathlib import Path

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.kicad import (
    # Library
    COMPONENT_LIBRARY,
    COMPONENT_CATEGORIES,
    COMPONENT_COUNT,
    get_component,
    get_available_components,
    get_component_info_for_ai,
    get_pin_position_with_rotation,
    PIN_OFFSET,
    # Schemas
    Position,
    PinReference,
    ComponentPlacement,
    WireConnection,
    SchematicPlan,
    GenerationResult,
    # Generator
    generate_schematic,
    save_schematic,
    KICAD_OUTPUT_DIR,
    # Templates
    TEMPLATES,
    get_template,
    get_available_templates,
    get_template_info_for_ai,
)


class TestComponentLibrary:
    """Test the component library."""
    
    def test_component_count(self):
        """Test that we have the expected number of components."""
        # V2 library has 14 core components (simplified from v1)
        assert COMPONENT_COUNT >= 14, "Should have at least 14 core components"
        assert len(COMPONENT_LIBRARY) == COMPONENT_COUNT
    
    def test_get_component_exists(self):
        """Test getting an existing component."""
        resistor = get_component("resistor")
        assert resistor is not None
        assert resistor.type == "resistor"
        assert resistor.symbol == "Device:R"
        assert resistor.ref_prefix == "R"
        assert len(resistor.pins) == 2
    
    def test_get_component_case_insensitive(self):
        """Test case-insensitive component lookup."""
        r1 = get_component("RESISTOR")
        r2 = get_component("Resistor")
        r3 = get_component("resistor")
        
        assert r1 is not None
        assert r1 == r2 == r3
    
    def test_get_component_not_exists(self):
        """Test getting a non-existent component."""
        result = get_component("nonexistent_component")
        assert result is None
    
    def test_available_components(self):
        """Test getting list of available components."""
        components = get_available_components()
        assert isinstance(components, list)
        assert "resistor" in components
        assert "capacitor" in components
        assert "led" in components
        assert "esp32" in components
        # Note: arduino_uno removed from V2 library (simplified)
    
    def test_pin_offset_constant(self):
        """Test PIN_OFFSET constant."""
        assert PIN_OFFSET == 3.81
    
    def test_component_has_lib_symbol_def(self):
        """Test that components have lib_symbol_def."""
        for comp_type, comp_def in COMPONENT_LIBRARY.items():
            assert comp_def.lib_symbol_def, f"{comp_type} missing lib_symbol_def"
            assert "(symbol" in comp_def.lib_symbol_def
    
    def test_component_categories(self):
        """Test component categories."""
        # V2 library doesn't use categories - components are flat
        # This test is for backwards compatibility check
        # COMPONENT_CATEGORIES is empty dict in V2
        assert isinstance(COMPONENT_CATEGORIES, dict)
    
    def test_component_info_for_ai(self):
        """Test AI-formatted component info."""
        info = get_component_info_for_ai()
        assert isinstance(info, str)
        assert "resistor" in info.lower()
        assert "led" in info.lower()
        assert "esp32" in info.lower()


class TestPinPositionCalculation:
    """Test pin position calculations with rotation."""
    
    def test_pin_position_no_rotation(self):
        """Test pin position without rotation."""
        resistor = get_component("resistor")
        
        # V2 API: get_pin_position(x, y, comp_def, pin_number, rotation)
        x, y = get_pin_position_with_rotation(100, 100, resistor, 1, 0)
        
        # Pin 1 should be above center (negative y offset)
        assert x == 100
        assert y < 100  # Pin 1 is above
    
    def test_pin_position_90_rotation(self):
        """Test pin position with 90 degree rotation."""
        resistor = get_component("resistor")
        
        # V2 API: get_pin_position(x, y, comp_def, pin_number, rotation)
        x, y = get_pin_position_with_rotation(100, 100, resistor, 1, 90)
        
        # After 90° CCW rotation, vertical becomes horizontal
        # Pin 1 was above (0, -3.81), after rotation: (3.81, 0) - to the right
        # Math: x' = dx*cos(90) - dy*sin(90) = 0 - (-3.81)*1 = 3.81
        assert abs(x - (100 + PIN_OFFSET)) < 0.01  # Pin moves to the right
        assert abs(y - 100) < 0.01
    
    def test_pin_position_180_rotation(self):
        """Test pin position with 180 degree rotation."""
        resistor = get_component("resistor")
        
        # V2 API: get_pin_position(x, y, comp_def, pin_number, rotation)
        x, y = get_pin_position_with_rotation(100, 100, resistor, 1, 180)
        
        # Pin 1 was above, now should be below
        assert abs(x - 100) < 0.01
        assert y > 100  # Pin 1 is now below


class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_position_schema(self):
        """Test Position schema."""
        pos = Position(x=127, y=100)
        assert pos.x == 127
        assert pos.y == 100
    
    def test_pin_reference_schema(self):
        """Test PinReference schema."""
        ref = PinReference(component="R1", pin=1)
        assert ref.component == "R1"
        assert ref.pin == 1
    
    def test_component_placement_schema(self):
        """Test ComponentPlacement schema."""
        comp = ComponentPlacement(
            type="resistor",
            reference="R1",
            value="10k",
            position=Position(x=127, y=80),
            rotation=0,
        )
        assert comp.type == "resistor"
        assert comp.reference == "R1"
        assert comp.value == "10k"
    
    def test_wire_connection_schema(self):
        """Test WireConnection schema."""
        wire = WireConnection(
            **{"from": PinReference(component="R1", pin=2)},
            to=PinReference(component="D1", pin=2),
        )
        assert wire.from_.component == "R1"
        assert wire.to.component == "D1"
    
    def test_schematic_plan_schema(self):
        """Test SchematicPlan schema."""
        plan = SchematicPlan(
            project="test_circuit",
            description="Test description",
            components=[
                ComponentPlacement(
                    type="resistor",
                    reference="R1",
                    position=Position(x=127, y=80),
                )
            ],
            wires=[],
        )
        assert plan.project == "test_circuit"
        assert len(plan.components) == 1


class TestTemplates:
    """Test schematic templates."""
    
    def test_templates_exist(self):
        """Test that templates exist."""
        templates = get_available_templates()
        assert len(templates) > 0
        assert "led_indicator" in templates
        assert "voltage_divider" in templates
    
    def test_get_template(self):
        """Test getting a template."""
        led = get_template("led_indicator")
        assert led is not None
        assert led.project == "led_indicator"
        assert len(led.components) >= 2
        assert len(led.wires) >= 2
    
    def test_get_template_case_insensitive(self):
        """Test case-insensitive template lookup."""
        t1 = get_template("LED_INDICATOR")
        t2 = get_template("led_indicator")
        assert t1 == t2
    
    def test_get_template_not_exists(self):
        """Test getting non-existent template."""
        result = get_template("nonexistent_template")
        assert result is None
    
    def test_template_info_for_ai(self):
        """Test AI-formatted template info."""
        info = get_template_info_for_ai()
        assert isinstance(info, str)
        assert "led_indicator" in info.lower()


class TestGenerator:
    """Test schematic generator."""
    
    def test_generate_simple_schematic(self):
        """Test generating a simple schematic."""
        plan = SchematicPlan(
            project="test_led",
            description="Test LED circuit",
            components=[
                ComponentPlacement(
                    type="resistor",
                    reference="R1",
                    value="330",
                    position=Position(x=127, y=80),
                ),
                ComponentPlacement(
                    type="led",
                    reference="D1",
                    value="Red",
                    position=Position(x=127, y=100),
                    rotation=90,
                ),
            ],
            wires=[
                WireConnection(
                    **{"from": PinReference(component="R1", pin=2)},
                    to=PinReference(component="D1", pin=2),
                ),
            ],
        )
        
        content = generate_schematic(plan)
        
        assert "(kicad_sch" in content
        assert "Device:R" in content
        assert "Device:LED" in content
        assert '"R1"' in content
        assert '"D1"' in content
    
    def test_generate_schematic_has_uuid(self):
        """Test that generated schematic has UUIDs."""
        plan = get_template("led_indicator")
        content = generate_schematic(plan)
        
        assert "(uuid" in content
    
    def test_save_schematic(self):
        """Test saving schematic to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan = get_template("led_indicator")
            plan.project = "test_save"
            
            result = save_schematic(plan, Path(tmpdir))
            
            assert result.success
            assert result.project_name == "test_save"
            assert os.path.exists(result.file_path)
            
            # Check file content
            with open(result.file_path, "r") as f:
                content = f.read()
                assert "(kicad_sch" in content


class TestIntegration:
    """Integration tests for the full pipeline."""
    
    def test_template_to_file(self):
        """Test generating file from template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for template_name in get_available_templates():
                plan = get_template(template_name)
                result = save_schematic(plan, Path(tmpdir))
                
                assert result.success, f"Failed for template: {template_name}"
                assert result.component_count > 0
    
    def test_component_wire_routing(self):
        """Test that wires are correctly routed between components."""
        plan = SchematicPlan(
            project="wire_test",
            components=[
                ComponentPlacement(
                    type="resistor",
                    reference="R1",
                    position=Position(x=100, y=80),
                ),
                ComponentPlacement(
                    type="resistor",
                    reference="R2",
                    position=Position(x=100, y=105),
                ),
            ],
            wires=[
                WireConnection(
                    **{"from": PinReference(component="R1", pin=2)},
                    to=PinReference(component="R2", pin=1),
                ),
            ],
        )
        
        content = generate_schematic(plan)
        
        # Should have wire segments
        assert "(wire" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
