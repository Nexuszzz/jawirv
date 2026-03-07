"""
Simulasi output Gemini AI untuk test KiCad Generator V2.
Ini mensimulasikan apa yang akan dihasilkan Gemini ketika diminta membuat skematik.
"""

import os
import sys

current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from generator_v2 import SchematicGenerator
from library_v2 import get_available_components

def simulate_gemini_esp32_sensor_hub():
    """
    Simulasi output Gemini untuk request:
    "Buat skematik ESP32 dengan sensor DHT11, HC-SR04, dan rotary encoder"
    
    Ini adalah output yang Gemini AI akan hasilkan dalam format structured.
    """
    
    print("=" * 70)
    print("  SIMULASI GEMINI AI RESPONSE")
    print("=" * 70)
    
    # ===== SIMULATED GEMINI OUTPUT =====
    gemini_output = {
        "project": "esp32_sensor_hub",
        "description": "ESP32 dengan DHT11 (suhu/kelembaban), HC-SR04 (ultrasonic), dan Rotary Encoder",
        "explanation": """
Rangkaian ini mengintegrasikan ESP32 sebagai mikrokontroler utama dengan 3 sensor:

1. **DHT11** - Sensor suhu dan kelembaban digital
   - VCC terhubung ke 3.3V ESP32
   - DATA terhubung ke GPIO4 (dengan pull-up internal)
   - GND terhubung ke ground

2. **HC-SR04** - Sensor jarak ultrasonik
   - VCC membutuhkan 5V (dari sumber eksternal atau VIN)
   - TRIG terhubung ke GPIO5 (trigger pulse)
   - ECHO terhubung ke GPIO18 (echo return)
   - GND terhubung ke ground

3. **Rotary Encoder** - Input rotasi dengan push button
   - A terhubung ke GPIO19 (encoder channel A)
   - B terhubung ke GPIO21 (encoder channel B)  
   - C (common) terhubung ke GND
   - S1 (switch) terhubung ke GPIO22
   - S2 (switch) terhubung ke GND

Semua sensor menggunakan power supply 3.3V/5V dengan common ground.
""",
        "components": [
            {"type": "esp32", "reference": "U1", "value": "ESP32-WROOM-32", "x": 200, "y": 100},
            {"type": "dht11", "reference": "U2", "value": "DHT11", "x": 80, "y": 60},
            {"type": "hcsr04", "reference": "U3", "value": "HC-SR04", "x": 80, "y": 110},
            {"type": "rotary_encoder", "reference": "SW1", "value": "EC11", "x": 80, "y": 170},
        ],
        "wires": [
            # DHT11 connections
            {"from_comp": "U2", "from_pin": 1, "to_comp": "U1", "to_pin": 2},   # VCC -> 3V3
            {"from_comp": "U2", "from_pin": 2, "to_comp": "U1", "to_pin": 26},  # DATA -> IO4
            {"from_comp": "U2", "from_pin": 4, "to_comp": "U1", "to_pin": 1},   # GND -> GND
            
            # HC-SR04 connections (VCC/GND akan dihandle dengan power symbols)
            {"from_comp": "U3", "from_pin": 2, "to_comp": "U1", "to_pin": 29},  # TRIG -> IO5
            {"from_comp": "U3", "from_pin": 3, "to_comp": "U1", "to_pin": 30},  # ECHO -> IO18
            
            # Rotary Encoder connections
            {"from_comp": "SW1", "from_pin": 1, "to_comp": "U1", "to_pin": 31},  # A -> IO19
            {"from_comp": "SW1", "from_pin": 3, "to_comp": "U1", "to_pin": 33},  # B -> IO21
            {"from_comp": "SW1", "from_pin": 4, "to_comp": "U1", "to_pin": 36},  # S1 -> IO22
        ]
    }
    
    print(f"\n📝 Project: {gemini_output['project']}")
    print(f"📄 Description: {gemini_output['description']}")
    print(f"\n📋 Explanation:\n{gemini_output['explanation']}")
    
    # ===== CONVERT TO SCHEMATIC =====
    print("\n" + "=" * 70)
    print("  GENERATING SCHEMATIC")
    print("=" * 70)
    
    gen = SchematicGenerator()
    
    # Add components
    comp_map = {}
    for comp in gemini_output["components"]:
        placed = gen.add_component(
            component_type=comp["type"],
            x=comp["x"],
            y=comp["y"],
            value=comp["value"],
            component_id=comp["reference"]
        )
        placed.reference = comp["reference"]  # Override reference
        comp_map[comp["reference"]] = placed
        print(f"  Added: {placed.reference} ({comp['type']}) at ({comp['x']}, {comp['y']})")
    
    # Add power symbols
    vcc = gen.add_component("vcc", 50, 40)
    gnd = gen.add_component("gnd", 50, 200)
    comp_map["VCC"] = vcc
    comp_map["GND"] = gnd
    print(f"  Added: VCC at (50, 40)")
    print(f"  Added: GND at (50, 200)")
    
    # Add wires
    print("\n  Wiring:")
    for wire in gemini_output["wires"]:
        from_comp = comp_map.get(wire["from_comp"])
        to_comp = comp_map.get(wire["to_comp"])
        if from_comp and to_comp:
            gen.add_wire_between_pins(from_comp, wire["from_pin"], to_comp, wire["to_pin"])
            print(f"    {wire['from_comp']}.{wire['from_pin']} -> {wire['to_comp']}.{wire['to_pin']}")
    
    # Add additional power connections
    gen.add_wire_between_pins(comp_map["U3"], 1, vcc, 1)  # HC-SR04 VCC
    gen.add_wire_between_pins(comp_map["U3"], 4, gnd, 1)  # HC-SR04 GND
    gen.add_wire_between_pins(comp_map["SW1"], 2, gnd, 1)  # Rotary C -> GND
    gen.add_wire_between_pins(comp_map["SW1"], 5, gnd, 1)  # Rotary S2 -> GND
    print("    U3.VCC -> VCC, U3.GND -> GND")
    print("    SW1.C -> GND, SW1.S2 -> GND")
    
    # Generate schematic
    content = gen.generate()
    
    # Save to file
    output_dir = "D:/sijawir/KiCad_Projects/gemini_test_output"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "esp32_sensor_hub.kicad_sch")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"\n" + "=" * 70)
    print("  HASIL")
    print("=" * 70)
    print(f"\n✅ Schematic berhasil dibuat!")
    print(f"   📁 File: {output_path}")
    print(f"   📊 Komponen: {len(gen.components)}")
    print(f"   🔌 Wire segments: {len(gen.wires)}")
    
    # Verification
    print("\n📋 Verifikasi:")
    checks = [
        ("ESP32 symbol", "RF_Module:ESP32-WROOM-32" in content),
        ("DHT11 symbol", "Sensor:DHT11" in content),
        ("HC-SR04 symbol", "Sensor_Proximity:HC-SR04" in content),
        ("Rotary Encoder symbol", "Device:RotaryEncoder_Switch" in content),
        ("U1 reference", 'Reference" "U1"' in content),
        ("U2 reference", 'Reference" "U2"' in content),
        ("U3 reference", 'Reference" "U3"' in content),
        ("SW1 reference", 'Reference" "SW1"' in content),
        ("VCC symbol", "power:VCC" in content),
        ("GND symbol", "power:GND" in content),
        ("Wire segments exist", "(wire" in content),
        ("Symbol instances", "(symbol_instances" in content),
    ]
    
    all_pass = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"   {status} {name}")
        if not passed:
            all_pass = False
    
    if all_pass:
        print(f"\n🎉 SEMUA VERIFIKASI BERHASIL!")
        print(f"\n🚀 Silakan buka file di KiCad untuk melihat hasilnya:")
        print(f"   {output_path}")
        
        # Try to open
        try:
            import subprocess
            subprocess.Popen(["explorer", "/select,", output_path], shell=True)
        except:
            pass
    
    return all_pass, output_path


def list_available_components():
    """List semua komponen yang tersedia untuk Gemini."""
    print("\n" + "=" * 70)
    print("  KOMPONEN TERSEDIA UNTUK GEMINI AI")
    print("=" * 70)
    
    components = get_available_components()
    print(f"\nTotal: {len(components)} komponen\n")
    
    for comp in components:
        from library_v2 import get_component
        comp_def = get_component(comp)
        if comp_def:
            pins = ", ".join(f"{p.number}:{p.name}" for p in comp_def.pins[:5])
            if len(comp_def.pins) > 5:
                pins += f"... ({len(comp_def.pins)} total)"
            print(f"  • {comp}: {comp_def.name}")
            print(f"    Pins: {pins}")


if __name__ == "__main__":
    list_available_components()
    print("\n")
    success, path = simulate_gemini_esp32_sensor_hub()
    sys.exit(0 if success else 1)
