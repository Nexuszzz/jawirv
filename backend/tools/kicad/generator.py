"""
JAWIR OS - KiCad Schematic Generator
Port of kicad-reference/schematic-generator.ts to Python.

Generates valid .kicad_sch files from AI schematic plans.
Handles semantic wire routing (component.pin references).
"""

import uuid
import os
import math
from pathlib import Path
from typing import Optional
from datetime import datetime

from .library import (
    COMPONENT_LIBRARY,
    get_component,
    get_pin_position_with_rotation,
    PIN_OFFSET,
    ComponentDefinition,
    PinDefinition,
)
from .schemas import (
    SchematicPlan,
    ComponentPlacement,
    WireConnection,
    PowerLabel,
    GenerationResult,
)


# ============================================
# CONSTANTS
# ============================================

# Default output directory for KiCad projects
KICAD_OUTPUT_DIR = Path("D:/sijawir/KiCad_Projects")

# KiCad schematic version
KICAD_VERSION = "20231120"
GENERATOR_NAME = "jawir-os"
GENERATOR_VERSION = "2.0"

# Default paper size
PAPER_SIZE = "A4"


# ============================================
# UUID GENERATION
# ============================================

def generate_uuid() -> str:
    """Generate a UUID for KiCad elements."""
    return str(uuid.uuid4())


# ============================================
# COMPONENT POSITION TRACKING
# ============================================

class ComponentRegistry:
    """Track placed components and their positions for wire routing."""
    
    def __init__(self):
        self.components: dict[str, dict] = {}
        # Add virtual power components
        self.components["VCC"] = {
            "type": "vcc",
            "x": 0,
            "y": 0,
            "rotation": 0,
            "pins": {1: {"x": 0, "y": 0}}
        }
        self.components["GND"] = {
            "type": "gnd",
            "x": 0,
            "y": 0,
            "rotation": 0,
            "pins": {1: {"x": 0, "y": 0}}
        }
    
    def register(
        self,
        reference: str,
        comp_type: str,
        x: float,
        y: float,
        rotation: float = 0
    ):
        """Register a component placement."""
        comp_def = get_component(comp_type)
        if not comp_def:
            return
        
        # Calculate pin positions
        pins = {}
        for pin in comp_def.pins:
            pin_x, pin_y = get_pin_position_with_rotation(x, y, pin, rotation)
            pins[pin.number] = {"x": pin_x, "y": pin_y, "name": pin.name}
        
        self.components[reference] = {
            "type": comp_type,
            "x": x,
            "y": y,
            "rotation": rotation,
            "pins": pins,
            "definition": comp_def
        }
    
    def get_pin_position(
        self,
        reference: str,
        pin: int | str
    ) -> Optional[tuple[float, float]]:
        """Get absolute pin position for a component."""
        if reference not in self.components:
            return None
        
        comp = self.components[reference]
        
        # Handle string pin names
        if isinstance(pin, str):
            # Try to find by name
            for pin_num, pin_data in comp["pins"].items():
                if pin_data.get("name") == pin:
                    return (pin_data["x"], pin_data["y"])
            # Try as number
            try:
                pin = int(pin)
            except ValueError:
                return None
        
        if pin in comp["pins"]:
            return (comp["pins"][pin]["x"], comp["pins"][pin]["y"])
        
        return None


# ============================================
# S-EXPRESSION GENERATORS
# ============================================

def generate_lib_symbols(components: list[ComponentPlacement]) -> str:
    """Generate lib_symbols section with all unique symbol definitions."""
    seen_types: set[str] = set()
    lib_symbols: list[str] = []
    
    for comp in components:
        comp_type = comp.type.lower()
        if comp_type in seen_types:
            continue
        seen_types.add(comp_type)
        
        comp_def = get_component(comp_type)
        if comp_def and comp_def.lib_symbol_def:
            lib_symbols.append(comp_def.lib_symbol_def)
    
    return "\n".join(lib_symbols)


def generate_symbol_instance(
    comp: ComponentPlacement,
    comp_def: ComponentDefinition,
    project_name: str
) -> str:
    """Generate symbol instance S-expression."""
    x = comp.position.x
    y = comp.position.y
    rotation = comp.rotation or comp_def.default_rotation
    value = comp.value or comp_def.default_value
    reference = comp.reference
    symbol_uuid = generate_uuid()
    
    # Reference offset based on rotation
    if rotation in [90, 270]:
        ref_offset_x = 3.81
        ref_offset_y = 0
    else:
        ref_offset_x = 0
        ref_offset_y = -5.08
    
    # Generate pin UUIDs
    pin_lines = []
    for pin in comp_def.pins:
        pin_lines.append(f'    (pin "{pin.number}" (uuid {generate_uuid()}))')
    
    pins_str = "\n".join(pin_lines)
    
    return f'''
  (symbol (lib_id "{comp_def.symbol}") (at {x} {y} {int(rotation)}) (unit 1)
    (in_bom yes) (on_board yes) (dnp no)
    (uuid {symbol_uuid})
    (property "Reference" "{reference}" (at {x + ref_offset_x} {y + ref_offset_y} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "{value}" (at {x + ref_offset_x} {y - ref_offset_y} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "~" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
{pins_str}
    (instances (project "{project_name}" (path "/" (reference "{reference}") (unit 1))))
  )'''


