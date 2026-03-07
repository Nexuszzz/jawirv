"""
JAWIR OS - KiCad Schematic Generator V2
FIXED: Proper symbol rendering and wire routing that ACTUALLY WORKS.

This is a complete rewrite with:
1. Correct symbol definitions with proper pins
2. Pin positions that MATCH the symbol definitions
3. Wire routing that connects to actual pin locations
4. Proper reference annotation (R1, R2, not R?)
"""

import uuid
from dataclasses import dataclass, field
from typing import Literal
from datetime import datetime
import math

# Handle both relative and direct imports
try:
    from .library_v2 import (
        COMPONENT_LIBRARY,
        ComponentDefinition,
        get_component,
        get_pin_position,
        PIN_OFFSET,
    )
except ImportError:
    from library_v2 import (
        COMPONENT_LIBRARY,
        ComponentDefinition,
        get_component,
        get_pin_position,
        PIN_OFFSET,
    )


# ============================================
# CONSTANTS
# ============================================

KICAD_VERSION = 20231120
GENERATOR = "jawir_os"
GRID_SIZE = 2.54  # Standard KiCad grid in mm


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class PlacedComponent:
    """A component that has been placed on the schematic."""
    id: str
    type: str  # Key in COMPONENT_LIBRARY
    x: float
    y: float
    rotation: float = 0
    value: str = ""
    reference: str = ""  # Will be auto-assigned: R1, R2, etc.
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Store resolved definition
    _definition: ComponentDefinition | None = None
    
    @property
    def definition(self) -> ComponentDefinition:
        if self._definition is None:
            self._definition = get_component(self.type)
        return self._definition
    
    def get_pin_position(self, pin_number: int | str) -> tuple[float, float]:
        """Get absolute position of a pin."""
        return get_pin_position(self.x, self.y, self.definition, pin_number, self.rotation)


@dataclass
class Wire:
    """A wire connection between two points."""
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Junction:
    """A junction point where wires connect."""
    x: float
    y: float
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Label:
    """A text label on the schematic."""
    text: str
    x: float
    y: float
    rotation: float = 0
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))


# ============================================
# SCHEMATIC GENERATOR
# ============================================

