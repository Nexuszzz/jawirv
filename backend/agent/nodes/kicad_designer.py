"""
JAWIR OS - KiCad Designer Node
LangGraph node for designing electronic schematics using Gemini AI.

This node handles the KiCad design workflow:
1. Receive user request for schematic
2. Use Gemini to generate SchematicPlan
3. Generate .kicad_sch file
4. Return result to user
"""

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from agent.state import JawirState, AgentThinking
from agent.api_rotator import get_api_key, mark_key_rate_limited

# Import KiCad tools
from tools.kicad import (
    SchematicPlan,
    ComponentPlacement,
    WireConnection,
    PinReference,
    Position,
    GenerationResult,
    save_schematic,
    open_in_kicad,
    get_component_info_for_ai,
    get_template_info_for_ai,
    get_template,
    get_available_templates,
)

logger = logging.getLogger("jawir.agent.kicad_designer")


# ============================================
# Pydantic Schema for KiCad Design Output
# ============================================

class KicadDesignOutput(BaseModel):
    """Schema output dari AI untuk desain KiCad."""
    
    project: str = Field(
        description="Nama project (untuk filename, tanpa spasi)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Deskripsi rangkaian"
    )
    use_template: Optional[str] = Field(
        default=None,
        description="Nama template jika menggunakan template yang sudah ada"
    )
    components: list[dict] = Field(
        default=[],
        description="List komponen: [{type, reference, value, position: {x, y}, rotation}]"
    )
    wires: list[dict] = Field(
        default=[],
        description="List koneksi: [{from: {component, pin}, to: {component, pin}}]"
    )
    labels: list[dict] = Field(
        default=[],
        description="List label power: [{name, x, y}]"
    )
    open_kicad: bool = Field(
        default=False,
        description="Buka KiCad setelah generate"
    )
    explanation: str = Field(
        description="Penjelasan rangkaian untuk user"
    )


# ============================================
# KiCad Designer Prompt
# ============================================

KICAD_DESIGNER_PROMPT = """Kamu adalah JAWIR OS - Electronic Architect, ahli desain rangkaian elektronika.

TUGAS: Desain skematik berdasarkan permintaan user.

{component_info}

{template_info}

ATURAN DESAIN:
1. Posisi komponen dalam mm, center canvas = (127, 100)
2. Spacing antar komponen = 25-30mm
3. MCU (Arduino, ESP32) butuh ruang besar (~50mm)
4. Gunakan rotation 0 (vertical) atau 90 (horizontal) untuk komponen 2-pin
5. SETIAP PIN HARUS TERHUBUNG - tidak boleh ada pin floating!

ATURAN WIRING:
1. Wire menggunakan referensi semantik: {{component: "R1", pin: 1}}
2. LED: cathode (pin 1) → GND, anode (pin 2) → resistor
3. Capacitor: pin 1 → power, pin 2 → GND
4. Transistor NPN: B=input, C=load, E=GND
5. Power net: gunakan "VCC" atau "GND" sebagai component reference

CONTOH LED DENGAN RESISTOR:
components: [
  {{type: "resistor", reference: "R1", value: "330", position: {{x: 127, y: 80}}}},
  {{type: "led", reference: "D1", value: "Red", position: {{x: 127, y: 100}}, rotation: 90}}
]
wires: [
  {{from: {{component: "VCC", pin: 1}}, to: {{component: "R1", pin: 1}}}},
  {{from: {{component: "R1", pin: 2}}, to: {{component: "D1", pin: 2}}}},
  {{from: {{component: "D1", pin: 1}}, to: {{component: "GND", pin: 1}}}}
]

JIKA MENGGUNAKAN TEMPLATE:
- Set use_template = nama_template
- Biarkan components dan wires kosong (akan diambil dari template)

SELALU berikan explanation yang membantu user memahami rangkaian."""


def get_kicad_llm():
    """Get Gemini LLM with structured output for KiCad design."""
    api_key = get_api_key()
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        temperature=0.3,  # Slightly higher for creative design
        convert_system_message_to_human=True,
    )
    return llm.with_structured_output(KicadDesignOutput), api_key


def parse_design_to_plan(design: KicadDesignOutput) -> SchematicPlan:
    """Convert AI design output to SchematicPlan."""
    
    # Parse components
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
    
    # Parse wires
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
    
    # Parse labels
    labels = None
    if design.labels:
        from tools.kicad import PowerLabel
        labels = [
            PowerLabel(name=l["name"], x=l["x"], y=l["y"])
            for l in design.labels
        ]
    
    return SchematicPlan(
        project=design.project,
        description=design.description,
        components=components,
        wires=wires,
        labels=labels,
        open_kicad=design.open_kicad,
    )


