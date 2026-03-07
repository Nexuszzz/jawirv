"""
JAWIR OS - KiCad Schematic Design Tool
========================================
Tool untuk generate skematik rangkaian elektronika.
"""

import logging
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger("jawir.agent.tools.kicad")


class KicadDesignInput(BaseModel):
    """Input schema for KiCad schematic design tool."""
    description: str = Field(description="Deskripsi rangkaian elektronika yang ingin dibuat. Contoh: 'LED blink dengan resistor 330 ohm' atau 'sensor suhu DHT11 dengan ESP32'")
    project_name: str = Field(description="Nama project untuk filename (tanpa spasi, gunakan underscore). Contoh: 'led_blink'")
    open_kicad: bool = Field(default=False, description="Apakah otomatis buka KiCad setelah file dibuat")


def create_kicad_tool() -> StructuredTool:
    """Create KiCad schematic design tool."""

    async def _kicad_design(description: str, project_name: str, open_kicad: bool = False) -> str:
        """Generate schematic rangkaian elektronika."""
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage, SystemMessage
        from agent.api_rotator import get_api_key
        from tools.kicad import (
            save_schematic,
            open_in_kicad as open_kicad_app,
            get_component_info_for_ai,
            get_template_info_for_ai,
            get_template,
            get_available_templates,
        )
        from agent.nodes.kicad_designer import (
            KicadDesignOutput,
            KICAD_DESIGNER_PROMPT,
            parse_design_to_plan,
        )

        try:
            # Check template first
            available_templates = get_available_templates()
            for tpl_name in available_templates:
                if tpl_name.replace("_", " ") in description.lower():
                    plan = get_template(tpl_name)
                    if plan:
                        result = save_schematic(plan)
                        if result.success:
                            return (
                                f"✅ Skematik '{result.project_name}' berhasil dibuat dari template!\n"
                                f"📁 File: {result.file_path}\n"
                                f"📊 Komponen: {result.component_count}\n"
                                f"🔌 Koneksi: {result.wire_count}"
                            )

            # Use Gemini for custom design
            api_key = get_api_key()
            llm = ChatGoogleGenerativeAI(
                model="gemini-3-flash-preview",
                google_api_key=api_key,
                temperature=0.3,
                convert_system_message_to_human=True,
            )
            structured_llm = llm.with_structured_output(KicadDesignOutput)

            component_info = get_component_info_for_ai()
            template_info = get_template_info_for_ai()
            system_prompt = KICAD_DESIGNER_PROMPT.format(
                component_info=component_info,
                template_info=template_info,
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Desain skematik: {description}. Project name: {project_name}"),
            ]

            design: KicadDesignOutput = await structured_llm.ainvoke(messages)

            # Generate schematic
            if design.use_template:
                plan = get_template(design.use_template)
                if not plan:
                    plan = parse_design_to_plan(design)
            else:
                plan = parse_design_to_plan(design)

            result = save_schematic(plan)

            if result.success:
                kicad_status = ""
                if open_kicad:
                    opened = open_kicad_app(result.file_path)
                    if opened:
                        kicad_status = "\n🔧 File dibuka di KiCad"
                    else:
                        kicad_status = "\n⚠️ KiCad tidak ditemukan. Silakan buka file secara manual atau install KiCad."

                return (
                    f"✅ Skematik '{result.project_name}' berhasil dibuat!\n"
                    f"📁 File: {result.file_path}\n"
                    f"📊 Komponen: {result.component_count}\n"
                    f"🔌 Koneksi: {result.wire_count}"
                    f"{kicad_status}\n\n"
                    f"Penjelasan: {design.explanation}"
                )
            else:
                return f"❌ Gagal membuat skematik: {result.message}\nErrors: {result.errors}"

        except Exception as e:
            return f"❌ Error saat mendesain skematik: {str(e)}"

    return StructuredTool.from_function(
        func=_kicad_design,
        coroutine=_kicad_design,
        name="generate_kicad_schematic",
        description=(
            "Generate skematik rangkaian elektronika (.kicad_sch file). "
            "Gunakan tool ini untuk permintaan desain circuit, PCB, atau komponen elektronik. "
            "Contoh: LED blink, sensor suhu, motor driver, rangkaian dengan Arduino/ESP32."
        ),
        args_schema=KicadDesignInput,
    )
