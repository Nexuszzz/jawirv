"""
JAWIR OS - KiCad Generator Bridge
Bridges the AI output (SchematicPlan) to the new generator_v2.

This module replaces the old buggy generator with proper symbol and wire handling.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Handle both relative and direct imports
try:
    from .generator_v2 import SchematicGenerator
    from .library_v2 import get_component, get_available_components
    from .schemas import SchematicPlan, GenerationResult
except ImportError:
    from generator_v2 import SchematicGenerator
    from library_v2 import get_component, get_available_components
    from schemas import SchematicPlan, GenerationResult


logger = logging.getLogger("jawir.kicad.bridge")

# Default output directory
KICAD_OUTPUT_DIR = Path("D:/sijawir/KiCad_Projects")


def generate_schematic_v2(plan: SchematicPlan) -> str:
    """
    Generate KiCad schematic from SchematicPlan using the new V2 generator.
    
    This replaces the old buggy generator with proper symbol definitions
    and correct wire routing.
    
    Args:
        plan: SchematicPlan from AI
        
    Returns:
        Complete .kicad_sch file content
    """
    gen = SchematicGenerator()
    
    # Map from AI reference to our component ID
    ref_to_comp = {}
    
    # Track power symbols to add with their positions
    power_symbols_needed = {}
    
    # STEP 1: Analyze ALL wires to find power connections
    # Power symbols: VCC, GND, 3V3, 5V, etc.
    POWER_NAMES = {"VCC", "GND", "+5V", "+3V3", "+3.3V", "+12V", "3V3", "5V", "#PWR"}
    
    for wire in plan.wires:
        from_ref = wire.from_.component.upper()
        to_ref = wire.to.component.upper()
        
        # Check if FROM is a power symbol
        for power_name in POWER_NAMES:
            if from_ref == power_name or from_ref.startswith(power_name):
                if from_ref not in power_symbols_needed:
                    power_symbols_needed[from_ref] = {
                        "type": "gnd" if "GND" in from_ref else "vcc",
                        "connections": []
                    }
                power_symbols_needed[from_ref]["connections"].append({
                    "target_ref": to_ref,
                    "target_pin": wire.to.pin
                })
                break
        
        # Check if TO is a power symbol
        for power_name in POWER_NAMES:
            if to_ref == power_name or to_ref.startswith(power_name):
                if to_ref not in power_symbols_needed:
                    power_symbols_needed[to_ref] = {
                        "type": "gnd" if "GND" in to_ref else "vcc",
                        "connections": []
                    }
                power_symbols_needed[to_ref]["connections"].append({
                    "target_ref": from_ref,
                    "target_pin": wire.from_.pin
                })
                break
    
    logger.info(f"Power symbols needed: {list(power_symbols_needed.keys())}")
    
    # STEP 2: Add regular components first (NOT power symbols)
    
    # Add components from plan
    for comp in plan.components:
        comp_type = comp.type.lower()
        
        # Skip power symbols - we'll add them later with correct positions
        if comp_type in ["vcc", "gnd", "power", "+5v", "+3v3", "3v3", "5v"]:
            continue
        
        # Handle aliases
        type_aliases = {
            "hc-sr04": "hcsr04",
            "hc_sr04": "hcsr04",
            "hc-sr501": "pir",
            "hc_sr501": "pir",
            "ultrasonic": "hcsr04",
            "rotary": "rotary_encoder",
            "encoder": "rotary_encoder",
            "switch": "button",
            "btn": "button",
            "r": "resistor",
            "c": "capacitor",
            "cap": "capacitor",
            "d": "led",
            "diode_led": "led",
            "transistor": "npn",
            "2n2222": "npn",
            "esp32-wroom": "esp32",
            "esp32_wroom": "esp32",
            "esp32-wroom-32": "esp32",
        }
        
        if comp_type in type_aliases:
            comp_type = type_aliases[comp_type]
        
        # Check if component exists in library
        comp_def = get_component(comp_type)
        if not comp_def:
            logger.warning(f"Unknown component type: {comp.type}, skipping")
            continue
        
        # Add component
        rotation = comp.rotation if comp.rotation is not None else comp_def.default_rotation
        value = comp.value if comp.value else comp_def.default_value
        
        placed = gen.add_component(
            component_type=comp_type,
            x=comp.position.x,
            y=comp.position.y,
            rotation=rotation,
            value=value,
            component_id=comp.reference
        )
        
        # Override reference to match AI output
        placed.reference = comp.reference
        
        ref_to_comp[comp.reference.upper()] = placed
        logger.debug(f"Added component: {comp.reference} ({comp_type}) at ({comp.position.x}, {comp.position.y})")
    
    # STEP 3: Add power symbols based on wire connections
    # For each power symbol needed, find the best position from its connections
    logger.info(f"Adding power symbols: {list(power_symbols_needed.keys())}")
    
    for power_name, info in power_symbols_needed.items():
        power_type = info["type"]  # "vcc" or "gnd"
        connections = info["connections"]
        
        if not connections:
            logger.warning(f"No connections for power symbol: {power_name}")
            continue
        
        # Find position from first valid connection
        placed = None
        for conn in connections:
            target_ref = conn["target_ref"].upper()
            target_pin = conn["target_pin"]
            
            if target_ref in ref_to_comp:
                comp = ref_to_comp[target_ref]
                try:
                    px, py = comp.get_pin_position(target_pin)
                    
                    # Offset power symbol appropriately
                    if power_type == "gnd":
                        py += 10  # GND below the connection point
                    else:
                        py -= 10  # VCC/power above the connection point
                    
                    placed = gen.add_component(power_type, px, py, component_id=power_name)
                    placed.reference = power_name  # Keep the reference name
                    ref_to_comp[power_name] = placed
                    logger.info(f"Added power symbol {power_name} at ({px}, {py}) connected to {target_ref}.pin{target_pin}")
                    break
                except Exception as e:
                    logger.warning(f"Could not get pin position for {target_ref}.{target_pin}: {e}")
                    continue
        
        if not placed:
            # Fallback: add at default position if no valid connection found
            default_x, default_y = 127, 30 if power_type == "vcc" else 127, 180
            placed = gen.add_component(power_type, default_x, default_y, component_id=power_name)
            placed.reference = power_name
            ref_to_comp[power_name] = placed
            logger.warning(f"Added power symbol {power_name} at default position ({default_x}, {default_y})")
    
    # STEP 4: Add wires
    for wire in plan.wires:
        from_ref = wire.from_.component.upper()
        to_ref = wire.to.component.upper()
        
        from_comp = ref_to_comp.get(from_ref)
        to_comp = ref_to_comp.get(to_ref)
        
        if from_comp and to_comp:
            gen.add_wire_between_pins(
                from_comp, wire.from_.pin,
                to_comp, wire.to.pin
            )
            logger.debug(f"Wire: {from_ref}.{wire.from_.pin} -> {to_ref}.{wire.to.pin}")
        else:
            if not from_comp:
                logger.warning(f"Wire source not found: {from_ref}")
            if not to_comp:
                logger.warning(f"Wire dest not found: {to_ref}")
    
    # Add labels if any
    if plan.labels:
        for label in plan.labels:
            gen.add_label(label.name, label.x, label.y)
    
    return gen.generate()


def save_schematic_v2(
    plan: SchematicPlan,
    output_dir: Optional[Path] = None
) -> GenerationResult:
    """
    Generate and save schematic using V2 generator.
    
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
        schematic_content = generate_schematic_v2(plan)
    except Exception as e:
        logger.exception(f"Error generating schematic: {e}")
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
    
    logger.info(f"✅ Schematic saved: {schematic_path}")
    
    return GenerationResult(
        success=True,
        project_name=project_name,
        file_path=str(schematic_path),
        component_count=len(plan.components),
        wire_count=len(plan.wires),
        message=f"Successfully generated {project_name}",
    )


