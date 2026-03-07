"""
JAWIR OS - Polinema SIAKAD/LMS Tools
=====================================
Tools untuk mengakses data Polinema SIAKAD dan LMS SPADA.

Tools:
    1. polinema_get_biodata       - Get biodata mahasiswa
    2. polinema_get_akademik      - Get kehadiran, nilai, jadwal, kalender
    3. polinema_get_lms_assignments - Get LMS SPADA assignments

Prerequisites:
    - polinema_api_server.py running on http://localhost:8001
    - Node.js scraper configured with credentials
"""

import logging
from typing import Optional

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger("jawir.agent.tools.polinema")

# Polinema API Server URL
POLINEMA_API_URL = "http://localhost:8001"


# ============================================
# Input Schemas
# ============================================

class PolinemaBiodataInput(BaseModel):
    """Input schema for polinema_get_biodata tool."""
    force_refresh: bool = Field(
        default=False,
        description="Force refresh data from SIAKAD (default: use cached data if available)"
    )


class PolinemaAkademikInput(BaseModel):
    """Input schema for polinema_get_akademik tool."""
    include_kehadiran: bool = Field(
        default=True,
        description="Include kehadiran (attendance) data"
    )
    include_nilai: bool = Field(
        default=True,
        description="Include nilai (grades) data"
    )
    include_jadwal: bool = Field(
        default=True,
        description="Include jadwal (schedule) data"
    )
    include_kalender: bool = Field(
        default=True,
        description="Include kalender akademik (academic calendar) data"
    )
    force_refresh: bool = Field(
        default=False,
        description="Force refresh data from SIAKAD"
    )


class PolinemaLMSInput(BaseModel):
    """Input schema for polinema_get_lms_assignments tool."""
    force_refresh: bool = Field(
        default=False,
        description="Force refresh data from LMS SPADA"
    )


# ============================================
# Tool Implementations
# ============================================

