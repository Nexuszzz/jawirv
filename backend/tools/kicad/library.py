"""
JAWIR OS - KiCad Component Library
Port of kicad-reference/kicad-library.ts to Python.

This file contains all component definitions that AI can reference.
AI hanya perlu specify component type, converter akan handle sisanya.
"""

from dataclasses import dataclass
from typing import Literal, Optional
import math

# ============================================
# CONSTANTS
# ============================================

# Standard pin length is 2.54mm, offset from center is 3.81mm
PIN_OFFSET = 3.81


# ============================================
# TYPES
# ============================================

@dataclass
class PinOffset:
    """Offset from component center (mm)"""
    dx: float
    dy: float


@dataclass
class PinDefinition:
    """Definition of a component pin"""
    number: int | str
    name: str
    offset: PinOffset
    direction: Literal["up", "down", "left", "right"]


@dataclass
class ComponentDefinition:
    """Complete definition of a KiCad component"""
    type: str  # Component type ID for AI reference
    symbol: str  # KiCad library:symbol format
    name: str  # Human readable name
    default_value: str  # Default value if not specified
    ref_prefix: str  # Reference prefix (R, C, D, U, etc)
    default_rotation: float  # Default rotation (degrees)
    pins: list[PinDefinition]  # Pin definitions
    lib_symbol_def: str  # S-expression template for lib_symbols


# ============================================
# COMPONENT DEFINITIONS
# ============================================

