"""
JAWIR OS - KiCad Component Library V2
FIXED: Proper pin positions that MATCH symbol definitions.

The key insight: Pin positions in the symbol definition (lib_symbol_def) 
MUST match the offsets we use for wire routing.
"""

from dataclasses import dataclass
from typing import Literal, Optional
import math

# ============================================
# CONSTANTS
# ============================================

# Standard KiCad pin offsets (in mm) - from actual KiCad symbols
PIN_OFFSET = 3.81  # Standard 2-pin component offset


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


@dataclass
class ComponentDefinition:
    """Complete definition of a KiCad component"""
    type: str
    symbol: str  # KiCad library:symbol format
    name: str
    default_value: str
    ref_prefix: str
    default_rotation: float
    pins: list[PinDefinition]
    lib_symbol_def: str  # Complete S-expression including pins!


# ============================================
# VALIDATED SYMBOL DEFINITIONS
# These are taken directly from KiCad and VERIFIED to work
# ============================================

# Resistor symbol - vertical orientation, pin1 at top, pin2 at bottom
RESISTOR_SYMBOL = '''
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
    )'''

# Capacitor symbol
CAPACITOR_SYMBOL = '''
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
    )'''

# LED symbol - HORIZONTAL at rotation 0, pin1 (K) at left, pin2 (A) at right
LED_SYMBOL = '''
    (symbol "Device:LED" (pin_numbers hide) (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "LED" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "LED_0_1"
        (polyline (pts (xy -1.27 -1.27) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 0) (xy 1.27 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy -3.048 -1.524) (xy -1.27 0.254)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -1.778 -0.762) (xy 0 1.016)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy -1.27 0.254) (xy -1.778 0.254) (xy -1.778 -0.254)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 1.016) (xy -0.508 1.016) (xy -0.508 0.508)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "LED_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54) (name "K" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 3.81 0 180) (length 2.54) (name "A" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

# DHT11 sensor - pins on left side
DHT11_SYMBOL = '''
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
    )'''

# VCC Power symbol
VCC_SYMBOL = '''
    (symbol "power:VCC" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "VCC" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "VCC_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "VCC_1_1" 
        (pin power_in line (at 0 0 90) (length 0) (name "VCC" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )'''

# GND Power symbol
GND_SYMBOL = '''
    (symbol "power:GND" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
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
    )'''

# NPN Transistor
NPN_SYMBOL = '''
    (symbol "Device:Q_NPN_BCE" (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "Q" (at 5.08 1.905 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "Q_NPN_BCE" (at 5.08 0 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 5.08 2.54 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Q_NPN_BCE_0_1"
        (polyline (pts (xy 0.635 0.635) (xy 2.54 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.635 -0.635) (xy 2.54 -2.54) (xy 2.54 -2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.635 1.905) (xy 0.635 -1.905) (xy 0.635 -1.905)) (stroke (width 0.508) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 -1.778) (xy 1.778 -1.27) (xy 2.286 -2.286) (xy 1.27 -1.778) (xy 1.27 -1.778)) (stroke (width 0) (type default)) (fill (type outline)))
      )
      (symbol "Q_NPN_BCE_1_1"
        (pin passive line (at -2.54 0 0) (length 3.175) (name "B" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 5.08 270) (length 2.54) (name "C" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 2.54 -5.08 90) (length 2.54) (name "E" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      )
    )'''

# ESP32 - SIMPLIFIED with just rectangle (complex IC)
# For complex ICs, we generate pins dynamically
ESP32_SYMBOL = '''
    (symbol "RF_Module:ESP32-WROOM-32" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 26.67 0) (effects (font (size 1.27 1.27))))
      (property "Value" "ESP32-WROOM-32" (at 0 -26.67 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "RF_Module:ESP32-WROOM-32" (at 0 -30 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "ESP32-WROOM-32_0_1"
        (rectangle (start -12.7 25.4) (end 12.7 -25.4) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "ESP32-WROOM-32_1_1"
        (pin power_in line (at -15.24 22.86 0) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -15.24 20.32 0) (length 2.54) (name "3V3" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin input line (at -15.24 17.78 0) (length 2.54) (name "EN" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin input line (at -15.24 15.24 0) (length 2.54) (name "VP" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin input line (at -15.24 12.7 0) (length 2.54) (name "VN" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 10.16 0) (length 2.54) (name "IO34" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 7.62 0) (length 2.54) (name "IO35" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 5.08 0) (length 2.54) (name "IO32" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 2.54 0) (length 2.54) (name "IO33" (effects (font (size 1.27 1.27)))) (number "9" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 0 0) (length 2.54) (name "IO25" (effects (font (size 1.27 1.27)))) (number "10" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 -2.54 0) (length 2.54) (name "IO26" (effects (font (size 1.27 1.27)))) (number "11" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 -5.08 0) (length 2.54) (name "IO27" (effects (font (size 1.27 1.27)))) (number "12" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 -7.62 0) (length 2.54) (name "IO14" (effects (font (size 1.27 1.27)))) (number "13" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 -10.16 0) (length 2.54) (name "IO12" (effects (font (size 1.27 1.27)))) (number "14" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -15.24 -12.7 0) (length 2.54) (name "GND2" (effects (font (size 1.27 1.27)))) (number "15" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 -15.24 0) (length 2.54) (name "IO13" (effects (font (size 1.27 1.27)))) (number "16" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 -17.78 0) (length 2.54) (name "SD2" (effects (font (size 1.27 1.27)))) (number "17" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 -20.32 0) (length 2.54) (name "SD3" (effects (font (size 1.27 1.27)))) (number "18" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 -22.86 0) (length 2.54) (name "CMD" (effects (font (size 1.27 1.27)))) (number "19" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 -22.86 180) (length 2.54) (name "CLK" (effects (font (size 1.27 1.27)))) (number "20" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 -20.32 180) (length 2.54) (name "SD0" (effects (font (size 1.27 1.27)))) (number "21" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 -17.78 180) (length 2.54) (name "SD1" (effects (font (size 1.27 1.27)))) (number "22" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 -15.24 180) (length 2.54) (name "IO15" (effects (font (size 1.27 1.27)))) (number "23" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 -12.7 180) (length 2.54) (name "IO2" (effects (font (size 1.27 1.27)))) (number "24" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 -10.16 180) (length 2.54) (name "IO0" (effects (font (size 1.27 1.27)))) (number "25" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 -7.62 180) (length 2.54) (name "IO4" (effects (font (size 1.27 1.27)))) (number "26" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 -5.08 180) (length 2.54) (name "IO16" (effects (font (size 1.27 1.27)))) (number "27" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 -2.54 180) (length 2.54) (name "IO17" (effects (font (size 1.27 1.27)))) (number "28" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 0 180) (length 2.54) (name "IO5" (effects (font (size 1.27 1.27)))) (number "29" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 2.54 180) (length 2.54) (name "IO18" (effects (font (size 1.27 1.27)))) (number "30" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 5.08 180) (length 2.54) (name "IO19" (effects (font (size 1.27 1.27)))) (number "31" (effects (font (size 1.27 1.27)))))
        (pin no_connect line (at 15.24 7.62 180) (length 2.54) (name "NC" (effects (font (size 1.27 1.27)))) (number "32" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 10.16 180) (length 2.54) (name "IO21" (effects (font (size 1.27 1.27)))) (number "33" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 12.7 180) (length 2.54) (name "RXD0" (effects (font (size 1.27 1.27)))) (number "34" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 15.24 180) (length 2.54) (name "TXD0" (effects (font (size 1.27 1.27)))) (number "35" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 17.78 180) (length 2.54) (name "IO22" (effects (font (size 1.27 1.27)))) (number "36" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 15.24 20.32 180) (length 2.54) (name "IO23" (effects (font (size 1.27 1.27)))) (number "37" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 15.24 22.86 180) (length 2.54) (name "GND3" (effects (font (size 1.27 1.27)))) (number "38" (effects (font (size 1.27 1.27)))))
      )
    )'''

# Arduino Uno - ATmega328P based development board
# Simplified symbol with essential pins
ARDUINO_UNO_SYMBOL = '''
    (symbol "MCU_Module:Arduino_UNO_R3" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 30.48 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Arduino_UNO_R3" (at 0 -30.48 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Module:Arduino_UNO_R3" (at 0 -33 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "https://www.arduino.cc/en/Main/arduinoBoardUno" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Arduino_UNO_R3_0_1"
        (rectangle (start -15.24 27.94) (end 15.24 -27.94) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "Arduino_UNO_R3_1_1"
        (pin power_in line (at -17.78 25.4 0) (length 2.54) (name "NC" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -17.78 22.86 0) (length 2.54) (name "IOREF" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin input line (at -17.78 20.32 0) (length 2.54) (name "RESET" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at -17.78 17.78 0) (length 2.54) (name "3V3" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at -17.78 15.24 0) (length 2.54) (name "5V" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -17.78 12.7 0) (length 2.54) (name "GND1" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -17.78 10.16 0) (length 2.54) (name "GND2" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -17.78 7.62 0) (length 2.54) (name "VIN" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))
        (pin input line (at -17.78 5.08 0) (length 2.54) (name "A0" (effects (font (size 1.27 1.27)))) (number "9" (effects (font (size 1.27 1.27)))))
        (pin input line (at -17.78 2.54 0) (length 2.54) (name "A1" (effects (font (size 1.27 1.27)))) (number "10" (effects (font (size 1.27 1.27)))))
        (pin input line (at -17.78 0 0) (length 2.54) (name "A2" (effects (font (size 1.27 1.27)))) (number "11" (effects (font (size 1.27 1.27)))))
        (pin input line (at -17.78 -2.54 0) (length 2.54) (name "A3" (effects (font (size 1.27 1.27)))) (number "12" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -17.78 -5.08 0) (length 2.54) (name "A4/SDA" (effects (font (size 1.27 1.27)))) (number "13" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -17.78 -7.62 0) (length 2.54) (name "A5/SCL" (effects (font (size 1.27 1.27)))) (number "14" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 -25.4 180) (length 2.54) (name "D0/RX" (effects (font (size 1.27 1.27)))) (number "15" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 -22.86 180) (length 2.54) (name "D1/TX" (effects (font (size 1.27 1.27)))) (number "16" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 -20.32 180) (length 2.54) (name "D2" (effects (font (size 1.27 1.27)))) (number "17" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 -17.78 180) (length 2.54) (name "D3" (effects (font (size 1.27 1.27)))) (number "18" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 -15.24 180) (length 2.54) (name "D4" (effects (font (size 1.27 1.27)))) (number "19" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 -12.7 180) (length 2.54) (name "D5" (effects (font (size 1.27 1.27)))) (number "20" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 -10.16 180) (length 2.54) (name "D6" (effects (font (size 1.27 1.27)))) (number "21" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 -7.62 180) (length 2.54) (name "D7" (effects (font (size 1.27 1.27)))) (number "22" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 -5.08 180) (length 2.54) (name "D8" (effects (font (size 1.27 1.27)))) (number "23" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 -2.54 180) (length 2.54) (name "D9" (effects (font (size 1.27 1.27)))) (number "24" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 0 180) (length 2.54) (name "D10/SS" (effects (font (size 1.27 1.27)))) (number "25" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 2.54 180) (length 2.54) (name "D11/MOSI" (effects (font (size 1.27 1.27)))) (number "26" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 5.08 180) (length 2.54) (name "D12/MISO" (effects (font (size 1.27 1.27)))) (number "27" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 7.62 180) (length 2.54) (name "D13/SCK" (effects (font (size 1.27 1.27)))) (number "28" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 17.78 10.16 180) (length 2.54) (name "GND3" (effects (font (size 1.27 1.27)))) (number "29" (effects (font (size 1.27 1.27)))))
        (pin input line (at 17.78 12.7 180) (length 2.54) (name "AREF" (effects (font (size 1.27 1.27)))) (number "30" (effects (font (size 1.27 1.27)))))
      )
    )'''

# Connector 2 pin
CONN_2PIN_SYMBOL = '''
    (symbol "Connector:Conn_01x02" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Conn_01x02" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Conn_01x02_1_1"
        (rectangle (start -1.27 1.27) (end 1.27 -3.81) (stroke (width 0.254) (type default)) (fill (type background)))
        (pin passive line (at -3.81 0 0) (length 2.54) (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -3.81 -2.54 0) (length 2.54) (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

# Connector 3 pin
CONN_3PIN_SYMBOL = '''
    (symbol "Connector:Conn_01x03" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Conn_01x03" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Conn_01x03_1_1"
        (rectangle (start -1.27 2.54) (end 1.27 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
        (pin passive line (at -3.81 1.27 0) (length 2.54) (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -3.81 -1.27 0) (length 2.54) (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -3.81 -3.81 0) (length 2.54) (name "3" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      )
    )'''

# Connector 4 pin
CONN_4PIN_SYMBOL = '''
    (symbol "Connector:Conn_01x04" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Conn_01x04" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Conn_01x04_1_1"
        (rectangle (start -1.27 3.81) (end 1.27 -6.35) (stroke (width 0.254) (type default)) (fill (type background)))
        (pin passive line (at -3.81 2.54 0) (length 2.54) (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -3.81 0 0) (length 2.54) (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -3.81 -2.54 0) (length 2.54) (name "3" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -3.81 -5.08 0) (length 2.54) (name "4" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      )
    )'''

# HC-SR04 Ultrasonic Sensor - 4 pins
HCSR04_SYMBOL = '''
    (symbol "Sensor_Proximity:HC-SR04" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 8.89 0) (effects (font (size 1.27 1.27))))
      (property "Value" "HC-SR04" (at 0 -8.89 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "HC-SR04_0_1"
        (rectangle (start -7.62 7.62) (end 7.62 -7.62) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "HC-SR04_1_1"
        (pin power_in line (at -10.16 5.08 0) (length 2.54) (name "VCC" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin input line (at -10.16 2.54 0) (length 2.54) (name "TRIG" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin output line (at -10.16 0 0) (length 2.54) (name "ECHO" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -10.16 -2.54 0) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      )
    )'''

# Rotary Encoder - 5 pins (A, B, SW, VCC, GND)
ROTARY_ENCODER_SYMBOL = '''
    (symbol "Device:RotaryEncoder_Switch" (pin_names (offset 0.254) hide) (in_bom yes) (on_board yes)
      (property "Reference" "SW" (at 0 6.35 0) (effects (font (size 1.27 1.27))))
      (property "Value" "RotaryEncoder_Switch" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at -2.54 3.81 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "RotaryEncoder_Switch_0_1"
        (rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "RotaryEncoder_Switch_1_1"
        (pin passive line (at -7.62 2.54 0) (length 2.54) (name "A" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -7.62 0 0) (length 2.54) (name "C" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -7.62 -2.54 0) (length 2.54) (name "B" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 7.62 2.54 180) (length 2.54) (name "S1" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 7.62 -2.54 180) (length 2.54) (name "S2" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
      )
    )'''

# Button/Switch
BUTTON_SYMBOL = '''
    (symbol "Switch:SW_Push" (pin_numbers hide) (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "SW" (at 1.27 6.35 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "SW_Push" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 5.08 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 5.08 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "SW_Push_0_1"
        (circle (center -2.032 0) (radius 0.508) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 1.27) (xy 0 3.048)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 2.54 1.27) (xy -2.54 1.27)) (stroke (width 0) (type default)) (fill (type none)))
        (circle (center 2.032 0) (radius 0.508) (stroke (width 0) (type default)) (fill (type none)))
        (pin passive line (at -5.08 0 0) (length 2.54) (name "1" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 5.08 0 180) (length 2.54) (name "2" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )'''

# ============================================
# NEW COMPONENTS FROM JAWI-OS LIBRARY
# ============================================

# DHT22 Temperature & Humidity Sensor
DHT22_SYMBOL = '''
    (symbol "Sensor:DHT22" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "DHT22" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "DHT22_0_1"
        (rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "DHT22_1_1"
        (pin power_in line (at -10.16 3.81 0) (length 2.54) (name "VCC") (number "1"))
        (pin bidirectional line (at 10.16 0 180) (length 2.54) (name "DATA") (number "2"))
        (pin no_connect line (at 10.16 -2.54 180) (length 2.54) (name "NC") (number "3"))
        (pin power_in line (at -10.16 -3.81 0) (length 2.54) (name "GND") (number "4"))
      )
    )'''

# BMP280 Pressure Sensor (I2C)
BMP280_SYMBOL = '''
    (symbol "Sensor:BMP280" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "BMP280" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "BMP280_0_1"
        (rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "BMP280_1_1"
        (pin power_in line (at -10.16 3.81 0) (length 2.54) (name "VCC") (number "1"))
        (pin power_in line (at -10.16 -3.81 0) (length 2.54) (name "GND") (number "2"))
        (pin input line (at 10.16 2.54 180) (length 2.54) (name "SCL") (number "3"))
        (pin bidirectional line (at 10.16 -2.54 180) (length 2.54) (name "SDA") (number "4"))
      )
    )'''

# PIR Motion Sensor
PIR_SYMBOL = '''
    (symbol "Sensor:PIR" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "PIR" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "PIR_0_1"
        (rectangle (start -5.08 3.81) (end 5.08 -3.81) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "PIR_1_1"
        (pin power_in line (at -7.62 2.54 0) (length 2.54) (name "VCC") (number "1"))
        (pin output line (at 7.62 0 180) (length 2.54) (name "OUT") (number "2"))
        (pin power_in line (at -7.62 -2.54 0) (length 2.54) (name "GND") (number "3"))
      )
    )'''

# LDR (Light Dependent Resistor)
LDR_SYMBOL = '''
    (symbol "Device:R_Photo" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "LDR" (at 0 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "R_Photo_0_1"
        (rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "R_Photo_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27) (name "~") (number "1"))
        (pin passive line (at 0 -3.81 90) (length 1.27) (name "~") (number "2"))
      )
    )'''

# OLED Display SSD1306
OLED_SSD1306_SYMBOL = '''
    (symbol "Display:OLED_SSD1306" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "SSD1306" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "OLED_SSD1306_0_1"
        (rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "OLED_SSD1306_1_1"
        (pin power_in line (at -10.16 -3.81 0) (length 2.54) (name "GND") (number "1"))
        (pin power_in line (at -10.16 3.81 0) (length 2.54) (name "VCC") (number "2"))
        (pin input line (at 10.16 2.54 180) (length 2.54) (name "SCL") (number "3"))
        (pin bidirectional line (at 10.16 -2.54 180) (length 2.54) (name "SDA") (number "4"))
      )
    )'''

# Servo Motor
SERVO_SYMBOL = '''
    (symbol "Motor:Servo" (in_bom yes) (on_board yes)
      (property "Reference" "M" (at 0 6.35 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Servo" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Servo_0_1"
        (rectangle (start -5.08 3.81) (end 5.08 -3.81) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "Servo_1_1"
        (pin power_in line (at -10.16 -2.54 0) (length 2.54) (name "GND") (number "1"))
        (pin power_in line (at -10.16 2.54 0) (length 2.54) (name "VCC") (number "2"))
        (pin input line (at 10.16 0 180) (length 2.54) (name "SIG") (number "3"))
      )
    )'''

# Buzzer
BUZZER_SYMBOL = '''
    (symbol "Device:Buzzer" (in_bom yes) (on_board yes)
      (property "Reference" "BZ" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Buzzer" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Buzzer_0_1"
        (circle (center 0 0) (radius 3.81) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "Buzzer_1_1"
        (pin passive line (at -7.62 0 0) (length 2.54) (name "+") (number "1"))
        (pin passive line (at 7.62 0 180) (length 2.54) (name "-") (number "2"))
      )
    )'''

# Relay 1 Channel Module
RELAY_1CH_SYMBOL = '''
    (symbol "Module:Relay_1CH" (in_bom yes) (on_board yes)
      (property "Reference" "K" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Relay" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "Relay_1CH_0_1"
        (rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "Relay_1CH_1_1"
        (pin power_in line (at -10.16 3.81 0) (length 2.54) (name "VCC") (number "1"))
        (pin power_in line (at -10.16 -3.81 0) (length 2.54) (name "GND") (number "2"))
        (pin input line (at -10.16 0 0) (length 2.54) (name "IN") (number "3"))
        (pin passive line (at 10.16 2.54 180) (length 2.54) (name "COM") (number "4"))
        (pin passive line (at 10.16 0 180) (length 2.54) (name "NO") (number "5"))
        (pin passive line (at 10.16 -2.54 180) (length 2.54) (name "NC") (number "6"))
      )
    )'''

# L298N Motor Driver
L298N_SYMBOL = '''
    (symbol "Module:L298N" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 17.78 0) (effects (font (size 1.27 1.27))))
      (property "Value" "L298N" (at 0 -17.78 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "L298N_0_1"
        (rectangle (start -10.16 15.24) (end 10.16 -15.24) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "L298N_1_1"
        (pin power_in line (at -12.7 12.7 0) (length 2.54) (name "VCC") (number "1"))
        (pin power_in line (at -12.7 10.16 0) (length 2.54) (name "GND") (number "2"))
        (pin power_out line (at -12.7 7.62 0) (length 2.54) (name "5V") (number "3"))
        (pin input line (at -12.7 2.54 0) (length 2.54) (name "ENA") (number "4"))
        (pin input line (at -12.7 0 0) (length 2.54) (name "IN1") (number "5"))
        (pin input line (at -12.7 -2.54 0) (length 2.54) (name "IN2") (number "6"))
        (pin input line (at -12.7 -5.08 0) (length 2.54) (name "IN3") (number "7"))
        (pin input line (at -12.7 -7.62 0) (length 2.54) (name "IN4") (number "8"))
        (pin input line (at -12.7 -10.16 0) (length 2.54) (name "ENB") (number "9"))
        (pin output line (at 12.7 5.08 180) (length 2.54) (name "OUT1") (number "10"))
        (pin output line (at 12.7 2.54 180) (length 2.54) (name "OUT2") (number "11"))
        (pin output line (at 12.7 -2.54 180) (length 2.54) (name "OUT3") (number "12"))
        (pin output line (at 12.7 -5.08 180) (length 2.54) (name "OUT4") (number "13"))
      )
    )'''

# Soil Moisture Sensor
SOIL_MOISTURE_SYMBOL = '''
    (symbol "Sensor:SoilMoisture" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "Soil" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "SoilMoisture_0_1"
        (rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "SoilMoisture_1_1"
        (pin power_in line (at -10.16 3.81 0) (length 2.54) (name "VCC") (number "1"))
        (pin power_in line (at -10.16 -3.81 0) (length 2.54) (name "GND") (number "2"))
        (pin output line (at 10.16 2.54 180) (length 2.54) (name "DO") (number "3"))
        (pin output line (at 10.16 -2.54 180) (length 2.54) (name "AO") (number "4"))
      )
    )'''

# MQ-2 Gas Sensor
MQ2_SYMBOL = '''
    (symbol "Sensor:MQ-2" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 7.62 0) (effects (font (size 1.27 1.27))))
      (property "Value" "MQ-2" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "MQ-2_0_1"
        (rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "MQ-2_1_1"
        (pin power_in line (at -10.16 3.81 0) (length 2.54) (name "VCC") (number "1"))
        (pin power_in line (at -10.16 -3.81 0) (length 2.54) (name "GND") (number "2"))
        (pin output line (at 10.16 2.54 180) (length 2.54) (name "DO") (number "3"))
        (pin output line (at 10.16 -2.54 180) (length 2.54) (name "AO") (number "4"))
      )
    )'''

# Potentiometer
POTENTIOMETER_SYMBOL = '''
    (symbol "Device:R_Potentiometer" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "RV" (at -4.445 0 90) (effects (font (size 1.27 1.27))))
      (property "Value" "Pot" (at -2.54 0 90) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "R_Potentiometer_0_1"
        (rectangle (start 1.016 2.54) (end -1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 2.54 0) (xy 1.524 0)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "R_Potentiometer_1_1"
        (pin passive line (at 0 -5.08 90) (length 2.54) (name "1") (number "1"))
        (pin passive line (at 5.08 0 180) (length 2.54) (name "2") (number "2"))
        (pin passive line (at 0 5.08 270) (length 2.54) (name "3") (number "3"))
      )
    )'''

# IR Receiver Module
IR_RECEIVER_SYMBOL = '''
    (symbol "Sensor:IR_Receiver" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
      (property "Value" "IR_RX" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "IR_Receiver_0_1"
        (rectangle (start -5.08 3.81) (end 5.08 -3.81) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "IR_Receiver_1_1"
        (pin output line (at 10.16 0 180) (length 2.54) (name "OUT") (number "1"))
        (pin power_in line (at -10.16 -2.54 0) (length 2.54) (name "GND") (number "2"))
        (pin power_in line (at -10.16 2.54 0) (length 2.54) (name "VCC") (number "3"))
      )
    )'''


# ============================================
# COMPONENT LIBRARY - PIN OFFSETS MUST MATCH LIB_SYMBOL_DEF!
# ============================================

COMPONENT_LIBRARY: dict[str, ComponentDefinition] = {
    # ----------------------------------------
    # PASSIVE COMPONENTS - 2 pin vertical
    # Pin at (0, 3.81) in symbol = offset (0, -3.81) from center
    # Pin at (0, -3.81) in symbol = offset (0, 3.81) from center
    # NOTE: KiCad Y axis is INVERTED (positive = down in schematic view)
    # ----------------------------------------
    
    "resistor": ComponentDefinition(
        type="resistor",
        symbol="Device:R",
        name="Resistor",
        default_value="10k",
        ref_prefix="R",
        default_rotation=0,
        pins=[
            # Pin 1 is at (0, 3.81) in symbol - that's TOP in KiCad
            # In KiCad, Y+ is DOWN, so top = negative Y offset from center
            PinDefinition(1, "1", PinOffset(0, -PIN_OFFSET)),
            PinDefinition(2, "2", PinOffset(0, PIN_OFFSET)),
        ],
        lib_symbol_def=RESISTOR_SYMBOL,
    ),
    
    "capacitor": ComponentDefinition(
        type="capacitor",
        symbol="Device:C",
        name="Capacitor",
        default_value="100nF",
        ref_prefix="C",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(0, -PIN_OFFSET)),
            PinDefinition(2, "2", PinOffset(0, PIN_OFFSET)),
        ],
        lib_symbol_def=CAPACITOR_SYMBOL,
    ),
    
    # ----------------------------------------
    # LED - Horizontal at rotation 0
    # Pin 1 (K) at left (-3.81, 0), Pin 2 (A) at right (3.81, 0)
    # ----------------------------------------
    
    "led": ComponentDefinition(
        type="led",
        symbol="Device:LED",
        name="LED",
        default_value="Red",
        ref_prefix="D",
        default_rotation=90,  # Default vertical for typical use
        pins=[
            # At rotation 0: pin1 left, pin2 right
            PinDefinition(1, "K", PinOffset(-PIN_OFFSET, 0)),
            PinDefinition(2, "A", PinOffset(PIN_OFFSET, 0)),
        ],
        lib_symbol_def=LED_SYMBOL,
    ),
    
    # ----------------------------------------
    # DHT11 Sensor
    # Pins on left side at x=-7.62 (after wire end, component edge is -5.08)
    # ----------------------------------------
    
    "dht11": ComponentDefinition(
        type="dht11",
        symbol="Sensor:DHT11",
        name="DHT11 Sensor",
        default_value="DHT11",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            # Pins are on LEFT at x=-7.62 (wire connection point)
            PinDefinition(1, "VCC", PinOffset(-7.62, 2.54)),
            PinDefinition(2, "DATA", PinOffset(-7.62, 0)),
            PinDefinition(3, "NC", PinOffset(7.62, 0)),
            PinDefinition(4, "GND", PinOffset(-7.62, -2.54)),
        ],
        lib_symbol_def=DHT11_SYMBOL,
    ),
    
    # ----------------------------------------
    # NPN Transistor
    # Pin 1 (B) at left, Pin 2 (C) at top, Pin 3 (E) at bottom
    # ----------------------------------------
    
    "npn": ComponentDefinition(
        type="npn",
        symbol="Device:Q_NPN_BCE",
        name="NPN Transistor",
        default_value="2N2222",
        ref_prefix="Q",
        default_rotation=0,
        pins=[
            PinDefinition(1, "B", PinOffset(-2.54, 0)),
            PinDefinition(2, "C", PinOffset(2.54, -5.08)),  # Collector at top
            PinDefinition(3, "E", PinOffset(2.54, 5.08)),   # Emitter at bottom
        ],
        lib_symbol_def=NPN_SYMBOL,
    ),
    
    # ----------------------------------------
    # Power Symbols
    # ----------------------------------------
    
    "vcc": ComponentDefinition(
        type="vcc",
        symbol="power:VCC",
        name="VCC Power",
        default_value="VCC",
        ref_prefix="#PWR",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VCC", PinOffset(0, 0)),  # At center
        ],
        lib_symbol_def=VCC_SYMBOL,
    ),
    
    "gnd": ComponentDefinition(
        type="gnd",
        symbol="power:GND",
        name="GND Power",
        default_value="GND",
        ref_prefix="#PWR",
        default_rotation=0,
        pins=[
            PinDefinition(1, "GND", PinOffset(0, 0)),  # At center
        ],
        lib_symbol_def=GND_SYMBOL,
    ),
    
    # ----------------------------------------
    # ESP32
    # ----------------------------------------
    
    "esp32": ComponentDefinition(
        type="esp32",
        symbol="RF_Module:ESP32-WROOM-32",
        name="ESP32-WROOM-32",
        default_value="ESP32-WROOM-32",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            # Left side pins (at x=-15.24)
            PinDefinition(1, "GND", PinOffset(-15.24, 22.86)),
            PinDefinition(2, "3V3", PinOffset(-15.24, 20.32)),
            PinDefinition(3, "EN", PinOffset(-15.24, 17.78)),
            PinDefinition(4, "VP", PinOffset(-15.24, 15.24)),
            PinDefinition(5, "VN", PinOffset(-15.24, 12.7)),
            PinDefinition(6, "IO34", PinOffset(-15.24, 10.16)),
            PinDefinition(7, "IO35", PinOffset(-15.24, 7.62)),
            PinDefinition(8, "IO32", PinOffset(-15.24, 5.08)),
            PinDefinition(9, "IO33", PinOffset(-15.24, 2.54)),
            PinDefinition(10, "IO25", PinOffset(-15.24, 0)),
            PinDefinition(11, "IO26", PinOffset(-15.24, -2.54)),
            PinDefinition(12, "IO27", PinOffset(-15.24, -5.08)),
            PinDefinition(13, "IO14", PinOffset(-15.24, -7.62)),
            PinDefinition(14, "IO12", PinOffset(-15.24, -10.16)),
            PinDefinition(15, "GND2", PinOffset(-15.24, -12.7)),
            PinDefinition(16, "IO13", PinOffset(-15.24, -15.24)),
            PinDefinition(17, "SD2", PinOffset(-15.24, -17.78)),
            PinDefinition(18, "SD3", PinOffset(-15.24, -20.32)),
            PinDefinition(19, "CMD", PinOffset(-15.24, -22.86)),
            # Right side pins (at x=15.24)
            PinDefinition(20, "CLK", PinOffset(15.24, -22.86)),
            PinDefinition(21, "SD0", PinOffset(15.24, -20.32)),
            PinDefinition(22, "SD1", PinOffset(15.24, -17.78)),
            PinDefinition(23, "IO15", PinOffset(15.24, -15.24)),
            PinDefinition(24, "IO2", PinOffset(15.24, -12.7)),
            PinDefinition(25, "IO0", PinOffset(15.24, -10.16)),
            PinDefinition(26, "IO4", PinOffset(15.24, -7.62)),
            PinDefinition(27, "IO16", PinOffset(15.24, -5.08)),
            PinDefinition(28, "IO17", PinOffset(15.24, -2.54)),
            PinDefinition(29, "IO5", PinOffset(15.24, 0)),
            PinDefinition(30, "IO18", PinOffset(15.24, 2.54)),
            PinDefinition(31, "IO19", PinOffset(15.24, 5.08)),
            PinDefinition(32, "NC", PinOffset(15.24, 7.62)),
            PinDefinition(33, "IO21", PinOffset(15.24, 10.16)),
            PinDefinition(34, "RXD0", PinOffset(15.24, 12.7)),
            PinDefinition(35, "TXD0", PinOffset(15.24, 15.24)),
            PinDefinition(36, "IO22", PinOffset(15.24, 17.78)),
            PinDefinition(37, "IO23", PinOffset(15.24, 20.32)),
            PinDefinition(38, "GND3", PinOffset(15.24, 22.86)),
        ],
        lib_symbol_def=ESP32_SYMBOL,
    ),
    
    # ----------------------------------------
    # Arduino Uno
    # ----------------------------------------
    
    "arduino_uno": ComponentDefinition(
        type="arduino_uno",
        symbol="MCU_Module:Arduino_UNO_R3",
        name="Arduino UNO R3",
        default_value="Arduino_UNO_R3",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            # Left side - Power and Analog pins
            PinDefinition(1, "NC", PinOffset(-17.78, 25.4)),
            PinDefinition(2, "IOREF", PinOffset(-17.78, 22.86)),
            PinDefinition(3, "RESET", PinOffset(-17.78, 20.32)),
            PinDefinition(4, "3V3", PinOffset(-17.78, 17.78)),
            PinDefinition(5, "5V", PinOffset(-17.78, 15.24)),
            PinDefinition(6, "GND1", PinOffset(-17.78, 12.7)),
            PinDefinition(7, "GND2", PinOffset(-17.78, 10.16)),
            PinDefinition(8, "VIN", PinOffset(-17.78, 7.62)),
            PinDefinition(9, "A0", PinOffset(-17.78, 5.08)),
            PinDefinition(10, "A1", PinOffset(-17.78, 2.54)),
            PinDefinition(11, "A2", PinOffset(-17.78, 0)),
            PinDefinition(12, "A3", PinOffset(-17.78, -2.54)),
            PinDefinition(13, "A4/SDA", PinOffset(-17.78, -5.08)),
            PinDefinition(14, "A5/SCL", PinOffset(-17.78, -7.62)),
            # Right side - Digital pins
            PinDefinition(15, "D0/RX", PinOffset(17.78, -25.4)),
            PinDefinition(16, "D1/TX", PinOffset(17.78, -22.86)),
            PinDefinition(17, "D2", PinOffset(17.78, -20.32)),
            PinDefinition(18, "D3", PinOffset(17.78, -17.78)),
            PinDefinition(19, "D4", PinOffset(17.78, -15.24)),
            PinDefinition(20, "D5", PinOffset(17.78, -12.7)),
            PinDefinition(21, "D6", PinOffset(17.78, -10.16)),
            PinDefinition(22, "D7", PinOffset(17.78, -7.62)),
            PinDefinition(23, "D8", PinOffset(17.78, -5.08)),
            PinDefinition(24, "D9", PinOffset(17.78, -2.54)),
            PinDefinition(25, "D10/SS", PinOffset(17.78, 0)),
            PinDefinition(26, "D11/MOSI", PinOffset(17.78, 2.54)),
            PinDefinition(27, "D12/MISO", PinOffset(17.78, 5.08)),
            PinDefinition(28, "D13/SCK", PinOffset(17.78, 7.62)),
            PinDefinition(29, "GND3", PinOffset(17.78, 10.16)),
            PinDefinition(30, "AREF", PinOffset(17.78, 12.7)),
        ],
        lib_symbol_def=ARDUINO_UNO_SYMBOL,
    ),
    
    # ----------------------------------------
    # Connectors
    # ----------------------------------------
    
    "conn_2pin": ComponentDefinition(
        type="conn_2pin",
        symbol="Connector:Conn_01x02",
        name="2-Pin Connector",
        default_value="Conn",
        ref_prefix="J",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(-3.81, 0)),
            PinDefinition(2, "2", PinOffset(-3.81, -2.54)),
        ],
        lib_symbol_def=CONN_2PIN_SYMBOL,
    ),
    
    "conn_3pin": ComponentDefinition(
        type="conn_3pin",
        symbol="Connector:Conn_01x03",
        name="3-Pin Connector",
        default_value="Conn",
        ref_prefix="J",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(-3.81, 1.27)),
            PinDefinition(2, "2", PinOffset(-3.81, -1.27)),
            PinDefinition(3, "3", PinOffset(-3.81, -3.81)),
        ],
        lib_symbol_def=CONN_3PIN_SYMBOL,
    ),
    
    "conn_4pin": ComponentDefinition(
        type="conn_4pin",
        symbol="Connector:Conn_01x04",
        name="4-Pin Connector",
        default_value="Conn",
        ref_prefix="J",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(-3.81, 2.54)),
            PinDefinition(2, "2", PinOffset(-3.81, 0)),
            PinDefinition(3, "3", PinOffset(-3.81, -2.54)),
            PinDefinition(4, "4", PinOffset(-3.81, -5.08)),
        ],
        lib_symbol_def=CONN_4PIN_SYMBOL,
    ),
    
    # ----------------------------------------
    # HC-SR04 Ultrasonic Sensor
    # ----------------------------------------
    
    "hcsr04": ComponentDefinition(
        type="hcsr04",
        symbol="Sensor_Proximity:HC-SR04",
        name="HC-SR04 Ultrasonic Sensor",
        default_value="HC-SR04",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VCC", PinOffset(-10.16, 5.08)),
            PinDefinition(2, "TRIG", PinOffset(-10.16, 2.54)),
            PinDefinition(3, "ECHO", PinOffset(-10.16, 0)),
            PinDefinition(4, "GND", PinOffset(-10.16, -2.54)),
        ],
        lib_symbol_def=HCSR04_SYMBOL,
    ),
    
    # ----------------------------------------
    # Rotary Encoder with Switch
    # ----------------------------------------
    
    "rotary_encoder": ComponentDefinition(
        type="rotary_encoder",
        symbol="Device:RotaryEncoder_Switch",
        name="Rotary Encoder with Switch",
        default_value="EC11",
        ref_prefix="SW",
        default_rotation=0,
        pins=[
            PinDefinition(1, "A", PinOffset(-7.62, 2.54)),
            PinDefinition(2, "C", PinOffset(-7.62, 0)),      # Common/GND for encoder
            PinDefinition(3, "B", PinOffset(-7.62, -2.54)),
            PinDefinition(4, "S1", PinOffset(7.62, 2.54)),   # Switch pin 1
            PinDefinition(5, "S2", PinOffset(7.62, -2.54)),  # Switch pin 2
        ],
        lib_symbol_def=ROTARY_ENCODER_SYMBOL,
    ),
    
    # ----------------------------------------
    # Button/Switch
    # ----------------------------------------
    
    "button": ComponentDefinition(
        type="button",
        symbol="Switch:SW_Push",
        name="Push Button",
        default_value="SW",
        ref_prefix="SW",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(-5.08, 0)),
            PinDefinition(2, "2", PinOffset(5.08, 0)),
        ],
        lib_symbol_def=BUTTON_SYMBOL,
    ),
    
    # ============================================
    # NEW COMPONENTS FROM JAWI-OS LIBRARY
    # ============================================
    
    # DHT22 - Higher precision temp/humidity sensor
    "dht22": ComponentDefinition(
        type="dht22",
        symbol="Sensor:DHT22",
        name="DHT22 Sensor",
        default_value="DHT22",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VCC", PinOffset(-10.16, 3.81)),
            PinDefinition(2, "DATA", PinOffset(10.16, 0)),
            PinDefinition(3, "NC", PinOffset(10.16, -2.54)),
            PinDefinition(4, "GND", PinOffset(-10.16, -3.81)),
        ],
        lib_symbol_def=DHT22_SYMBOL,
    ),
    
    # BMP280 - Pressure/Temperature sensor (I2C)
    "bmp280": ComponentDefinition(
        type="bmp280",
        symbol="Sensor:BMP280",
        name="BMP280 Pressure Sensor",
        default_value="BMP280",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VCC", PinOffset(-10.16, 3.81)),
            PinDefinition(2, "GND", PinOffset(-10.16, -3.81)),
            PinDefinition(3, "SCL", PinOffset(10.16, 2.54)),
            PinDefinition(4, "SDA", PinOffset(10.16, -2.54)),
        ],
        lib_symbol_def=BMP280_SYMBOL,
    ),
    
    # PIR Motion Sensor
    "pir": ComponentDefinition(
        type="pir",
        symbol="Sensor:PIR",
        name="PIR Motion Sensor",
        default_value="HC-SR501",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VCC", PinOffset(-7.62, 2.54)),
            PinDefinition(2, "OUT", PinOffset(7.62, 0)),
            PinDefinition(3, "GND", PinOffset(-7.62, -2.54)),
        ],
        lib_symbol_def=PIR_SYMBOL,
    ),
    
    # LDR - Light Dependent Resistor
    "ldr": ComponentDefinition(
        type="ldr",
        symbol="Device:R_Photo",
        name="LDR Photoresistor",
        default_value="LDR",
        ref_prefix="R",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(0, -PIN_OFFSET)),
            PinDefinition(2, "2", PinOffset(0, PIN_OFFSET)),
        ],
        lib_symbol_def=LDR_SYMBOL,
    ),
    
    # OLED Display SSD1306 (I2C)
    "oled_ssd1306": ComponentDefinition(
        type="oled_ssd1306",
        symbol="Display:OLED_SSD1306",
        name="OLED Display 0.96",
        default_value="SSD1306",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            PinDefinition(1, "GND", PinOffset(-10.16, -3.81)),
            PinDefinition(2, "VCC", PinOffset(-10.16, 3.81)),
            PinDefinition(3, "SCL", PinOffset(10.16, 2.54)),
            PinDefinition(4, "SDA", PinOffset(10.16, -2.54)),
        ],
        lib_symbol_def=OLED_SSD1306_SYMBOL,
    ),
    
    # Servo Motor
    "servo": ComponentDefinition(
        type="servo",
        symbol="Motor:Servo",
        name="Servo Motor",
        default_value="SG90",
        ref_prefix="M",
        default_rotation=0,
        pins=[
            PinDefinition(1, "GND", PinOffset(-10.16, -2.54)),
            PinDefinition(2, "VCC", PinOffset(-10.16, 2.54)),
            PinDefinition(3, "SIG", PinOffset(10.16, 0)),
        ],
        lib_symbol_def=SERVO_SYMBOL,
    ),
    
    # Buzzer
    "buzzer": ComponentDefinition(
        type="buzzer",
        symbol="Device:Buzzer",
        name="Buzzer",
        default_value="Buzzer",
        ref_prefix="BZ",
        default_rotation=0,
        pins=[
            PinDefinition(1, "+", PinOffset(-7.62, 0)),
            PinDefinition(2, "-", PinOffset(7.62, 0)),
        ],
        lib_symbol_def=BUZZER_SYMBOL,
    ),
    
    # Relay 1 Channel Module
    "relay": ComponentDefinition(
        type="relay",
        symbol="Module:Relay_1CH",
        name="Relay 1 Channel",
        default_value="5V Relay",
        ref_prefix="K",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VCC", PinOffset(-10.16, 3.81)),
            PinDefinition(2, "GND", PinOffset(-10.16, -3.81)),
            PinDefinition(3, "IN", PinOffset(-10.16, 0)),
            PinDefinition(4, "COM", PinOffset(10.16, 2.54)),
            PinDefinition(5, "NO", PinOffset(10.16, 0)),
            PinDefinition(6, "NC", PinOffset(10.16, -2.54)),
        ],
        lib_symbol_def=RELAY_1CH_SYMBOL,
    ),
    
    # L298N Motor Driver
    "l298n": ComponentDefinition(
        type="l298n",
        symbol="Module:L298N",
        name="L298N Motor Driver",
        default_value="L298N",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VCC", PinOffset(-12.7, 12.7)),
            PinDefinition(2, "GND", PinOffset(-12.7, 10.16)),
            PinDefinition(3, "5V", PinOffset(-12.7, 7.62)),
            PinDefinition(4, "ENA", PinOffset(-12.7, 2.54)),
            PinDefinition(5, "IN1", PinOffset(-12.7, 0)),
            PinDefinition(6, "IN2", PinOffset(-12.7, -2.54)),
            PinDefinition(7, "IN3", PinOffset(-12.7, -5.08)),
            PinDefinition(8, "IN4", PinOffset(-12.7, -7.62)),
            PinDefinition(9, "ENB", PinOffset(-12.7, -10.16)),
            PinDefinition(10, "OUT1", PinOffset(12.7, 5.08)),
            PinDefinition(11, "OUT2", PinOffset(12.7, 2.54)),
            PinDefinition(12, "OUT3", PinOffset(12.7, -2.54)),
            PinDefinition(13, "OUT4", PinOffset(12.7, -5.08)),
        ],
        lib_symbol_def=L298N_SYMBOL,
    ),
    
    # Soil Moisture Sensor
    "soil_moisture": ComponentDefinition(
        type="soil_moisture",
        symbol="Sensor:SoilMoisture",
        name="Soil Moisture Sensor",
        default_value="Soil Sensor",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VCC", PinOffset(-10.16, 3.81)),
            PinDefinition(2, "GND", PinOffset(-10.16, -3.81)),
            PinDefinition(3, "DO", PinOffset(10.16, 2.54)),
            PinDefinition(4, "AO", PinOffset(10.16, -2.54)),
        ],
        lib_symbol_def=SOIL_MOISTURE_SYMBOL,
    ),
    
    # MQ-2 Gas Sensor
    "mq2": ComponentDefinition(
        type="mq2",
        symbol="Sensor:MQ-2",
        name="MQ-2 Gas Sensor",
        default_value="MQ-2",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            PinDefinition(1, "VCC", PinOffset(-10.16, 3.81)),
            PinDefinition(2, "GND", PinOffset(-10.16, -3.81)),
            PinDefinition(3, "DO", PinOffset(10.16, 2.54)),
            PinDefinition(4, "AO", PinOffset(10.16, -2.54)),
        ],
        lib_symbol_def=MQ2_SYMBOL,
    ),
    
    # Potentiometer
    "potentiometer": ComponentDefinition(
        type="potentiometer",
        symbol="Device:R_Potentiometer",
        name="Potentiometer",
        default_value="10k",
        ref_prefix="RV",
        default_rotation=0,
        pins=[
            PinDefinition(1, "1", PinOffset(0, -5.08)),
            PinDefinition(2, "2", PinOffset(5.08, 0)),
            PinDefinition(3, "3", PinOffset(0, 5.08)),
        ],
        lib_symbol_def=POTENTIOMETER_SYMBOL,
    ),
    
    # IR Receiver Module
    "ir_receiver": ComponentDefinition(
        type="ir_receiver",
        symbol="Sensor:IR_Receiver",
        name="IR Receiver",
        default_value="VS1838B",
        ref_prefix="U",
        default_rotation=0,
        pins=[
            PinDefinition(1, "OUT", PinOffset(10.16, 0)),
            PinDefinition(2, "GND", PinOffset(-10.16, -2.54)),
            PinDefinition(3, "VCC", PinOffset(-10.16, 2.54)),
        ],
        lib_symbol_def=IR_RECEIVER_SYMBOL,
    ),
}


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_component(name: str) -> ComponentDefinition | None:
    """Get component definition by name (case-insensitive)."""
    return COMPONENT_LIBRARY.get(name.lower())