class SchematicGenerator:
    """Generate KiCad schematic files with proper symbols and wiring."""
    
    def __init__(self):
        self.components: list[PlacedComponent] = []
        self.wires: list[Wire] = []
        self.junctions: list[Junction] = []
        self.labels: list[Label] = []
        
        # Reference counters for each prefix (R, C, D, U, Q, etc.)
        self.ref_counters: dict[str, int] = {}
        
        # Track used lib symbols
        self.used_symbols: set[str] = set()
    
    def _next_reference(self, prefix: str) -> str:
        """Get next reference designator for a prefix."""
        if prefix not in self.ref_counters:
            self.ref_counters[prefix] = 0
        self.ref_counters[prefix] += 1
        return f"{prefix}{self.ref_counters[prefix]}"
    
    def add_component(
        self,
        component_type: str,
        x: float,
        y: float,
        rotation: float = 0,
        value: str | None = None,
        component_id: str | None = None,
    ) -> PlacedComponent:
        """
        Add a component to the schematic.
        
        Args:
            component_type: Type from COMPONENT_LIBRARY (e.g., 'resistor', 'led')
            x, y: Position in mm (center of component)
            rotation: Rotation in degrees (0, 90, 180, 270)
            value: Component value (e.g., '10k' for resistor)
            component_id: Optional ID for referencing
        
        Returns:
            PlacedComponent instance
        """
        comp_def = get_component(component_type)
        if not comp_def:
            raise ValueError(f"Unknown component type: {component_type}")
        
        # Use default value if not specified
        actual_value = value or comp_def.default_value
        
        # Generate reference
        reference = self._next_reference(comp_def.ref_prefix)
        
        # Create component
        component = PlacedComponent(
            id=component_id or f"{component_type}_{len(self.components)}",
            type=component_type,
            x=x,
            y=y,
            rotation=rotation,
            value=actual_value,
            reference=reference,
            _definition=comp_def,
        )
        
        self.components.append(component)
        self.used_symbols.add(comp_def.symbol)
        
        return component
    
    def add_wire(
        self,
        start_x: float, start_y: float,
        end_x: float, end_y: float
    ) -> Wire:
        """Add a wire between two points."""
        wire = Wire(start_x, start_y, end_x, end_y)
        self.wires.append(wire)
        return wire
    
    def add_wire_between_pins(
        self,
        comp1: PlacedComponent, pin1: int | str,
        comp2: PlacedComponent, pin2: int | str
    ) -> list[Wire]:
        """
        Add wires to connect two component pins.
        Uses L-shaped routing (horizontal then vertical).
        
        Returns list of wires created.
        """
        # Get actual pin positions
        x1, y1 = comp1.get_pin_position(pin1)
        x2, y2 = comp2.get_pin_position(pin2)
        
        created_wires = []
        
        # If straight line possible
        if abs(x1 - x2) < 0.01 or abs(y1 - y2) < 0.01:
            # Direct connection
            wire = self.add_wire(x1, y1, x2, y2)
            created_wires.append(wire)
        else:
            # L-shaped routing: horizontal first, then vertical
            # Midpoint for the corner
            mid_x = x2
            mid_y = y1
            
            wire1 = self.add_wire(x1, y1, mid_x, mid_y)
            wire2 = self.add_wire(mid_x, mid_y, x2, y2)
            created_wires.extend([wire1, wire2])
        
        return created_wires
    
    def add_junction(self, x: float, y: float) -> Junction:
        """Add a junction point."""
        junction = Junction(x, y)
        self.junctions.append(junction)
        return junction
    
    def add_label(
        self,
        text: str,
        x: float, y: float,
        rotation: float = 0
    ) -> Label:
        """Add a text label."""
        label = Label(text, x, y, rotation)
        self.labels.append(label)
        return label
    
    def _generate_lib_symbols(self) -> str:
        """Generate lib_symbols section with all used symbols."""
        lines = ["  (lib_symbols"]
        
        for comp in self.components:
            comp_def = comp.definition
            if comp_def and comp_def.symbol not in [c.definition.symbol for c in self.components[:self.components.index(comp)]]:
                # Only add each symbol once
                lines.append(comp_def.lib_symbol_def)
        
        lines.append("  )")
        return "\n".join(lines)
    
    def _generate_symbol_instance(self, comp: PlacedComponent) -> str:
        """Generate symbol instance for a component."""
        comp_def = comp.definition
        
        # Calculate mirror settings based on rotation
        # KiCad uses mirror_x and mirror_y for flipping
        mirror = ""
        
        return f'''
  (symbol
    (lib_id "{comp_def.symbol}")
    (at {comp.x:.2f} {comp.y:.2f} {comp.rotation:.0f})
    (unit 1)
    (exclude_from_sim no)
    (in_bom yes)
    (on_board yes)
    (dnp no)
    (uuid "{comp.uuid}")
    (property "Reference" "{comp.reference}" (at {comp.x:.2f} {comp.y - 5:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "{comp.value}" (at {comp.x:.2f} {comp.y + 5:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at {comp.x:.2f} {comp.y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "~" (at {comp.x:.2f} {comp.y:.2f} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid "{uuid.uuid4()}"))
    {self._generate_extra_pins(comp_def)}
  )'''
    
    def _generate_extra_pins(self, comp_def: ComponentDefinition) -> str:
        """Generate pin UUID entries for pins beyond pin 1."""
        lines = []
        for pin in comp_def.pins[1:]:  # Skip pin 1, already added
            lines.append(f'    (pin "{pin.number}" (uuid "{uuid.uuid4()}"))')
        return "\n".join(lines)
    
    def _generate_wire(self, wire: Wire) -> str:
        """Generate wire S-expression."""
        return f'''  (wire
    (pts
      (xy {wire.start_x:.2f} {wire.start_y:.2f})
      (xy {wire.end_x:.2f} {wire.end_y:.2f})
    )
    (stroke (width 0) (type default))
    (uuid "{wire.uuid}")
  )'''
    
    def _generate_junction(self, junction: Junction) -> str:
        """Generate junction S-expression."""
        return f'''  (junction (at {junction.x:.2f} {junction.y:.2f}) (diameter 0) (color 0 0 0 0)
    (uuid "{junction.uuid}")
  )'''
    
    def _generate_label(self, label: Label) -> str:
        """Generate label S-expression."""
        return f'''  (label "{label.text}" (at {label.x:.2f} {label.y:.2f} {label.rotation:.0f})
    (effects (font (size 1.27 1.27)) (justify left bottom))
    (uuid "{label.uuid}")
  )'''
    
    def generate(self) -> str:
        """Generate complete KiCad schematic file content."""
        
        # Header
        schematic = f'''(kicad_sch
  (version {KICAD_VERSION})
  (generator "{GENERATOR}")
  (generator_version "8.0")
  (uuid "{uuid.uuid4()}")
  (paper "A4")
'''
        
        # Lib symbols
        schematic += self._generate_lib_symbols() + "\n"
        
        # Wires
        for wire in self.wires:
            schematic += self._generate_wire(wire) + "\n"
        
        # Junctions
        for junction in self.junctions:
            schematic += self._generate_junction(junction) + "\n"
        
        # Labels
        for label in self.labels:
            schematic += self._generate_label(label) + "\n"
        
        # Components
        for comp in self.components:
            schematic += self._generate_symbol_instance(comp) + "\n"
        
        # Symbol instances section (for annotation)
        schematic += "\n  (symbol_instances\n"
        for comp in self.components:
            schematic += f'    (path "/{comp.uuid}" (reference "{comp.reference}") (unit 1))\n'
        schematic += "  )\n"
        
        # Close
        schematic += ")\n"
        
        return schematic
    
    def get_component_by_id(self, component_id: str) -> PlacedComponent | None:
        """Get component by its ID."""
        for comp in self.components:
            if comp.id == component_id:
                return comp
        return None


