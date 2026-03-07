"""
JAWIR OS - KiCad Tools
Tools for generating KiCad schematic files from AI-generated designs.

Modules:
- library_v2: Component definitions (FIXED - proper pin positions)
- schemas: Pydantic models for structured output
- generator_v2: Generate .kicad_sch files (FIXED - proper symbols and wiring)
- generator_bridge: Bridge AI output to generator_v2
- templates: Pre-made circuit templates
"""

# Library V2 - Component definitions (FIXED)
from .library_v2 import (
    COMPONENT_LIBRARY,
    COMPONENT_COUNT,
    ComponentDefinition,
    PinDefinition,
    PinOffset,
    PIN_OFFSET,
    get_component,
    get_available_components,
    get_component_info_for_ai,
    get_pin_position,
)

# Schemas - Pydantic models
from .schemas import (
    Position,
    PinReference,
    ComponentPlacement,
    WireConnection,
    PowerLabel,
    SchematicPlan,
    TemplateRequest,
    GenerationResult,
    KicadOutput,
    get_schematic_design_schema,
)

# Generator V2 - Generate .kicad_sch files (FIXED)
from .generator_v2 import (
    SchematicGenerator,
    PlacedComponent,
    Wire,
    create_led_circuit,
    create_schematic_from_components,
)

# Generator Bridge - Convert AI output to V2 generator
from .generator_bridge import (
    generate_schematic_v2 as generate_schematic,
    save_schematic_v2 as save_schematic,
    open_in_kicad,
    KICAD_OUTPUT_DIR,
)

# Templates - Pre-made circuits
from .templates import (
    TEMPLATES,
    get_template,
    get_available_templates,
    get_template_descriptions,
    get_template_info_for_ai,
)

# For backwards compatibility
COMPONENT_CATEGORIES = {}  # Not used in V2
get_pin_position_with_rotation = get_pin_position  # Alias

__all__ = [
    # Library
    "COMPONENT_LIBRARY",
    "COMPONENT_CATEGORIES",
    "COMPONENT_COUNT",
    "ComponentDefinition",
    "PinDefinition",
    "PinOffset",
    "PIN_OFFSET",
    "get_component",
    "get_available_components",
    "get_component_info_for_ai",
    "get_pin_position",
    "get_pin_position_with_rotation",
    # Schemas
    "Position",
    "PinReference",
    "ComponentPlacement",
    "WireConnection",
    "PowerLabel",
    "SchematicPlan",
    "TemplateRequest",
    "GenerationResult",
    "KicadOutput",
    "get_schematic_design_schema",
    # Generator V2
    "SchematicGenerator",
    "PlacedComponent",
    "Wire",
    "create_led_circuit",
    "create_schematic_from_components",
    "generate_schematic",
    "save_schematic",
    "open_in_kicad",
    "KICAD_OUTPUT_DIR",
    # Templates
    "TEMPLATES",
    "get_template",
    "get_available_templates",
    "get_template_descriptions",
    "get_template_info_for_ai",
]