COMPONENT_LIBRARY: dict[str, ComponentDefinition] = {
    # ----------------------------------------
    # PASSIVE COMPONENTS
    # ----------------------------------------
    
    "resistor": ComponentDefinition(
        type="resistor",
        symbol="Device:R",
        name="Resistor",
        default_value="10k",
        ref_prefix="R",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(0, -PIN_OFFSET), "up"),
            PinDefinition(2, "2", PinOffset(0, PIN_OFFSET), "down"),
        ],
        lib_symbol_def='''
    (symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "R" (at 0 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at -1.778 0 90) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "R_0_1"
        (rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "R_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    "capacitor": ComponentDefinition(
        type="capacitor",
        symbol="Device:C",
        name="Capacitor",
        default_value="100nF",
        ref_prefix="C",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(0, -PIN_OFFSET), "up"),
            PinDefinition(2, "2", PinOffset(0, PIN_OFFSET), "down"),
        ],
        lib_symbol_def='''
    (symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254)) (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 0.635 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "C" (at 0.635 -2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 0.9652 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "C_0_1"
        (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
        (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
      )
      (symbol "C_1_1"
        (pin passive line (at 0 3.81 270) (length 2.794) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 2.794) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    "capacitor_polarized": ComponentDefinition(
        type="capacitor_polarized",
        symbol="Device:CP",
        name="Polarized Capacitor",
        default_value="100uF",
        ref_prefix="C",
        default_rotation=0,
        pins=[
            PinDefinition(1, "+", PinOffset(0, -PIN_OFFSET), "up"),
            PinDefinition(2, "-", PinOffset(0, PIN_OFFSET), "down"),
        ],
        lib_symbol_def='''
    (symbol "Device:CP" (pin_numbers hide) (pin_names (offset 0.254)) (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 0.635 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "CP" (at 0.635 -2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 0.9652 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "CP_0_1"
        (rectangle (start -2.286 0.508) (end 2.286 1.016) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -1.778 2.286) (xy -0.762 2.286)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 2.794) (xy -1.27 1.778)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
      )
      (symbol "CP_1_1"
        (pin passive line (at 0 3.81 270) (length 2.794) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 2.794) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    "inductor": ComponentDefinition(
        type="inductor",
        symbol="Device:L",
        name="Inductor",
        default_value="10uH",
        ref_prefix="L",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(0, -PIN_OFFSET), "up"),
            PinDefinition(2, "2", PinOffset(0, PIN_OFFSET), "down"),
        ],
        lib_symbol_def='''
    (symbol "Device:L" (pin_numbers hide) (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "L" (at -1.016 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "L" (at 1.524 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "L_0_1"
        (arc (start 0 -2.54) (mid 0.6323 -1.905) (end 0 -1.27) (stroke (width 0) (type default)) (fill (type none)))
        (arc (start 0 -1.27) (mid 0.6323 -0.635) (end 0 0) (stroke (width 0) (type default)) (fill (type none)))
        (arc (start 0 0) (mid 0.6323 0.635) (end 0 1.27) (stroke (width 0) (type default)) (fill (type none)))
        (arc (start 0 1.27) (mid 0.6323 1.905) (end 0 2.54) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "L_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    # ----------------------------------------
    # SEMICONDUCTOR - DIODES
    # ----------------------------------------
    
    "led": ComponentDefinition(
        type="led",
        symbol="Device:LED",
        name="LED",
        default_value="Red",
        ref_prefix="D",
        default_rotation=90,  # Vertical orientation
        pins=[
            PinDefinition(1, "K", PinOffset(-PIN_OFFSET, 0), "left"),  # Cathode
            PinDefinition(2, "A", PinOffset(PIN_OFFSET, 0), "right"),  # Anode
        ],
        lib_symbol_def='''
    (symbol "Device:LED" (pin_numbers hide) (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "LED" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "LED_0_1"
        (polyline (pts (xy -1.27 -1.27) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 0) (xy 1.27 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -3.048 -1.524) (xy -1.778 -2.794)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -1.524 -1.524) (xy -0.254 -2.794)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "LED_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54) (name "K" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "A" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    "diode": ComponentDefinition(
        type="diode",
        symbol="Device:D",
        name="Diode",
        default_value="1N4148",
        ref_prefix="D",
        default_rotation=90,
        pins=[
            PinDefinition(1, "K", PinOffset(-PIN_OFFSET, 0), "left"),
            PinDefinition(2, "A", PinOffset(PIN_OFFSET, 0), "right"),
        ],
        lib_symbol_def='''
    (symbol "Device:D" (pin_numbers hide) (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "D" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "D_0_1"
        (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 0) (xy -1.27 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27) (xy -1.27 0) (xy 1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "D_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54) (name "K" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "A" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    "zener": ComponentDefinition(
        type="zener",
        symbol="Device:D_Zener",
        name="Zener Diode",
        default_value="5.1V",
        ref_prefix="D",
        default_rotation=90,
        pins=[
            PinDefinition(1, "K", PinOffset(-PIN_OFFSET, 0), "left"),
            PinDefinition(2, "A", PinOffset(PIN_OFFSET, 0), "right"),
        ],
        lib_symbol_def='''
    (symbol "Device:D_Zener" (pin_numbers hide) (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "D_Zener" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "D_Zener_0_1"
        (polyline (pts (xy 1.27 0) (xy -1.27 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 -1.27) (xy -1.27 1.27) (xy -0.762 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "D_Zener_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54) (name "K" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "A" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    # ----------------------------------------
    # POWER SYMBOLS
    # ----------------------------------------
    
    "vcc": ComponentDefinition(
        type="vcc",
        symbol="power:VCC",
        name="VCC Power",
        default_value="VCC",
        ref_prefix="#PWR",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VCC", PinOffset(0, 0), "down"),
        ],
        lib_symbol_def='''
    (symbol "power:VCC" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "VCC" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "VCC_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 1.27) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 1.27) (xy 0 2.54) (xy -0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "VCC_1_1"
        (pin power_in line (at 0 0 90) (length 0) (name "VCC" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    "gnd": ComponentDefinition(
        type="gnd",
        symbol="power:GND",
        name="Ground",
        default_value="GND",
        ref_prefix="#PWR",
        default_rotation=0,
        pins=[
            PinDefinition(1, "GND", PinOffset(0, 0), "up"),
        ],
        lib_symbol_def='''
    (symbol "power:GND" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -6.35 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "GND" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "GND_0_1"
        (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "GND_1_1"
        (pin power_in line (at 0 0 270) (length 0) (name "GND" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    # ----------------------------------------
    # TRANSISTORS
    # ----------------------------------------
    
    "npn": ComponentDefinition(
        type="npn",
        symbol="Device:Q_NPN_BCE",
        name="NPN Transistor",
        default_value="BC547",
        ref_prefix="Q",
        default_rotation=0,
        pins=[
            PinDefinition(1, "B", PinOffset(-2.54, 0), "left"),
            PinDefinition(2, "C", PinOffset(2.54, 2.54), "up"),
            PinDefinition(3, "E", PinOffset(2.54, -2.54), "down"),
        ],
        lib_symbol_def='''
    (symbol "Device:Q_NPN_BCE" (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "Q" (at 5.08 1.905 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "Q_NPN_BCE" (at 5.08 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 5.08 -1.905 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Q_NPN_BCE_0_1"
        (polyline (pts (xy 0.635 0.635) (xy 2.54 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.635 -0.635) (xy 2.54 -2.54) (xy 2.54 -2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.635 1.905) (xy 0.635 -1.905) (xy 0.635 -1.905)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -1.778) (xy 1.778 -1.27) (xy 2.286 -2.286) (xy 1.27 -1.778) (xy 1.27 -1.778)) (stroke (width 0) (type default)) (fill (type outline)))
        (circle (center 1.27 0) (radius 2.8194) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "Q_NPN_BCE_1_1"
        (pin passive line (at -5.08 0 0) (length 5.715) (name "B" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 5.08 270) (length 2.54) (name "C" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 -5.08 90) (length 2.54) (name "E" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    "pnp": ComponentDefinition(
        type="pnp",
        symbol="Device:Q_PNP_BCE",
        name="PNP Transistor",
        default_value="BC557",
        ref_prefix="Q",
        default_rotation=0,
        pins=[
            PinDefinition(1, "B", PinOffset(-2.54, 0), "left"),
            PinDefinition(2, "C", PinOffset(2.54, -2.54), "down"),
            PinDefinition(3, "E", PinOffset(2.54, 2.54), "up"),
        ],
        lib_symbol_def='''
    (symbol "Device:Q_PNP_BCE" (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "Q" (at 5.08 1.905 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "Q_PNP_BCE" (at 5.08 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 5.08 -1.905 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Q_PNP_BCE_0_1"
        (polyline (pts (xy 0.635 0.635) (xy 2.54 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.635 -0.635) (xy 2.54 -2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.635 1.905) (xy 0.635 -1.905)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 2.286 0.508) (xy 1.778 1.016) (xy 1.27 0) (xy 2.286 0.508)) (stroke (width 0) (type default)) (fill (type outline)))
        (circle (center 1.27 0) (radius 2.8194) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "Q_PNP_BCE_1_1"
        (pin passive line (at -5.08 0 0) (length 5.715) (name "B" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 -5.08 90) (length 2.54) (name "C" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 5.08 270) (length 2.54) (name "E" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    # ----------------------------------------
    # TIMER ICs
    # ----------------------------------------
    
    "ne555": ComponentDefinition(
        type="ne555",
        symbol="Timer:NE555",
        name="555 Timer",
        default_value="NE555",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            PinDefinition(1, "GND", PinOffset(-7.62, -5.08), "left"),
            PinDefinition(2, "TR", PinOffset(-7.62, -2.54), "left"),
            PinDefinition(3, "Q", PinOffset(7.62, -2.54), "right"),
            PinDefinition(4, "R", PinOffset(-7.62, 5.08), "left"),
            PinDefinition(5, "CV", PinOffset(7.62, 0), "right"),
            PinDefinition(6, "THR", PinOffset(-7.62, 0), "left"),
            PinDefinition(7, "DIS", PinOffset(-7.62, 2.54), "left"),
            PinDefinition(8, "VCC", PinOffset(7.62, 5.08), "right"),
        ],
        lib_symbol_def='''
    (symbol "Timer:NE555" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at -7.62 8.89 0) (effects (font (size 1.27 1.27))))
      (property "Value" "NE555" (at 5.08 8.89 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "http://www.ti.com/lit/ds/symlink/ne555.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "NE555_0_0"
        (rectangle (start -7.62 7.62) (end 7.62 -7.62) (stroke (width 0.254) (type default)) (fill (type background)))
        (pin power_in line (at 0 -10.16 90) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin input line (at -10.16 -2.54 0) (length 2.54) (name "TR" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin output line (at 10.16 -2.54 180) (length 2.54) (name "Q" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin input line (at -10.16 5.08 0) (length 2.54) (name "R" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin input line (at 10.16 0 180) (length 2.54) (name "CV" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
        (pin input line (at -10.16 0 0) (length 2.54) (name "THR" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
        (pin input line (at -10.16 2.54 0) (length 2.54) (name "DIS" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 10.16 270) (length 2.54) (name "VCC" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    # ----------------------------------------
    # VOLTAGE REGULATORS
    # ----------------------------------------
    
    "lm7805": ComponentDefinition(
        type="lm7805",
        symbol="Regulator_Linear:L7805",
        name="5V Voltage Regulator",
        default_value="LM7805",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VI", PinOffset(-5.08, 0), "left"),
            PinDefinition(2, "GND", PinOffset(0, -5.08), "down"),
            PinDefinition(3, "VO", PinOffset(5.08, 0), "right"),
        ],
        lib_symbol_def='''
    (symbol "Regulator_Linear:L7805" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Value" "L7805" (at 0 1.27 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_TO_SOT_THT:TO-220-3_Vertical" (at 0 -5.08 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "L7805_0_1"
        (rectangle (start -5.08 -2.54) (end 5.08 2.54) (stroke (width 0.254) (type default)) (fill (type background)))
        (pin power_in line (at -7.62 0 0) (length 2.54) (name "VI" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -5.08 90) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at 7.62 0 180) (length 2.54) (name "VO" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    # ----------------------------------------
    # SWITCHES
    # ----------------------------------------
    
    "switch": ComponentDefinition(
        type="switch",
        symbol="Switch:SW_Push",
        name="Push Button Switch",
        default_value="SW_Push",
        ref_prefix="SW",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(-2.54, 0), "left"),
            PinDefinition(2, "2", PinOffset(2.54, 0), "right"),
        ],
        lib_symbol_def='''
    (symbol "Switch:SW_Push" (pin_numbers hide) (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "SW" (at 1.27 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "SW_Push" (at 0 -1.524 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 5.08 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 5.08 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "SW_Push_0_1"
        (circle (center -2.032 0) (radius 0.508) (stroke (width 0) (type default)) (fill (type none)))
        (circle (center 2.032 0) (radius 0.508) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 1.27) (xy 0 3.048)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -2.54 0) (xy 2.54 0) (xy 2.54 0)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "SW_Push_1_1"
        (pin passive line (at -5.08 0 0) (length 2.54) (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 5.08 0 180) (length 2.54) (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    # ----------------------------------------
    # POTENTIOMETER
    # ----------------------------------------
    
    "potentiometer": ComponentDefinition(
        type="potentiometer",
        symbol="Device:R_Potentiometer",
        name="Potentiometer",
        default_value="10k",
        ref_prefix="RV",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(0, -3.81), "down"),
            PinDefinition(2, "2", PinOffset(3.81, 0), "right"),
            PinDefinition(3, "3", PinOffset(0, 3.81), "up"),
        ],
        lib_symbol_def='''
    (symbol "Device:R_Potentiometer" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "RV" (at -4.445 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "R_Potentiometer" (at -2.54 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "R_Potentiometer_0_1"
        (polyline (pts (xy 2.54 0) (xy 1.524 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.143 0) (xy 2.286 0.508) (xy 2.286 -0.508) (xy 1.143 0)) (stroke (width 0) (type default)) (fill (type none)))
        (rectangle (start 1.016 2.54) (end -1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "R_Potentiometer_1_1"
        (pin passive line (at 0 -5.08 90) (length 2.54) (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 5.08 0 180) (length 2.54) (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 5.08 270) (length 2.54) (name "3" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    # ----------------------------------------
    # BATTERY
    # ----------------------------------------
    
    "battery": ComponentDefinition(
        type="battery",
        symbol="Device:Battery",
        name="Battery",
        default_value="9V",
        ref_prefix="BT",
        default_rotation=0,
        pins=[
            PinDefinition(1, "+", PinOffset(0, -2.54), "down"),
            PinDefinition(2, "-", PinOffset(0, 2.54), "up"),
        ],
        lib_symbol_def='''
    (symbol "Device:Battery" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "BT" (at 2.54 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "Battery" (at 2.54 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 0 1.524 90) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 1.524 90) (effects (font (size 1.27 1.27)) hide))
      (symbol "Battery_0_1"
        (rectangle (start -2.286 -1.27) (end 2.286 -1.016) (stroke (width 0) (type default)) (fill (type outline)))
        (rectangle (start -1.016 1.27) (end 1.016 1.016) (stroke (width 0) (type default)) (fill (type outline)))
        (polyline (pts (xy 0 0.762) (xy 0 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 -2.54) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.762 2.286) (xy 0.762 1.778) (xy 0.762 1.778)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 1.016 2.032) (xy 0.508 2.032)) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "Battery_1_1"
        (pin passive line (at 0 5.08 270) (length 2.54) (name "+" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -5.08 90) (length 2.54) (name "-" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    # ----------------------------------------
    # SENSORS
    # ----------------------------------------
    
    "dht11": ComponentDefinition(
        type="dht11",
        symbol="Sensor:DHT11",
        name="DHT11 Temperature/Humidity",
        default_value="DHT11",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VCC", PinOffset(-5.08, 2.54), "left"),
            PinDefinition(2, "DATA", PinOffset(-5.08, 0), "left"),
            PinDefinition(3, "NC", PinOffset(5.08, 0), "right"),
            PinDefinition(4, "GND", PinOffset(-5.08, -2.54), "left"),
        ],
        lib_symbol_def='''
    (symbol "Sensor:DHT11" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 6.35 0) (effects (font (size 1.27 1.27))))
      (property "Value" "DHT11" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "DHT11_0_1"
        (rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
        (pin power_in line (at -7.62 2.54 0) (length 2.54) (name "VCC" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -7.62 0 0) (length 2.54) (name "DATA" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin no_connect line (at 7.62 0 180) (length 2.54) (name "NC" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -7.62 -2.54 0) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    "ldr": ComponentDefinition(
        type="ldr",
        symbol="Device:R_Photo",
        name="Light Dependent Resistor",
        default_value="LDR",
        ref_prefix="R",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(0, -PIN_OFFSET), "up"),
            PinDefinition(2, "2", PinOffset(0, PIN_OFFSET), "down"),
        ],
        lib_symbol_def='''
    (symbol "Device:R_Photo" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "LDR" (at 0 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "R_Photo_0_1"
        (rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -2.286 -1.778) (xy -1.27 -0.762)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -2.286 -0.508) (xy -1.27 0.508)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "R_Photo_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )''',
    ),
    
    # ----------------------------------------
    # BUZZER
    # ----------------------------------------
    
    "buzzer": ComponentDefinition(
        type="buzzer",
        symbol="Device:Buzzer",
        name="Buzzer",
        default_value="Buzzer",
        ref_prefix="BZ",
        default_rotation=0,
        pins=[
            PinDefinition(1, "+", PinOffset(-5.08, 0), "left"),
            PinDefinition(2, "-", PinOffset(5.08, 0), "right"),
        ],
        lib_symbol_def='''
    (symbol "Device:Buzzer" (in_bom yes) (on_board yes)
      (property "Reference" "BZ" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Buzzer" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (symbol "Buzzer_0_1"
        (circle (center 0 0) (radius 3.81) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "Buzzer_1_1"
        (pin passive line (at -7.62 0 0) (length 2.54) (name "+") (number "1"))
        (pin passive line (at 7.62 0 180) (length 2.54) (name "-") (number "2"))
      )
    )''',
    ),
    
    # ----------------------------------------
    # MOTORS
    # ----------------------------------------
    
    "dc_motor": ComponentDefinition(
        type="dc_motor",
        symbol="Motor:DC_Motor",
        name="DC Motor",
        default_value="DC Motor",
        ref_prefix="M",
        default_rotation=0,
        pins=[
            PinDefinition(1, "+", PinOffset(-5.08, 0), "left"),
            PinDefinition(2, "-", PinOffset(5.08, 0), "right"),
        ],
        lib_symbol_def='''
    (symbol "Motor:DC_Motor" (in_bom yes) (on_board yes)
      (property "Reference" "M" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Motor" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (symbol "DC_Motor_0_1"
        (circle (center 0 0) (radius 3.81) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "M" (at 0 0 0) (effects (font (size 2.54 2.54))))
      )
      (symbol "DC_Motor_1_1"
        (pin passive line (at -7.62 0 0) (length 2.54) (name "+") (number "1"))
        (pin passive line (at 7.62 0 180) (length 2.54) (name "-") (number "2"))
      )
    )''',
    ),
    
    "servo": ComponentDefinition(
        type="servo",
        symbol="Motor:Servo",
        name="Servo Motor",
        default_value="SG90",
        ref_prefix="M",
        default_rotation=0,
        pins=[
            PinDefinition(1, "GND", PinOffset(-7.62, -2.54), "left"),
            PinDefinition(2, "VCC", PinOffset(-7.62, 2.54), "left"),
            PinDefinition(3, "SIG", PinOffset(7.62, 0), "right"),
        ],
        lib_symbol_def='''
    (symbol "Motor:Servo" (in_bom yes) (on_board yes)
      (property "Reference" "M" (at 0 6.35 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Servo" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))
      (symbol "Servo_0_1"
        (rectangle (start -5.08 3.81) (end 5.08 -3.81) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "SERVO" (at 0 0 0) (effects (font (size 1.27 1.27))))
      )
      (symbol "Servo_1_1"
        (pin power_in line (at -10.16 -2.54 0) (length 2.54) (name "GND") (number "1"))
        (pin power_in line (at -10.16 2.54 0) (length 2.54) (name "VCC") (number "2"))
        (pin input line (at 10.16 0 180) (length 2.54) (name "SIG") (number "3"))
      )
    )''',
    ),
    
    # ----------------------------------------
    # RELAY
    # ----------------------------------------
    
    "relay_1ch": ComponentDefinition(
        type="relay_1ch",
        symbol="Module:Relay_1CH",
        name="Relay 1 Channel",
        default_value="5V Relay",
        ref_prefix="K",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VCC", PinOffset(-7.62, 3.81), "left"),
            PinDefinition(2, "GND", PinOffset(-7.62, -3.81), "left"),
            PinDefinition(3, "IN", PinOffset(-7.62, 0), "left"),
            PinDefinition(4, "COM", PinOffset(7.62, 2.54), "right"),
            PinDefinition(5, "NO", PinOffset(7.62, 0), "right"),
            PinDefinition(6, "NC", PinOffset(7.62, -2.54), "right"),
        ],
        lib_symbol_def='''
    (symbol "Module:Relay_1CH" (in_bom yes) (on_board yes)
      (property "Reference" "K" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Relay" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (symbol "Relay_1CH_0_1"
        (rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "RELAY" (at 0 0 0) (effects (font (size 1.27 1.27))))
      )
      (symbol "Relay_1CH_1_1"
        (pin power_in line (at -10.16 3.81 0) (length 2.54) (name "VCC") (number "1"))
        (pin power_in line (at -10.16 -3.81 0) (length 2.54) (name "GND") (number "2"))
        (pin input line (at -10.16 0 0) (length 2.54) (name "IN") (number "3"))
        (pin passive line (at 10.16 2.54 180) (length 2.54) (name "COM") (number "4"))
        (pin passive line (at 10.16 0 180) (length 2.54) (name "NO") (number "5"))
        (pin passive line (at 10.16 -2.54 180) (length 2.54) (name "NC") (number "6"))
      )
    )''',
    ),
    
    # ----------------------------------------
    # MICROCONTROLLERS
    # ----------------------------------------
    
    "arduino_uno": ComponentDefinition(
        type="arduino_uno",
        symbol="MCU_Module:Arduino_UNO_R3",
        name="Arduino UNO R3",
        default_value="Arduino UNO R3",
        ref_prefix="A",
        default_rotation=0,
        pins=[
            # Power pins
            PinDefinition(1, "3V3", PinOffset(-2.54, -25.4), "up"),
            PinDefinition(2, "5V", PinOffset(0, -25.4), "up"),
            PinDefinition(3, "Vin", PinOffset(2.54, -25.4), "up"),
            # Control pins
            PinDefinition(4, "RST", PinOffset(-15.24, -20.32), "left"),
            PinDefinition(5, "AREF", PinOffset(-15.24, -17.78), "left"),
            # Analog pins
            PinDefinition(6, "A0", PinOffset(-15.24, -10.16), "left"),
            PinDefinition(7, "A1", PinOffset(-15.24, -7.62), "left"),
            PinDefinition(8, "A2", PinOffset(-15.24, -5.08), "left"),
            PinDefinition(9, "A3", PinOffset(-15.24, -2.54), "left"),
            PinDefinition(10, "A4", PinOffset(-15.24, 0), "left"),
            PinDefinition(11, "A5", PinOffset(-15.24, 2.54), "left"),
            # GND
            PinDefinition(12, "GND", PinOffset(0, 25.4), "down"),
            # Digital pins
            PinDefinition(13, "D13", PinOffset(15.24, -20.32), "right"),
            PinDefinition(14, "D12", PinOffset(15.24, -17.78), "right"),
            PinDefinition(15, "D11", PinOffset(15.24, -15.24), "right"),
            PinDefinition(16, "D10", PinOffset(15.24, -12.7), "right"),
            PinDefinition(17, "D9", PinOffset(15.24, -10.16), "right"),
            PinDefinition(18, "D8", PinOffset(15.24, -7.62), "right"),
            PinDefinition(19, "D7", PinOffset(15.24, -5.08), "right"),
            PinDefinition(20, "D6", PinOffset(15.24, -2.54), "right"),
            PinDefinition(21, "D5", PinOffset(15.24, 0), "right"),
            PinDefinition(22, "D4", PinOffset(15.24, 2.54), "right"),
            PinDefinition(23, "D3", PinOffset(15.24, 5.08), "right"),
            PinDefinition(24, "D2", PinOffset(15.24, 7.62), "right"),
            PinDefinition(25, "D1", PinOffset(15.24, 10.16), "right"),
            PinDefinition(26, "D0", PinOffset(15.24, 12.7), "right"),
        ],
        lib_symbol_def='''
    (symbol "MCU_Module:Arduino_UNO_R3" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "A" (at 0 26.67 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Arduino_UNO_R3" (at 0 24.13 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Module:Arduino_UNO_R3" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Arduino_UNO_R3_0_1"
        (rectangle (start -12.7 22.86) (end 12.7 -22.86) (stroke (width 0.254) (type default)) (fill (type background)))
        (text "ARDUINO\\nUNO" (at 0 0 0) (effects (font (size 3.81 3.81) bold)))
      )
    )''',
    ),
    
    "esp32": ComponentDefinition(
        type="esp32",
        symbol="RF_Module:ESP32-WROOM-32",
        name="ESP32-WROOM-32",
        default_value="ESP32-WROOM-32",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            # Left side
            PinDefinition(1, "GND", PinOffset(-15.24, 22.86), "left"),
            PinDefinition(2, "3V3", PinOffset(-15.24, 20.32), "left"),
            PinDefinition(3, "EN", PinOffset(-15.24, 17.78), "left"),
            PinDefinition(4, "SENSOR_VP", PinOffset(-15.24, 15.24), "left"),
            PinDefinition(5, "SENSOR_VN", PinOffset(-15.24, 12.7), "left"),
            PinDefinition(6, "IO34", PinOffset(-15.24, 10.16), "left"),
            PinDefinition(7, "IO35", PinOffset(-15.24, 7.62), "left"),
            PinDefinition(8, "IO32", PinOffset(-15.24, 5.08), "left"),
            PinDefinition(9, "IO33", PinOffset(-15.24, 2.54), "left"),
            PinDefinition(10, "IO25", PinOffset(-15.24, 0), "left"),
            PinDefinition(11, "IO26", PinOffset(-15.24, -2.54), "left"),
            PinDefinition(12, "IO27", PinOffset(-15.24, -5.08), "left"),
            PinDefinition(13, "IO14", PinOffset(-15.24, -7.62), "left"),
            PinDefinition(14, "IO12", PinOffset(-15.24, -10.16), "left"),
            PinDefinition(15, "GND2", PinOffset(-15.24, -12.7), "left"),
            PinDefinition(16, "IO13", PinOffset(-15.24, -15.24), "left"),
            PinDefinition(17, "SD2", PinOffset(-15.24, -17.78), "left"),
            PinDefinition(18, "SD3", PinOffset(-15.24, -20.32), "left"),
            PinDefinition(19, "CMD", PinOffset(-15.24, -22.86), "left"),
            # Right side
            PinDefinition(20, "CLK", PinOffset(15.24, -22.86), "right"),
            PinDefinition(21, "SD0", PinOffset(15.24, -20.32), "right"),
            PinDefinition(22, "SD1", PinOffset(15.24, -17.78), "right"),
            PinDefinition(23, "IO15", PinOffset(15.24, -15.24), "right"),
            PinDefinition(24, "IO2", PinOffset(15.24, -12.7), "right"),
            PinDefinition(25, "IO0", PinOffset(15.24, -10.16), "right"),
            PinDefinition(26, "IO4", PinOffset(15.24, -7.62), "right"),
            PinDefinition(27, "IO16", PinOffset(15.24, -5.08), "right"),
            PinDefinition(28, "IO17", PinOffset(15.24, -2.54), "right"),
            PinDefinition(29, "IO5", PinOffset(15.24, 0), "right"),
            PinDefinition(30, "IO18", PinOffset(15.24, 2.54), "right"),
            PinDefinition(31, "IO19", PinOffset(15.24, 5.08), "right"),
            PinDefinition(32, "NC", PinOffset(15.24, 7.62), "right"),
            PinDefinition(33, "IO21", PinOffset(15.24, 10.16), "right"),
            PinDefinition(34, "RXD0", PinOffset(15.24, 12.7), "right"),
            PinDefinition(35, "TXD0", PinOffset(15.24, 15.24), "right"),
            PinDefinition(36, "IO22", PinOffset(15.24, 17.78), "right"),
            PinDefinition(37, "IO23", PinOffset(15.24, 20.32), "right"),
            PinDefinition(38, "GND3", PinOffset(15.24, 22.86), "right"),
        ],
        lib_symbol_def='''
    (symbol "RF_Module:ESP32-WROOM-32" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 26.67 0) (effects (font (size 1.27 1.27))))
      (property "Value" "ESP32-WROOM-32" (at 0 -26.67 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "RF_Module:ESP32-WROOM-32" (at 0 -30 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "ESP32-WROOM-32_0_1"
        (rectangle (start -12.7 25.4) (end 12.7 -25.4) (stroke (width 0.254) (type default)) (fill (type background)))
      )
    )''',
    ),
    
    # ----------------------------------------
    # CONNECTORS
    # ----------------------------------------
    
    "conn_2pin": ComponentDefinition(
        type="conn_2pin",
        symbol="Connector:Conn_01x02",
        name="2-Pin Connector",
        default_value="Conn_2",
        ref_prefix="J",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(-5.08, 1.27), "left"),
            PinDefinition(2, "2", PinOffset(-5.08, -1.27), "left"),
        ],
        lib_symbol_def='''
    (symbol "Connector:Conn_01x02" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Conn_01x02" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (symbol "Conn_01x02_0_1"
        (rectangle (start -2.54 2.54) (end 2.54 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
        (pin passive line (at -5.08 0 0) (length 2.54) (name "1") (number "1"))
        (pin passive line (at -5.08 -2.54 0) (length 2.54) (name "2") (number "2"))
      )
    )''',
    ),
    
    "conn_3pin": ComponentDefinition(
        type="conn_3pin",
        symbol="Connector:Conn_01x03",
        name="3-Pin Connector",
        default_value="Conn_3",
        ref_prefix="J",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(-5.08, 2.54), "left"),
            PinDefinition(2, "2", PinOffset(-5.08, 0), "left"),
            PinDefinition(3, "3", PinOffset(-5.08, -2.54), "left"),
        ],
        lib_symbol_def='''
    (symbol "Connector:Conn_01x03" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Conn_01x03" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (symbol "Conn_01x03_0_1"
        (rectangle (start -2.54 3.81) (end 2.54 -3.81) (stroke (width 0.254) (type default)) (fill (type background)))
        (pin passive line (at -5.08 2.54 0) (length 2.54) (name "1") (number "1"))
        (pin passive line (at -5.08 0 0) (length 2.54) (name "2") (number "2"))
        (pin passive line (at -5.08 -2.54 0) (length 2.54) (name "3") (number "3"))
      )
    )''',
    ),
}


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_component(component_type: str) -> Optional[ComponentDefinition]:
    """Get component definition by type (case-insensitive)."""
    return COMPONENT_LIBRARY.get(component_type.lower())


def get_available_components() -> list[str]:
    """Get list of all available component types."""
    return list(COMPONENT_LIBRARY.keys())


def get_pin_position_with_rotation(
    component_x: float,
    component_y: float,
    pin: PinDefinition,
    rotation_degrees: float
) -> tuple[float, float]:
    """
    Get pin position after rotation.
    KiCad rotation is counter-clockwise in degrees.
    
    Args:
        component_x: X position of component center
        component_y: Y position of component center
        pin: Pin definition
        rotation_degrees: Rotation in degrees (counter-clockwise)
        
    Returns:
        Tuple of (x, y) absolute position
    """
    rad = math.radians(rotation_degrees)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)
    
    # Rotate the offset
    rotated_dx = pin.offset.dx * cos_r - pin.offset.dy * sin_r
    rotated_dy = pin.offset.dx * sin_r + pin.offset.dy * cos_r
    
    return (
        component_x + rotated_dx,
        component_y + rotated_dy
    )


def get_component_info_for_ai() -> str:
    """Get component information formatted for AI prompts."""
    lines = ["KOMPONEN TERSEDIA:"]
    
    for comp_type, comp_def in COMPONENT_LIBRARY.items():
        pin_info = ", ".join(f"pin{p.number}={p.name}" for p in comp_def.pins)
        lines.append(f"- {comp_type}: {comp_def.name} ({comp_def.symbol}) [{pin_info}]")
    
    return "\n".join(lines)


# ============================================
# MODULE INFO
# ============================================

# Component count for reference
COMPONENT_COUNT = len(COMPONENT_LIBRARY)

# Categories
COMPONENT_CATEGORIES = {
    "passive": ["resistor", "capacitor", "capacitor_polarized", "inductor", "potentiometer"],
    "diodes": ["led", "diode", "zener"],
    "power": ["vcc", "gnd", "battery"],
    "transistors": ["npn", "pnp"],
    "ics": ["ne555", "lm7805"],
    "switches": ["switch"],
    "sensors": ["dht11", "ldr"],
    "actuators": ["buzzer", "dc_motor", "servo", "relay_1ch"],
    "microcontrollers": ["arduino_uno", "esp32"],
    "connectors": ["conn_2pin", "conn_3pin"],
}