# ============================================
# HIGH-LEVEL API FOR AI INTEGRATION
# ============================================

def create_led_circuit(
    led_count: int = 1,
    resistance: str = "330"
) -> str:
    """
    Create a simple LED circuit with resistors.
    
    Example:
        VCC --- R1 --- LED1 --- GND
    """
    gen = SchematicGenerator()
    
    # Starting position
    start_x = 100
    start_y = 100
    spacing_y = 20
    
    # Add VCC
    vcc = gen.add_component("vcc", start_x, start_y - 15)
    
    for i in range(led_count):
        y_offset = i * spacing_y
        
        # Add resistor
        r = gen.add_component(
            "resistor",
            start_x,
            start_y + y_offset,
            rotation=0,
            value=resistance
        )
        
        # Add LED (rotated 90 degrees for vertical flow)
        led = gen.add_component(
            "led",
            start_x,
            start_y + y_offset + 15,
            rotation=90,  # Vertical
            value="Red"
        )
        
        # Add GND
        gnd = gen.add_component("gnd", start_x, start_y + y_offset + 30)
        
        # Wire VCC to resistor pin 1
        gen.add_wire_between_pins(vcc, 1, r, 1)
        
        # Wire resistor pin 2 to LED anode (pin 2)
        gen.add_wire_between_pins(r, 2, led, 2)
        
        # Wire LED cathode (pin 1) to GND
        gen.add_wire_between_pins(led, 1, gnd, 1)
    
    return gen.generate()


def create_schematic_from_components(
    components: list[dict],
    connections: list[dict]
) -> str:
    """
    Create schematic from component and connection specifications.
    
    Args:
        components: List of component specs:
            {
                "id": "r1",
                "type": "resistor",
                "x": 100,
                "y": 100,
                "rotation": 0,  # optional
                "value": "10k"  # optional
            }
        
        connections: List of connection specs:
            {
                "from": {"component": "r1", "pin": 1},
                "to": {"component": "led1", "pin": 2}
            }
    
    Returns:
        KiCad schematic content
    """
    gen = SchematicGenerator()
    
    # Place all components
    comp_map: dict[str, PlacedComponent] = {}
    for comp_spec in components:
        comp = gen.add_component(
            component_type=comp_spec["type"],
            x=comp_spec["x"],
            y=comp_spec["y"],
            rotation=comp_spec.get("rotation", 0),
            value=comp_spec.get("value"),
            component_id=comp_spec["id"]
        )
        comp_map[comp_spec["id"]] = comp
    
    # Create all connections
    for conn in connections:
        from_comp = comp_map.get(conn["from"]["component"])
        to_comp = comp_map.get(conn["to"]["component"])
        
        if from_comp and to_comp:
            gen.add_wire_between_pins(
                from_comp, conn["from"]["pin"],
                to_comp, conn["to"]["pin"]
            )
    
    return gen.generate()


# ============================================
# TEST HELPER
# ============================================

def test_simple_circuit():
    """Generate a test circuit to verify correctness."""
    gen = SchematicGenerator()
    
    # VCC at top
    vcc = gen.add_component("vcc", 127.0, 76.2)
    
    # Resistor below VCC
    r1 = gen.add_component("resistor", 127.0, 88.9, value="330")
    
    # LED below resistor (rotated for vertical)
    led1 = gen.add_component("led", 127.0, 101.6, rotation=90, value="Red")
    
    # GND at bottom
    gnd = gen.add_component("gnd", 127.0, 114.3)
    
    # Connect VCC -> R1 pin 1
    gen.add_wire_between_pins(vcc, 1, r1, 1)
    
    # Connect R1 pin 2 -> LED pin 2 (anode)
    gen.add_wire_between_pins(r1, 2, led1, 2)
    
    # Connect LED pin 1 (cathode) -> GND
    gen.add_wire_between_pins(led1, 1, gnd, 1)
    
    return gen.generate()


if __name__ == "__main__":
    # Generate test circuit
    content = test_simple_circuit()
    print(content)