def generate_wire(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float
) -> str:
    """Generate wire S-expression."""
    wire_uuid = generate_uuid()
    return f'''
  (wire (pts (xy {start_x} {start_y}) (xy {end_x} {end_y}))
    (stroke (width 0) (type default))
    (uuid {wire_uuid})
  )'''


def generate_junction(x: float, y: float) -> str:
    """Generate junction S-expression for wire intersections."""
    junction_uuid = generate_uuid()
    return f'''
  (junction (at {x} {y}) (diameter 0) (color 0 0 0 0)
    (uuid {junction_uuid})
  )'''


def generate_label(name: str, x: float, y: float) -> str:
    """Generate label S-expression."""
    label_uuid = generate_uuid()
    return f'''
  (label "{name}" (at {x} {y} 0) (fields_autoplaced)
    (effects (font (size 1.27 1.27)) (justify left bottom))
    (uuid {label_uuid})
  )'''


def generate_power_symbol(
    symbol_type: str,
    reference: str,
    x: float,
    y: float,
    project_name: str
) -> str:
    """Generate power symbol (VCC/GND)."""
    comp_def = get_component(symbol_type)
    if not comp_def:
        return ""
    
    symbol_uuid = generate_uuid()
    
    return f'''
  (symbol (lib_id "{comp_def.symbol}") (at {x} {y} 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no)
    (uuid {symbol_uuid})
    (property "Reference" "{reference}" (at {x} {y + 3.81} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Value" "{symbol_type.upper()}" (at {x} {y - 3.81} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
    (pin "1" (uuid {generate_uuid()}))
    (instances (project "{project_name}" (path "/" (reference "{reference}") (unit 1))))
  )'''


# ============================================
# WIRE ROUTING
# ============================================

def route_wire(
    registry: ComponentRegistry,
    from_ref: str,
    from_pin: int | str,
    to_ref: str,
    to_pin: int | str
) -> list[str]:
    """
    Route a wire between two pins.
    Returns list of wire segments (may use intermediate points for cleaner routing).
    """
    start = registry.get_pin_position(from_ref, from_pin)
    end = registry.get_pin_position(to_ref, to_pin)
    
    if not start or not end:
        return []
    
    wires = []
    start_x, start_y = start
    end_x, end_y = end
    
    # Simple L-routing: horizontal then vertical OR vertical then horizontal
    if abs(start_x - end_x) > 0.01 and abs(start_y - end_y) > 0.01:
        # Need to route around - use midpoint
        mid_y = (start_y + end_y) / 2
        
        # Vertical from start to mid
        wires.append(generate_wire(start_x, start_y, start_x, mid_y))
        # Horizontal at mid
        wires.append(generate_wire(start_x, mid_y, end_x, mid_y))
        # Vertical from mid to end
        wires.append(generate_wire(end_x, mid_y, end_x, end_y))
    else:
        # Direct line (same X or same Y)
        wires.append(generate_wire(start_x, start_y, end_x, end_y))
    
    return wires


# ============================================
# MAIN GENERATOR
# ============================================

def generate_schematic(plan: SchematicPlan) -> str:
    """
    Generate complete KiCad schematic from plan.
    
    Args:
        plan: SchematicPlan from AI with components and wires
        
    Returns:
        Complete .kicad_sch file content
    """
    schematic_uuid = generate_uuid()
    project_name = plan.project.replace(" ", "_").lower()
    
    # Initialize component registry for wire routing
    registry = ComponentRegistry()
    
    # Collect symbol definitions
    lib_symbols_content = generate_lib_symbols(plan.components)
    
    # Generate symbol instances
    symbol_instances = []
    power_counter = 1
    
    for comp in plan.components:
        comp_def = get_component(comp.type)
        if not comp_def:
            continue
        
        # Register for wire routing
        rotation = comp.rotation or comp_def.default_rotation
        registry.register(comp.reference, comp.type, comp.position.x, comp.position.y, rotation)
        
        # Generate symbol instance
        symbol_instances.append(generate_symbol_instance(comp, comp_def, project_name))
    
    # Process wires - identify needed power symbols
    power_symbols_needed: dict[str, tuple[float, float]] = {}
    
    for wire in plan.wires:
        from_ref = wire.from_.component
        to_ref = wire.to.component
        
        # Check for power references
        for ref in [from_ref, to_ref]:
            if ref.upper() in ["VCC", "GND", "+5V", "+3V3", "+12V"]:
                ref_upper = ref.upper()
                if ref_upper not in power_symbols_needed:
                    # Find position from the other end
                    other_ref = to_ref if ref == from_ref else from_ref
                    other_pin = wire.to.pin if ref == from_ref else wire.from_.pin
                    pos = registry.get_pin_position(other_ref, other_pin)
                    if pos:
                        # Offset power symbol
                        offset_y = -10 if ref_upper == "VCC" or ref_upper.startswith("+") else 10
                        power_symbols_needed[ref_upper] = (pos[0], pos[1] + offset_y)
    
    # Add power symbols
    power_symbol_instances = []
    for power_name, (px, py) in power_symbols_needed.items():
        power_type = "vcc" if power_name != "GND" else "gnd"
        power_ref = f"#PWR0{power_counter}"
        power_counter += 1
        
        power_symbol_instances.append(
            generate_power_symbol(power_type, power_ref, px, py, project_name)
        )
        
        # Register power symbol position
        registry.components[power_name] = {
            "type": power_type,
            "x": px,
            "y": py,
            "rotation": 0,
            "pins": {1: {"x": px, "y": py}}
        }
    
    # Generate wires
    wire_segments = []
    for wire in plan.wires:
        segments = route_wire(
            registry,
            wire.from_.component,
            wire.from_.pin,
            wire.to.component,
            wire.to.pin
        )
        wire_segments.extend(segments)
    
    # Generate labels
    label_instances = []
    if plan.labels:
        for label in plan.labels:
            label_instances.append(generate_label(label.name, label.x, label.y))
    
    # Combine all sections
    symbols_str = "\n".join(symbol_instances + power_symbol_instances)
    wires_str = "\n".join(wire_segments)
    labels_str = "\n".join(label_instances)
    
    # Generate complete schematic
    schematic = f'''(kicad_sch (version {KICAD_VERSION}) (generator "{GENERATOR_NAME}") (generator_version "{GENERATOR_VERSION}")
  (uuid {schematic_uuid})
  (paper "{PAPER_SIZE}")
  
  (lib_symbols
    {lib_symbols_content}
  )
  
  {symbols_str}
  
  {wires_str}
  
  {labels_str}
  
  (sheet_instances
    (path "/" (page "1"))
  )
)'''
    
    return schematic