async def kicad_designer_node(state: JawirState) -> dict[str, Any]:
    """
    KiCad Designer Node: Design and generate electronic schematics.
    
    Flow:
    1. Get user query about schematic
    2. Check if it's a template request
    3. Use Gemini to design the schematic
    4. Generate .kicad_sch file
    5. Return result
    """
    query = state['user_query']
    logger.info(f"🔌 KiCad Designer processing: {query[:50]}...")
    
    # Check for template keywords
    available_templates = get_available_templates()
    template_match = None
    
    for template_name in available_templates:
        if template_name.replace("_", " ") in query.lower():
            template_match = template_name
            break
    
    # Use template directly if matched
    if template_match:
        logger.info(f"📋 Using template: {template_match}")
        plan = get_template(template_match)
        
        if plan:
            result = save_schematic(plan)
            
            if result.success:
                response_msg = f"""✅ Skematik **{result.project_name}** berhasil dibuat!

📁 File: `{result.file_path}`
📊 Komponen: {result.component_count}
🔌 Koneksi: {result.wire_count}

Template yang digunakan: **{template_match}**

{plan.description or ''}"""
                
                # Try to open KiCad
                if plan.open_kicad:
                    open_in_kicad(result.file_path)
                
                return {
                    "understanding": f"Membuat skematik dari template {template_match}",
                    "plan": [],
                    "tools_needed": [],
                    "current_step": 0,
                    "pending_tools": [],
                    "status": "done",
                    "final_response": response_msg,
                    "sources_used": [],
                    "messages": state.get("messages", []) + [
                        HumanMessage(content=query),
                        AIMessage(content=response_msg),
                    ],
                }
    
    # ============================================
    # Use Gemini for custom design
    # ============================================
    try:
        structured_llm, current_key = get_kicad_llm()
        
        # Build prompt with component and template info
        component_info = get_component_info_for_ai()
        template_info = get_template_info_for_ai()
        
        system_prompt = KICAD_DESIGNER_PROMPT.format(
            component_info=component_info,
            template_info=template_info,
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Desain skematik: {query}"),
        ]
        
        # Invoke AI
        design: KicadDesignOutput = await structured_llm.ainvoke(messages)
        
        logger.info(f"✅ AI Design: project={design.project}, components={len(design.components)}")
        
        # Check if AI wants to use template
        if design.use_template:
            plan = get_template(design.use_template)
            if plan:
                # Override open_kicad from AI suggestion
                plan.open_kicad = design.open_kicad
            else:
                # Template not found, use AI design
                plan = parse_design_to_plan(design)
        else:
            # Use AI design
            plan = parse_design_to_plan(design)
        
        # Generate schematic file
        result = save_schematic(plan)
        
        if result.success:
            response_msg = f"""✅ Skematik **{result.project_name}** berhasil dibuat!

📁 File: `{result.file_path}`
📊 Komponen: {result.component_count}
🔌 Koneksi: {result.wire_count}

**Penjelasan:**
{design.explanation}

{f'💡 Buka file di KiCad untuk melihat hasilnya.' if not design.open_kicad else '🚀 KiCad sedang dibuka...'}"""
            
            # Try to open KiCad if requested
            if design.open_kicad:
                opened = open_in_kicad(result.file_path)
                if not opened:
                    response_msg += "\n\n⚠️ KiCad tidak ditemukan. Silakan buka file secara manual."
            
            # Update thinking
            thinking = AgentThinking(
                thought=f"Desain skematik {result.project_name} selesai",
                evaluation=f"Berhasil membuat {result.component_count} komponen dengan {result.wire_count} koneksi",
                memory=f"File disimpan di {result.file_path}",
                next_goal=None,
            )
            
            return {
                "understanding": design.description or f"Membuat skematik {design.project}",
                "plan": [],
                "tools_needed": [],
                "current_step": 0,
                "pending_tools": [],
                "status": "done",
                "final_response": response_msg,
                "sources_used": [],
                "current_thinking": thinking,
                "thinking_history": state.get("thinking_history", []) + [thinking],
                "messages": state.get("messages", []) + [
                    HumanMessage(content=query),
                    AIMessage(content=response_msg),
                ],
            }
        else:
            # Generation failed
            error_msg = f"""❌ Gagal membuat skematik: {result.message}

Errors: {result.errors}

Silakan coba lagi dengan deskripsi yang lebih spesifik."""
            
            return {
                "understanding": "Gagal membuat skematik",
                "plan": [],
                "tools_needed": [],
                "current_step": 0,
                "pending_tools": [],
                "status": "error",
                "final_response": error_msg,
                "sources_used": [],
                "errors": state.get("errors", []) + [result.message],
                "messages": state.get("messages", []) + [
                    HumanMessage(content=query),
                    AIMessage(content=error_msg),
                ],
            }
            
    except Exception as e:
        logger.error(f"❌ KiCad Designer error: {e}")
        
        error_msg = f"""❌ Error saat mendesain skematik: {str(e)}

Silakan coba lagi atau gunakan template yang tersedia:
{get_template_info_for_ai()}"""
        
        return {
            "understanding": "Error pada KiCad Designer",
            "plan": [],
            "tools_needed": [],
            "current_step": 0,
            "pending_tools": [],
            "status": "error",
            "final_response": error_msg,
            "sources_used": [],
            "errors": state.get("errors", []) + [str(e)],
            "messages": state.get("messages", []) + [
                HumanMessage(content=query),
                AIMessage(content=error_msg),
            ],
        }
