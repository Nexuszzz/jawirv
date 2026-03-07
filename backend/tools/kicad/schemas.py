"""
JAWIR OS - KiCad Pydantic Schemas
Structured output models for Gemini KiCad design.

These models define the exact structure AI must output.
Converter will transform this to KiCad S-expression format.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


# ============================================
# POSITION & CONNECTION MODELS
# ============================================

class Position(BaseModel):
    """Position in mm on schematic canvas."""
    x: float = Field(description="X position in mm (center ~127)")
    y: float = Field(description="Y position in mm (center ~100)")


class PinReference(BaseModel):
    """Reference to a specific pin on a component."""
    component: str = Field(description="Component reference (R1, D1, U1, etc)")
    pin: int | str = Field(description="Pin number or name")


# ============================================
# COMPONENT PLACEMENT
# ============================================

class ComponentPlacement(BaseModel):
    """Single component placement on schematic."""
    type: str = Field(
        description="Component type from library (resistor, led, esp32, etc)"
    )
    reference: str = Field(
        description="Reference designator (R1, C1, D1, U1, etc)"
    )
    value: Optional[str] = Field(
        default=None,
        description="Component value (10k, 100uF, Red, etc)"
    )
    position: Position = Field(
        description="Position on schematic in mm"
    )
    rotation: Optional[float] = Field(
        default=None,
        description="Rotation in degrees (0, 90, 180, 270)"
    )


# ============================================
# WIRE / NET CONNECTION
# ============================================

class WireConnection(BaseModel):
    """Wire connection between two component pins."""
    from_: PinReference = Field(
        alias="from",
        description="Source pin reference"
    )
    to: PinReference = Field(
        description="Destination pin reference"
    )
    
    class Config:
        populate_by_name = True


# ============================================
# POWER LABELS
# ============================================

class PowerLabel(BaseModel):
    """Power net label (VCC, GND, +5V, etc)."""
    name: str = Field(
        description="Label name (VCC, GND, +5V, +3V3, etc)"
    )
    x: float = Field(description="X position in mm")
    y: float = Field(description="Y position in mm")


# ============================================
# SCHEMATIC PLAN - MAIN OUTPUT
# ============================================

class SchematicPlan(BaseModel):
    """
    Complete schematic design plan from AI.
    This is the main structured output model.
    """
    project: str = Field(
        description="Project/circuit name for filename"
    )
    description: Optional[str] = Field(
        default=None,
        description="Circuit description"
    )
    components: list[ComponentPlacement] = Field(
        description="List of component placements"
    )
    wires: list[WireConnection] = Field(
        description="List of wire connections (semantic, not coordinates)"
    )
    labels: Optional[list[PowerLabel]] = Field(
        default=None,
        description="Optional power labels"
    )
    open_kicad: bool = Field(
        default=False,
        description="Whether to open KiCad after generation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "project": "led_blink",
                "description": "Simple LED with resistor",
                "components": [
                    {
                        "type": "resistor",
                        "reference": "R1",
                        "value": "330",
                        "position": {"x": 127, "y": 80}
                    },
                    {
                        "type": "led",
                        "reference": "D1",
                        "value": "Red",
                        "position": {"x": 127, "y": 100}
                    }
                ],
                "wires": [
                    {
                        "from": {"component": "R1", "pin": 2},
                        "to": {"component": "D1", "pin": 2}
                    },
                    {
                        "from": {"component": "D1", "pin": 1},
                        "to": {"component": "GND", "pin": 1}
                    }
                ],
                "open_kicad": False
            }
        }


# ============================================
# TEMPLATE REQUEST
# ============================================

class TemplateRequest(BaseModel):
    """Request for template-based schematic."""
    template: Literal[
        "led_indicator",
        "voltage_divider",
        "powerbank",
        "amplifier",
        "fire_detection",
        "esp32_basic",
        "arduino_led"
    ] = Field(description="Template name")
    project_name: Optional[str] = Field(
        default=None,
        description="Custom project name"
    )
    open_kicad: bool = Field(
        default=False,
        description="Open KiCad after generation"
    )


# ============================================
# GENERATION RESULT
# ============================================

class GenerationResult(BaseModel):
    """Result of schematic generation."""
    success: bool = Field(description="Whether generation succeeded")
    project_name: str = Field(description="Generated project name")
    file_path: str = Field(description="Path to generated .kicad_sch file")
    component_count: int = Field(description="Number of components placed")
    wire_count: int = Field(description="Number of wires/nets")
    message: str = Field(description="Status message")
    errors: Optional[list[str]] = Field(
        default=None,
        description="Any errors or warnings"
    )


# ============================================
# KICAD NODE OUTPUT
# ============================================

class KicadOutput(BaseModel):
    """Output from KiCad designer node for agent state."""
    plan: Optional[SchematicPlan] = Field(
        default=None,
        description="The schematic plan from AI"
    )
    result: Optional[GenerationResult] = Field(
        default=None,
        description="Generation result"
    )
    raw_response: Optional[str] = Field(
        default=None,
        description="Raw AI response for debugging"
    )


# ============================================
# GEMINI FUNCTION CALLING SCHEMA
# ============================================

def get_schematic_design_schema() -> dict:
    """
    Get JSON schema for Gemini function calling.
    This defines the structure AI must output.
    """
    return {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "description": "Project/circuit name (for filename)"
            },
            "description": {
                "type": "string",
                "description": "Circuit description"
            },
            "components": {
                "type": "array",
                "description": "Component placements",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Component type: resistor, led, esp32, etc"
                        },
                        "reference": {
                            "type": "string",
                            "description": "Reference: R1, D1, U1, etc"
                        },
                        "value": {
                            "type": "string",
                            "description": "Value: 10k, 100uF, Red, etc"
                        },
                        "position": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "number"},
                                "y": {"type": "number"}
                            },
                            "required": ["x", "y"]
                        },
                        "rotation": {
                            "type": "number",
                            "description": "Rotation 0/90/180/270"
                        }
                    },
                    "required": ["type", "reference", "position"]
                }
            },
            "wires": {
                "type": "array",
                "description": "Wire connections (semantic)",
                "items": {
                    "type": "object",
                    "properties": {
                        "from": {
                            "type": "object",
                            "properties": {
                                "component": {"type": "string"},
                                "pin": {"type": "integer"}
                            },
                            "required": ["component", "pin"]
                        },
                        "to": {
                            "type": "object",
                            "properties": {
                                "component": {"type": "string"},
                                "pin": {"type": "integer"}
                            },
                            "required": ["component", "pin"]
                        }
                    },
                    "required": ["from", "to"]
                }
            },
            "labels": {
                "type": "array",
                "description": "Power labels (optional)",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "x": {"type": "number"},
                        "y": {"type": "number"}
                    },
                    "required": ["name", "x", "y"]
                }
            },
            "open_kicad": {
                "type": "boolean",
                "description": "Open KiCad after generation"
            }
        },
        "required": ["project", "components", "wires"]
    }