# ============================================
# FILE OPERATIONS
# ============================================

def save_schematic(
    plan: SchematicPlan,
    output_dir: Optional[Path] = None
) -> GenerationResult:
    """
    Generate and save schematic to file.
    
    Args:
        plan: SchematicPlan from AI
        output_dir: Output directory (default: D:/sijawir/KiCad_Projects)
        
    Returns:
        GenerationResult with file path and status
    """
    if output_dir is None:
        output_dir = KICAD_OUTPUT_DIR
    
    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate project name
    project_name = plan.project.replace(" ", "_").lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create project folder
    project_dir = output_dir / f"{project_name}_{timestamp}"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate schematic content
    try:
        schematic_content = generate_schematic(plan)
    except Exception as e:
        return GenerationResult(
            success=False,
            project_name=project_name,
            file_path="",
            component_count=0,
            wire_count=0,
            message=f"Error generating schematic: {str(e)}",
            errors=[str(e)]
        )
    
    # Save schematic file
    schematic_path = project_dir / f"{project_name}.kicad_sch"
    try:
        schematic_path.write_text(schematic_content, encoding="utf-8")
    except Exception as e:
        return GenerationResult(
            success=False,
            project_name=project_name,
            file_path="",
            component_count=len(plan.components),
            wire_count=len(plan.wires),
            message=f"Error saving file: {str(e)}",
            errors=[str(e)]
        )
    
    # Generate minimal .kicad_pro file
    pro_content = f'''{{
  "board": {{
    "3dviewports": [],
    "design_settings": {{}},
    "ipc2581": {{}},
    "layer_presets": [],
    "viewports": []
  }},
  "meta": {{
    "filename": "{project_name}.kicad_pro",
    "version": 1
  }},
  "net_settings": {{}},
  "schematic": {{
    "legacy_lib_dir": "",
    "legacy_lib_list": []
  }},
  "sheets": []
}}'''
    
    pro_path = project_dir / f"{project_name}.kicad_pro"
    pro_path.write_text(pro_content, encoding="utf-8")
    
    return GenerationResult(
        success=True,
        project_name=project_name,
        file_path=str(schematic_path),
        component_count=len(plan.components),
        wire_count=len(plan.wires),
        message=f"Schematic berhasil dibuat: {schematic_path}",
        errors=None
    )


# ============================================
# UTILITY FUNCTIONS
# ============================================

def open_in_kicad(file_path: str) -> bool:
    """Open schematic in KiCad application."""
    import subprocess
    import shutil
    
    # Find KiCad executable
    kicad_paths = [
        r"C:\Program Files\KiCad\8.0\bin\kicad.exe",
        r"C:\Program Files\KiCad\7.0\bin\kicad.exe",
        r"C:\Program Files (x86)\KiCad\8.0\bin\kicad.exe",
        r"C:\Program Files (x86)\KiCad\7.0\bin\kicad.exe",
    ]
    
    kicad_exe = None
    for path in kicad_paths:
        if os.path.exists(path):
            kicad_exe = path
            break
    
    if not kicad_exe:
        # Try to find in PATH
        kicad_exe = shutil.which("kicad")
    
    if not kicad_exe:
        return False
    
    try:
        subprocess.Popen([kicad_exe, file_path])
        return True
    except Exception:
        return False