async def _check_server_health() -> bool:
    """Check if Polinema API server is running."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{POLINEMA_API_URL}/health")
            health = r.json()
            return health.get("status") in ["healthy", "degraded"]
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return False


async def _get_biodata_impl(force_refresh: bool = False) -> str:
    """
    Implementation for polinema_get_biodata.
    
    Returns biodata mahasiswa from Polinema SIAKAD including:
    - Nama, NIM, Program Studi
    - Status mahasiswa (aktif/cuti/dll)
    - Data kontak
    - Info akademik lainnya
    """
    try:
        logger.info("📋 Fetching biodata from Polinema API...")
        
        if not await _check_server_health():
            return "❌ Polinema API server tidak berjalan. Pastikan server aktif di port 8001."
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            # POST to /scrape/biodata (stateless, uses default credentials)
            response = await client.post(f"{POLINEMA_API_URL}/scrape/biodata")
            response.raise_for_status()
            data = response.json()
        
        if data.get("status") == "error":
            error = data.get("error", "Unknown error")
            return f"❌ Gagal ambil biodata: {error}"
        
        # Format biodata - server returns {"status": "success", "data": {"raw": {...}, "summary": "..."}}
        result_data = data.get("data", {})
        summary_text = result_data.get("summary", "")
        raw_data = result_data.get("raw", {})
        
        if summary_text:
            return f"✅ **Biodata Mahasiswa Polinema**\n\n{summary_text}"
        elif isinstance(raw_data, dict) and raw_data:
            output = "✅ **Biodata Mahasiswa Polinema**\n\n"
            for key, value in raw_data.items():
                output += f"- **{key}**: {value}\n"
            return output
        else:
            return f"✅ Biodata retrieved:\n\n{str(raw_data)[:2000]}"
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return f"❌ Failed to connect to Polinema API: {str(e)}"
    except Exception as e:
        logger.error(f"Error getting biodata: {e}")
        return f"❌ Error: {str(e)}"


async def _get_akademik_impl(
    include_kehadiran: bool = True,
    include_nilai: bool = True,
    include_jadwal: bool = True,
    include_kalender: bool = True,
    force_refresh: bool = False
) -> str:
    """
    Implementation for polinema_get_akademik.
    
    Returns akademik data including:
    - Kehadiran per semester (attendance records)
    - Nilai mata kuliah (grades)
    - Jadwal perkuliahan (class schedule with Zoom links)
    - Kalender akademik (academic calendar)
    """
    try:
        logger.info("📚 Fetching akademik data from Polinema API...")
        
        if not await _check_server_health():
            return "❌ Polinema API server tidak berjalan. Pastikan server aktif di port 8001."
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            # POST to /scrape/akademik (stateless, uses default credentials)
            response = await client.post(f"{POLINEMA_API_URL}/scrape/akademik")
            response.raise_for_status()
            data = response.json()
        
        if data.get("status") == "error":
            error = data.get("error", "Unknown error")
            return f"❌ Gagal ambil data akademik: {error}"
        
        # Format akademik - server returns {"status": "success", "data": {"raw": {...}, "summary": "..."}}
        result_data = data.get("data", {})
        summary_text = result_data.get("summary", "")
        raw_data = result_data.get("raw", {})
        
        output = "✅ **Data Akademik Polinema**\n\n"
        
        # Always start with summary if available
        if summary_text:
            output += summary_text + "\n\n"
        
        # Also extract detailed data from raw for better responses
        if isinstance(raw_data, dict) and raw_data:
            # Jadwal details - extract mata kuliah names if not in summary
            if include_jadwal and "jadwal" in raw_data and raw_data["jadwal"]:
                jadwal = raw_data["jadwal"]
                if isinstance(jadwal, dict):
                    mata_kuliah = jadwal.get("mata_kuliah", [])
                    if mata_kuliah and not any(mk.get("mata_kuliah", "") in summary_text for mk in mata_kuliah[:1]):
                        tahun = jadwal.get("tahun_akademik", "")
                        kelas = jadwal.get("kelas", "")
                        jadwal_lengkap = any(mk.get("hari") and mk.get("jam") for mk in mata_kuliah)
                        
                        output += f"\n📅 **Daftar Mata Kuliah** ({len(mata_kuliah)} MK)"
                        if kelas:
                            output += f" - Kelas {kelas}"
                        if tahun:
                            output += f" - {tahun}"
                        output += "\n"
                        
                        if not jadwal_lengkap:
                            output += "⚠️ Jadwal hari & jam belum diinput oleh admin\n"
                        
                        for i, mk in enumerate(mata_kuliah, 1):
                            kode = mk.get("kode_mk", "")
                            nama_mk = mk.get("mata_kuliah", "")
                            dosen = mk.get("dosen", "")
                            hari = mk.get("hari", "")
                            jam = mk.get("jam", "")
                            
                            output += f"\n{i}. **{nama_mk}**"
                            if kode:
                                output += f" ({kode})"
                            if hari and jam:
                                output += f" - {hari} {jam}"
                            if dosen:
                                output += f"\n   Dosen: {dosen}"
                        output += "\n"
            
            # Presensi details
            if include_kehadiran and "presensi" in raw_data and raw_data["presensi"] and "presensi" not in summary_text.lower():
                presensi = raw_data["presensi"]
                if isinstance(presensi, dict):
                    output += f"\n📊 **Presensi**: Data kehadiran tersedia\n"
            
            # Nilai details
            if include_nilai and "nilai" in raw_data and raw_data["nilai"] and "nilai" not in summary_text.lower():
                output += f"\n📈 **Nilai**: Data nilai tersedia\n"
            
            # Kalender details
            if include_kalender and "kalender" in raw_data and raw_data["kalender"] and "kalender" not in summary_text.lower():
                output += f"\n📆 **Kalender Akademik**: Data tersedia\n"
        
        if output.strip() == "✅ **Data Akademik Polinema**":
            output += str(raw_data)[:2000]
        
        return output
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return f"❌ Failed to connect to Polinema API: {str(e)}"
    except Exception as e:
        logger.error(f"Error getting akademik data: {e}")
        return f"❌ Error: {str(e)}"


async def _get_lms_assignments_impl(force_refresh: bool = False) -> str:
    """
    Implementation for polinema_get_lms_assignments.
    
    Returns LMS SPADA data including:
    - List of enrolled courses (mata kuliah)
    - Current assignments/tugas with deadlines
    - Quiz and essay tasks
    """
    try:
        logger.info("🎓 Fetching LMS data from Polinema API...")
        
        if not await _check_server_health():
            return "❌ Polinema API server tidak berjalan. Pastikan server aktif di port 8001."
        
        async with httpx.AsyncClient(timeout=300.0) as client:  # LMS takes longer
            # POST to /scrape/lms (stateless, uses default credentials)
            response = await client.post(f"{POLINEMA_API_URL}/scrape/lms")
            response.raise_for_status()
            data = response.json()
        
        if data.get("status") == "error":
            error = data.get("error", "Unknown error")
            return f"❌ Gagal ambil data LMS: {error}"
        
        # Format LMS - server returns {"status": "success", "data": {"raw": {...}, "summary": "..."}}
        result_data = data.get("data", {})
        summary_text = result_data.get("summary", "")
        raw_data = result_data.get("raw", result_data)  # fallback to result_data if no raw
        
        output = "✅ **Data LMS SPADA Polinema**\n\n"
        
        if summary_text:
            output += summary_text
        elif isinstance(raw_data, dict) and raw_data:
            for section, content in raw_data.items():
                if content:
                    output += f"📋 **{section.upper()}**:\n{str(content)[:400]}\n\n"
        elif isinstance(raw_data, str):
            output += raw_data[:2000]
        else:
            output += str(raw_data)[:2000]
        
        return output
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return f"❌ Failed to connect to Polinema API: {str(e)}"
    except Exception as e:
        logger.error(f"Error getting LMS data: {e}")
        return f"❌ Error: {str(e)}"


# ============================================
# Tool Factory Functions
# ============================================

def create_polinema_biodata_tool() -> StructuredTool:
    """
    Create polinema_get_biodata tool.

    Use this tool when user asks about:
    - "Siapa nama saya?"
    - "Apa NIM saya?"
    - "Program studi saya apa?"
    - "Status mahasiswa saya apa?"
    - "Cek biodata saya"
    - "Data mahasiswa Polinema"
    - "Profil mahasiswa"
    - Any question about personal/biodata information
    """
    return StructuredTool.from_function(
        func=_get_biodata_impl,
        coroutine=_get_biodata_impl,
        name="polinema_get_biodata",
        description=(
            "Mengambil dan menampilkan biodata mahasiswa dari Polinema SIAKAD. "
            "Mengembalikan: Nama lengkap, NIM, Program Studi, Semester, Status mahasiswa, dan informasi kontak. "
            "Gunakan tool ini saat user bertanya: 'Cek biodata saya', 'Siapa nama saya?', 'Apa NIM saya?', "
            "'Data mahasiswa Polinema', 'Profil saya di SIAKAD', 'Biodata Polinema', atau pertanyaan sejenis."
        ),
        args_schema=PolinemaBiodataInput,
    )


def create_polinema_akademik_tool() -> StructuredTool:
    """
    Create polinema_get_akademik tool.

    Use this tool when user asks about:
    - "Berapa IPK saya?"
    - "Jadwal kuliah saya hari ini?"
    - "Link Zoom untuk kelas X?"
    - "Kehadiran saya semester ini?"
    - "Kalender akademik kapan UTS?"
    - "Data akademik Polinema"
    - "Nilai kuliah saya"
    - "Jadwal SIAKAD"
    - Any question about academic data
    """
    return StructuredTool.from_function(
        func=_get_akademik_impl,
        coroutine=_get_akademik_impl,
        name="polinema_get_akademik",
        description=(
            "Mengambil dan menampilkan data akademik lengkap dari Polinema SIAKAD. "
            "Mengembalikan: Kehadiran per semester, Daftar nilai mata kuliah (IPK), Jadwal perkuliahan dengan link Zoom, "
            "Kalender akademik (jadwal UTS/UAS), dan info tugas/assignments dari jadwal kuliah. "
            "PRIORITAS: Gunakan tool ini untuk SEMUA pertanyaan akademik termasuk tugas, jadwal, nilai, kehadiran. "
            "Contoh: 'Tugas apa yang harus dikerjakan?', 'Jadwal kuliah hari ini', 'Nilai semester ini', "
            "'Kehadiran kuliah', 'Kalender akademik', 'IPK saya', 'Ada tugas apa?', 'List tugas kuliah'."
        ),
        args_schema=PolinemaAkademikInput,
    )


def create_polinema_lms_tool() -> StructuredTool:
    """
    Create polinema_get_lms_assignments tool.
    
    NOTE: LMS SPADA scraping is NOT implemented yet.
    Agent should use polinema_get_akademik instead for tugas/assignments.
    """
    return StructuredTool.from_function(
        func=_get_lms_assignments_impl,
        coroutine=_get_lms_assignments_impl,
        name="polinema_get_lms_assignments",
        description=(
            "[DEPRECATED - JANGAN GUNAKAN] Tool ini BELUM DIIMPLEMENTASIKAN. "
            "LMS SPADA tidak tersedia. Untuk melihat tugas/assignments, gunakan polinema_get_akademik sebagai gantinya. "
            "Tool ini akan mengembalikan error. SELALU gunakan polinema_get_akademik untuk semua data akademik."
        ),
        args_schema=PolinemaLMSInput,
    )
