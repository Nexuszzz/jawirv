"""
Test KiCad Designer dengan Gemini AI.
Menguji integrasi generator V2 dengan AI.
Menggunakan API Key Rotator untuk handle rate limit.
"""

import os
import sys
import asyncio
import logging
import time

# Setup path - direct imports to avoid dependency issues
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

# Add backend to path for api_rotator
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, backend_dir)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_gemini_kicad")

# Environment setup
try:
    from dotenv import load_dotenv
    # Try multiple paths for .env
    env_paths = [
        os.path.join(backend_dir, '.env'),  # backend/.env
        os.path.join(os.path.dirname(backend_dir), '.env'),  # project root
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            print(f"Loading .env from: {env_path}")
            load_dotenv(env_path)
            break
except ImportError:
    pass


class GeminiWithRotation:
    """Wrapper untuk ChatGoogleGenerativeAI dengan API key rotation."""
    
    def __init__(self, api_keys: list[str], model: str = "gemini-3-flash-preview"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        self.api_keys = api_keys
        self.model = model
        self.current_index = 0
        self.rate_limited_keys: dict[str, float] = {}  # key -> cooldown_until timestamp
        self.max_retries = len(api_keys) * 2  # Allow cycling through all keys twice
        
    def get_next_key(self) -> str:
        """Get next available API key, skipping rate-limited ones."""
        now = time.time()
        attempts = 0
        
        while attempts < len(self.api_keys):
            key = self.api_keys[self.current_index]
            
            # Check if key is in cooldown
            if key in self.rate_limited_keys:
                if now < self.rate_limited_keys[key]:
                    # Still in cooldown
                    self.current_index = (self.current_index + 1) % len(self.api_keys)
                    attempts += 1
                    continue
                else:
                    # Cooldown expired
                    del self.rate_limited_keys[key]
                    print(f"✅ Key #{self.current_index + 1} keluar dari cooldown")
            
            # Rotate for next call
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            return key
        
        # All keys rate-limited, return the one with shortest cooldown
        if self.rate_limited_keys:
            min_key = min(self.rate_limited_keys, key=self.rate_limited_keys.get)
            wait_time = self.rate_limited_keys[min_key] - now
            if wait_time > 0:
                print(f"⏳ Semua key rate-limited. Menunggu {wait_time:.0f}s...")
                time.sleep(wait_time + 1)
            return min_key
        
        raise RuntimeError("No API keys available")
    
    def mark_rate_limited(self, key: str, cooldown_seconds: int = 60):
        """Mark key as rate-limited."""
        self.rate_limited_keys[key] = time.time() + cooldown_seconds
        key_index = self.api_keys.index(key) + 1
        print(f"🔒 Key #{key_index} rate-limited, cooldown {cooldown_seconds}s. Mencoba key lain...")
    
    def create_llm(self, api_key: str):
        """Create LLM instance with specific API key."""
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=api_key,
            temperature=0.3,
            convert_system_message_to_human=True,
        )
    
    async def invoke_with_rotation(self, messages, output_schema, max_retries: int = None):
        """Invoke AI dengan automatic key rotation on rate limit."""
        from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
        
        max_retries = max_retries or self.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            api_key = self.get_next_key()
            key_num = self.api_keys.index(api_key) + 1
            
            print(f"🔑 Mencoba key #{key_num} (attempt {attempt + 1}/{max_retries})...")
            
            try:
                llm = self.create_llm(api_key)
                structured_llm = llm.with_structured_output(output_schema)
                result = await structured_llm.ainvoke(messages)
                print(f"✅ Sukses dengan key #{key_num}")
                return result
                
            except ChatGoogleGenerativeAIError as e:
                error_str = str(e)
                last_error = e
                
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    # Extract retry time if available
                    import re
                    retry_match = re.search(r'retry.*?(\d+\.?\d*)s', error_str.lower())
                    cooldown = int(float(retry_match.group(1))) + 5 if retry_match else 60
                    
                    self.mark_rate_limited(api_key, cooldown)
                    continue
                elif "API_KEY_INVALID" in error_str or "PERMISSION_DENIED" in error_str:
                    print(f"❌ Key #{key_num} tidak valid, skip permanent")
                    self.rate_limited_keys[api_key] = float('inf')  # Permanent disable
                    continue
                else:
                    raise
            except Exception as e:
                last_error = e
                print(f"⚠️ Error dengan key #{key_num}: {e}")
                continue
        
        raise RuntimeError(f"Gagal setelah {max_retries} percobaan. Last error: {last_error}")


async def test_gemini_kicad_design():
    """Test Gemini AI untuk desain KiCad."""
    
    from pydantic import BaseModel, Field
    from typing import Optional
    from langchain_core.messages import HumanMessage, SystemMessage
    
    # Import KiCad tools (V2) - direct imports
    from library_v2 import get_component_info_for_ai
    from generator_bridge import save_schematic_v2 as save_schematic, open_in_kicad
    from schemas import Position, PinReference, ComponentPlacement, WireConnection, SchematicPlan
    
    # Schema output dari AI
    class KicadDesignOutput(BaseModel):
        """Schema output dari AI untuk desain KiCad."""
        
        project: str = Field(description="Nama project (untuk filename, tanpa spasi)")
        description: Optional[str] = Field(default=None, description="Deskripsi rangkaian")
        components: list[dict] = Field(
            default=[],
            description="List komponen: [{type, reference, value, position: {x, y}, rotation}]"
        )
        wires: list[dict] = Field(
            default=[],
            description="List koneksi: [{from: {component, pin}, to: {component, pin}}]"
        )
        explanation: str = Field(description="Penjelasan rangkaian untuk user")
    
    # Get API keys - support multiple keys for rotation
    api_keys = []
    
    # Try GOOGLE_API_KEYS first (comma-separated)
    google_api_keys = os.getenv("GOOGLE_API_KEYS", "")
    if google_api_keys:
        api_keys = [k.strip() for k in google_api_keys.split(",") if k.strip()]
    
    # Fallback to single key
    if not api_keys:
        single_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if single_key:
            api_keys = [single_key]
    
    if not api_keys:
        print("❌ GOOGLE_API_KEYS, GEMINI_API_KEY, atau GOOGLE_API_KEY tidak ditemukan!")
        print("   Set environment variable atau tambahkan ke .env file")
        return False
    
    print(f"✅ {len(api_keys)} API Key(s) ditemukan, rotation enabled!")
    for i, key in enumerate(api_keys):
        print(f"   Key #{i+1}: {key[:10]}...{key[-4:]}")
    
    # Setup LLM with rotation
    gemini = GeminiWithRotation(api_keys, model="gemini-3-flash-preview")
    
    # Get component info
    component_info = get_component_info_for_ai()
    
    # ENHANCED System prompt - lebih robust dan sesuai kaidah elektronika
    system_prompt = f"""Kamu adalah JAWIR OS - Electronic Architect, ahli desain rangkaian elektronika profesional.

TUGAS UTAMA: Desain skematik KiCad yang BENAR secara elektrikal dan sesuai kaidah.

═══════════════════════════════════════════════════════════════════
LANGKAH WAJIB SEBELUM DESAIN (Chain of Thought):
═══════════════════════════════════════════════════════════════════
1. ANALISIS permintaan user - apa tujuan rangkaian?
2. IDENTIFIKASI komponen yang dibutuhkan
3. TENTUKAN koneksi berdasarkan datasheet/spesifikasi
4. VALIDASI setiap koneksi sebelum output

═══════════════════════════════════════════════════════════════════
KOMPONEN TERSEDIA & PIN MAPPING (WAJIB IKUTI):
═══════════════════════════════════════════════════════════════════

📦 PASSIVE COMPONENTS:
• resistor: pin1=terminal1, pin2=terminal2 (vertical, 2-pin)
• capacitor: pin1=terminal1, pin2=terminal2 (vertical, 2-pin)
• led: pin1=K(Cathode/-), pin2=A(Anode/+) (horizontal)

📦 SENSORS:
• dht11: pin1=VCC(3.3-5V), pin2=DATA, pin3=NC, pin4=GND
• hcsr04: pin1=VCC(5V), pin2=TRIG, pin3=ECHO, pin4=GND

📦 INPUT DEVICES:
• rotary_encoder: pin1=A, pin2=C(Common/GND), pin3=B, pin4=S1(switch), pin5=S2(switch)
• button: pin1=terminal1, pin2=terminal2

📦 TRANSISTORS:
• npn: pin1=B(Base), pin2=C(Collector), pin3=E(Emitter)

📦 MICROCONTROLLERS:
• esp32: 38 pins total
  - Power: pin1=GND, pin2=3V3, pin3=EN
  - ADC: pin4=VP(GPIO36), pin5=VN(GPIO39), pin6=IO34, pin7=IO35
  - GPIO: pin8=IO32, pin9=IO33, pin10=IO25, pin11=IO26, pin12=IO27
  - SPI/GPIO: pin13=IO14, pin14=IO12, pin16=IO13
  - Serial: pin34=RXD0, pin35=TXD0
  - I2C: pin36=IO22(SCL), pin37=IO23(SDA)

📦 POWER:
• vcc: pin1=VCC (sumber +3.3V atau +5V)
• gnd: pin1=GND (ground/0V)

📦 CONNECTORS:
• conn_2pin: pin1, pin2
• conn_3pin: pin1, pin2, pin3
• conn_4pin: pin1, pin2, pin3, pin4

═══════════════════════════════════════════════════════════════════
KAIDAH ELEKTRONIKA WAJIB:
═══════════════════════════════════════════════════════════════════

🔴 POWER SUPPLY:
• SETIAP IC/sensor WAJIB punya koneksi VCC dan GND
• ESP32 menggunakan 3.3V logic (pin2=3V3)
• DHT11 bisa 3.3-5V, HC-SR04 butuh 5V (level shifter optional)

🔴 LED CIRCUIT:
• LED WAJIB pakai current-limiting resistor (220-1K ohm)
• Urutan: GPIO → Resistor → LED(Anode) → LED(Cathode) → GND
• Atau: VCC → Resistor → LED(Anode) → LED(Cathode) → GPIO (active low)

🔴 SENSOR DIGITAL:
• DHT11: VCC→pin1, DATA→pin2 (ke GPIO), NC→floating atau GND, GND→pin4
• HC-SR04: VCC→pin1(5V), TRIG→pin2(GPIO output), ECHO→pin3(GPIO input), GND→pin4
• Data pin sensor ke GPIO yang support digital read

🔴 ROTARY ENCODER:
• pin1(A) → GPIO dengan interrupt support
• pin2(C/Common) → GND
• pin3(B) → GPIO dengan interrupt support
• pin4(S1), pin5(S2) → untuk switch, salah satu ke GPIO, satu ke GND

🔴 BUTTON/SWITCH:
• Selalu pakai pull-up atau pull-down resistor (internal ESP32 bisa dipakai)
• Config: GPIO → Button → GND (dengan internal pull-up)

═══════════════════════════════════════════════════════════════════
ATURAN POSISI & LAYOUT:
═══════════════════════════════════════════════════════════════════
• Canvas center = (127, 100) mm
• MCU (ESP32) di tengah-kanan, butuh ~60x80mm area
• Sensors di kiri MCU
• Power symbols (VCC/GND) di atas/bawah
• Spacing minimum 25-30mm antar komponen

═══════════════════════════════════════════════════════════════════
FORMAT WIRING:
═══════════════════════════════════════════════════════════════════
Wire format: {{from: {{component: "REF", pin: NUMBER}}, to: {{component: "REF", pin: NUMBER}}}}

Untuk power nets, gunakan:
- VCC: {{component: "VCC", pin: 1}} atau {{component: "PWR1", pin: 1}}
- GND: {{component: "GND", pin: 1}} atau {{component: "PWR2", pin: 1}}

═══════════════════════════════════════════════════════════════════
CONTOH LENGKAP - ESP32 + DHT11 + LED (CORRECT):
═══════════════════════════════════════════════════════════════════

REQUEST: "Buat ESP32 dengan DHT11 dan LED indicator"

REASONING:
1. ESP32 sebagai MCU utama
2. DHT11 untuk sensor suhu/kelembaban - butuh VCC, DATA, GND
3. LED untuk indikator - WAJIB pakai resistor
4. Power: VCC dan GND untuk semua komponen

COMPONENTS:
[
  {{"type": "esp32", "reference": "U1", "value": "ESP32-WROOM-32", "position": {{"x": 180, "y": 100}}}},
  {{"type": "dht11", "reference": "U2", "value": "DHT11", "position": {{"x": 80, "y": 70}}}},
  {{"type": "resistor", "reference": "R1", "value": "330", "position": {{"x": 80, "y": 120}}}},
  {{"type": "led", "reference": "D1", "value": "Green", "position": {{"x": 80, "y": 140}}, "rotation": 90}},
  {{"type": "vcc", "reference": "VCC", "value": "3.3V", "position": {{"x": 130, "y": 30}}}},
  {{"type": "gnd", "reference": "GND", "value": "GND", "position": {{"x": 130, "y": 180}}}}
]

WIRES:
[
  // ESP32 Power
  {{"from": {{"component": "U1", "pin": 2}}, "to": {{"component": "VCC", "pin": 1}}}},
  {{"from": {{"component": "U1", "pin": 1}}, "to": {{"component": "GND", "pin": 1}}}},
  // DHT11 connections
  {{"from": {{"component": "U2", "pin": 1}}, "to": {{"component": "VCC", "pin": 1}}}},
  {{"from": {{"component": "U2", "pin": 2}}, "to": {{"component": "U1", "pin": 11}}}},  // DATA to IO26
  {{"from": {{"component": "U2", "pin": 4}}, "to": {{"component": "GND", "pin": 1}}}},
  // LED with resistor (CORRECT WAY)
  {{"from": {{"component": "U1", "pin": 12}}, "to": {{"component": "R1", "pin": 1}}}},  // IO27 to Resistor
  {{"from": {{"component": "R1", "pin": 2}}, "to": {{"component": "D1", "pin": 2}}}},   // Resistor to LED Anode
  {{"from": {{"component": "D1", "pin": 1}}, "to": {{"component": "GND", "pin": 1}}}}   // LED Cathode to GND
]

═══════════════════════════════════════════════════════════════════
VALIDATION CHECKLIST (WAJIB SEBELUM OUTPUT):
═══════════════════════════════════════════════════════════════════
☑ Semua IC/sensor punya VCC dan GND?
☑ LED punya resistor series?
☑ Pin number sesuai dengan mapping di atas?
☑ Tidak ada pin floating yang seharusnya terhubung?
☑ GPIO assignments tidak conflict?
☑ Posisi komponen tidak overlap?

═══════════════════════════════════════════════════════════════════
OUTPUT REQUIREMENTS:
═══════════════════════════════════════════════════════════════════
1. project: nama project (lowercase, underscore, tanpa spasi)
2. description: deskripsi singkat rangkaian
3. components: array komponen dengan type, reference, value, position
4. wires: array koneksi dengan from/to pin references
5. explanation: penjelasan detail termasuk:
   - Fungsi setiap komponen
   - Alasan pemilihan GPIO
   - Cara kerja rangkaian

BERIKAN EXPLANATION YANG EDUCATIONAL untuk membantu user memahami rangkaian!"""

    # User request - test dengan rangkaian yang lebih kompleks
    user_query = "Buat skematik ESP32 dengan 2 LED (merah dan hijau) sebagai indikator, masing-masing dengan resistor pembatas arus. Tambahkan button untuk input dan DHT11 untuk sensor suhu."
    
    print("=" * 60)
    print("  TEST GEMINI AI KICAD DESIGNER (Enhanced Prompt)")
    print("=" * 60)
    print(f"\n📝 Request: {user_query}\n")
    print("⏳ Mengirim ke Gemini AI...")
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Desain skematik: {user_query}"),
    ]
    
    try:
        # Invoke AI with rotation
        design: KicadDesignOutput = await gemini.invoke_with_rotation(
            messages, 
            KicadDesignOutput,
            max_retries=len(api_keys) * 2  # Try each key twice
        )
        
        print(f"\n✅ AI Response:")
        print(f"   Project: {design.project}")
        print(f"   Components: {len(design.components)}")
        print(f"   Wires: {len(design.wires)}")
        print(f"\n📋 Explanation: {design.explanation}")
        
        # Print components
        print(f"\n📦 Components:")
        for comp in design.components:
            print(f"   - {comp.get('reference', '?')}: {comp.get('type', '?')} at ({comp.get('position', {}).get('x', 0)}, {comp.get('position', {}).get('y', 0)})")
        
        # Print wires
        print(f"\n🔌 Wires:")
        for wire in design.wires[:10]:  # Show first 10
            from_ref = wire.get('from', {})
            to_ref = wire.get('to', {})
            print(f"   - {from_ref.get('component', '?')}.{from_ref.get('pin', '?')} → {to_ref.get('component', '?')}.{to_ref.get('pin', '?')}")
        if len(design.wires) > 10:
            print(f"   ... and {len(design.wires) - 10} more")
        
        # Convert to SchematicPlan
        components = []
        for comp in design.components:
            components.append(ComponentPlacement(
                type=comp["type"],
                reference=comp["reference"],
                value=comp.get("value"),
                position=Position(
                    x=comp["position"]["x"],
                    y=comp["position"]["y"]
                ),
                rotation=comp.get("rotation"),
            ))
        
        wires = []
        for wire in design.wires:
            from_ref = wire["from"]
            to_ref = wire["to"]
            
            wires.append(WireConnection(
                **{"from": PinReference(
                    component=from_ref["component"],
                    pin=from_ref["pin"]
                )},
                to=PinReference(
                    component=to_ref["component"],
                    pin=to_ref["pin"]
                ),
            ))
        
        plan = SchematicPlan(
            project=design.project,
            description=design.description,
            components=components,
            wires=wires,
        )
        
        # Generate schematic using V2 generator
        print(f"\n⚙️ Generating schematic using V2 generator...")
        result = save_schematic(plan)
        
        if result.success:
            print(f"\n✅ SUCCESS!")
            print(f"   📁 File: {result.file_path}")
            print(f"   📊 Components: {result.component_count}")
            print(f"   🔌 Wires: {result.wire_count}")
            
            # Open in KiCad
            print(f"\n🚀 Opening in KiCad...")
            open_in_kicad(result.file_path)
            
            return True
        else:
            print(f"\n❌ FAILED: {result.message}")
            if result.errors:
                for err in result.errors:
                    print(f"   - {err}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_gemini_kicad_design())
    sys.exit(0 if result else 1)