def get_available_components() -> list[str]:
    """Get list of all available component types."""
    return list(COMPONENT_LIBRARY.keys())


def get_pin_position(
    component_x: float,
    component_y: float,
    comp_def: ComponentDefinition,
    pin_number: int | str,
    rotation: float = 0
) -> tuple[float, float]:
    """
    Calculate absolute pin position with rotation.
    
    Args:
        component_x, component_y: Component center position
        comp_def: Component definition
        pin_number: Pin number to get position for
        rotation: Rotation in degrees (counter-clockwise)
    
    Returns:
        (x, y) absolute position of the pin connection point
    """
    # Find pin definition
    pin_def = None
    for p in comp_def.pins:
        if p.number == pin_number or str(p.number) == str(pin_number):
            pin_def = p
            break
    
    if not pin_def:
        # Default to center if pin not found
        return (component_x, component_y)
    
    # Get base offset
    dx = pin_def.offset.dx
    dy = pin_def.offset.dy
    
    # Apply rotation (counter-clockwise)
    if rotation != 0:
        rad = math.radians(rotation)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)
        
        new_dx = dx * cos_r - dy * sin_r
        new_dy = dx * sin_r + dy * cos_r
        
        dx = new_dx
        dy = new_dy
    
    return (component_x + dx, component_y + dy)


def get_component_info_for_ai() -> str:
    """Get component information formatted for AI prompts."""
    lines = ["KOMPONEN TERSEDIA:"]
    
    for comp_type, comp_def in COMPONENT_LIBRARY.items():
        pin_info = ", ".join(f"pin{p.number}={p.name}" for p in comp_def.pins[:4])
        if len(comp_def.pins) > 4:
            pin_info += f", ... ({len(comp_def.pins)} pins total)"
        lines.append(f"- {comp_type}: {comp_def.name} [{pin_info}]")
    
    return "\n".join(lines)


# ============================================
# MODULE INFO
# ============================================

COMPONENT_COUNT = len(COMPONENT_LIBRARY)