def open_in_kicad(file_path: str) -> bool:
    """Try to open schematic in KiCad eeschema (schematic editor)."""
    import subprocess
    import os
    
    # Normalize path
    file_path = os.path.abspath(file_path)
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    # Common KiCad eeschema paths on Windows (use eeschema for .kicad_sch files, not kicad.exe)
    eeschema_paths = [
        r"C:\Program Files\KiCad\8.0\bin\eeschema.exe",
        r"C:\Program Files\KiCad\7.0\bin\eeschema.exe",
        r"C:\Program Files\KiCad\bin\eeschema.exe",
        r"C:\Program Files (x86)\KiCad\8.0\bin\eeschema.exe",
        r"C:\Program Files (x86)\KiCad\7.0\bin\eeschema.exe",
    ]
    
    # Also try kicad-cli schematic open (KiCad 8+)
    kicad_paths = [
        r"C:\Program Files\KiCad\8.0\bin\kicad.exe",
        r"C:\Program Files\KiCad\7.0\bin\kicad.exe",
    ]
    
    # Try eeschema first (opens schematic directly)
    for path in eeschema_paths:
        if os.path.exists(path):
            try:
                subprocess.Popen([path, file_path], start_new_session=True)
                logger.info(f"Opened {file_path} in eeschema")
                return True
            except Exception as e:
                logger.error(f"Failed to open with eeschema: {e}")
    
    # Fallback to kicad.exe (project manager - won't open .kicad_sch directly well)
    for path in kicad_paths:
        if os.path.exists(path):
            try:
                subprocess.Popen([path, file_path], start_new_session=True)
                logger.info(f"Opened {file_path} in KiCad")
                return True
            except Exception as e:
                logger.error(f"Failed to open with KiCad: {e}")
    
    # Last resort: use Windows file association (os.startfile)
    try:
        os.startfile(file_path)
        logger.info(f"Opened {file_path} with default application")
        return True
    except Exception as e:
        logger.error(f"Failed to open file: {e}")
        return False


# Test
if __name__ == "__main__":
    from schemas import Position, PinReference, ComponentPlacement, WireConnection
    
    # Create a test plan
    plan = SchematicPlan(
        project="test_led",
        description="Simple LED circuit",
        components=[
            ComponentPlacement(
                type="resistor",
                reference="R1",
                value="330",
                position=Position(x=127, y=70),
            ),
            ComponentPlacement(
                type="led",
                reference="D1",
                value="Red",
                position=Position(x=127, y=90),
                rotation=90,
            ),
        ],
        wires=[
            WireConnection(
                **{"from": PinReference(component="VCC", pin=1)},
                to=PinReference(component="R1", pin=1)
            ),
            WireConnection(
                **{"from": PinReference(component="R1", pin=2)},
                to=PinReference(component="D1", pin=2)
            ),
            WireConnection(
                **{"from": PinReference(component="D1", pin=1)},
                to=PinReference(component="GND", pin=1)
            ),
        ],
    )
    
    result = save_schematic_v2(plan)
    print(f"Result: {result}")
