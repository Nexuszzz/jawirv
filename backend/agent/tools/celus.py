"""
JAWIR OS - Celus Automation Tools
==================================
Tools untuk mengakses Celus.io Design Studio automation.
Generate rangkaian elektronik secara otomatis melalui Celus AI.

Tools:
    1. celus_update_config     - Update prompt untuk circuit design
    2. celus_run_automation    - Jalankan automation untuk generate circuit
    3. celus_get_downloads     - List file hasil download (PDF/ZIP)

Prerequisites:
    - celus_api_server.py running on http://localhost:8002
    - Node.js dengan Playwright installed
    - auth.json Celus yang valid
"""

import logging
from typing import Optional, List

import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger("jawir.agent.tools.celus")

# Celus API Server URL
CELUS_API_URL = "http://localhost:8002"


# ============================================
# Input Schemas
# ============================================

class CelusConfigInput(BaseModel):
    """Input schema for celus_update_config tool."""
    prompt: str = Field(
        ...,
        description=(
            "Prompt detail untuk Celus AI. Harus berisi: "
            "1) Mikrokontroler (ESP32, Arduino, STM32, dll), "
            "2) Sensor/aktuator yang digunakan, "
            "3) Koneksi pin yang diinginkan, "
            "4) Power supply specification. "
            "Contoh: 'Buat rangkaian ESP32 dengan sensor DHT11 pada pin GPIO4, "
            "LED pada GPIO2, buzzer pada GPIO16. Power supply 5V.'"
        ),
        min_length=10
    )
    headless: bool = Field(
        default=True,
        description="Jalankan browser tanpa UI (default True untuk speed)"
    )
    download_mode: str = Field(
        default="pdf",
        description="Mode download: 'pdf' untuk PDF saja, 'all' untuk ZIP semua file"
    )


class CelusRunInput(BaseModel):
    """Input schema for celus_run_automation tool."""
    timeout_seconds: int = Field(
        default=300,
        description="Timeout dalam detik (default 5 menit, max 10 menit)",
        ge=60,
        le=600
    )


class CelusDownloadsInput(BaseModel):
    """Input schema for celus_get_downloads tool."""
    limit: int = Field(
        default=5,
        description="Jumlah file terbaru yang ditampilkan (default 5)",
        ge=1,
        le=20
    )


# ============================================
# Tool Implementations
# ============================================

async def _update_config_impl(
    prompt: str,
    headless: bool = True,
    download_mode: str = "pdf"
) -> str:
    """
    Implementation for celus_update_config.
    
    Updates the Celus config with a new circuit design prompt.
    This must be called BEFORE running the automation.
    """
    try:
        logger.info(f"📝 Updating Celus config with prompt: {prompt[:50]}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CELUS_API_URL}/config",
                json={
                    "prompt": prompt,
                    "headless": headless,
                    "download_mode": download_mode
                }
            )
            response.raise_for_status()
            data = response.json()
        
        if data.get("status") != "success":
            return f"❌ Failed to update config: {data.get('message', 'Unknown error')}"
        
        preview = data.get("prompt_preview", prompt[:100])
        return f"""✅ **Config Updated Successfully**

📝 **Prompt Preview**: {preview}
⚙️ **Settings**:
  - Headless Mode: {'Ya' if headless else 'Tidak'}
  - Download Mode: {download_mode.upper()}

🚀 Selanjutnya panggil `celus_run_automation` untuk menjalankan automation."""
        
    except httpx.ConnectError:
        logger.error("Cannot connect to Celus API server")
        return (
            "❌ Cannot connect to Celus API Server!\n\n"
            "Pastikan server berjalan:\n"
            "```\n"
            "cd automasicelus/celus-auto\n"
            "python celus_api_server.py\n"
            "```"
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return f"❌ HTTP Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return f"❌ Error: {str(e)}"


async def _run_automation_impl(timeout_seconds: int = 300) -> str:
    """
    Implementation for celus_run_automation.
    
    Runs the full Celus automation flow:
    1. Opens Celus Design Studio
    2. Creates new project
    3. Opens Design Canvas
    4. Inputs prompt to AI assistant
    5. Waits for Resolve
    6. Downloads output file (PDF/ZIP)
    
    Returns path to downloaded file on success.
    """
    try:
        logger.info(f"🚀 Starting Celus automation (timeout: {timeout_seconds}s)...")
        
        # This can take a long time, use extended timeout
        async with httpx.AsyncClient(timeout=timeout_seconds + 30) as client:
            response = await client.post(
                f"{CELUS_API_URL}/run",
                json={"timeout": timeout_seconds}
            )
            response.raise_for_status()
            data = response.json()
        
        status = data.get("status", "error")
        
        if status == "success":
            duration = data.get("duration_seconds", 0)
            downloaded = data.get("downloaded_file", "No file")
            
            result = f"""✅ **Celus Automation Completed!**

⏱️ **Duration**: {duration:.1f} detik
📁 **Downloaded File**: {downloaded}

🎉 Rangkaian elektronik berhasil di-generate!"""

            # Add output log preview if available
            output_log = data.get("output_log", "")
            if output_log:
                # Extract key info from log
                if "✅" in output_log:
                    result += "\n\n📋 **Progress Log**:\n"
                    for line in output_log.split("\n"):
                        if "✅" in line or "STEP" in line:
                            result += f"  {line.strip()}\n"
            
            return result
        elif status == "warning":
            # Automation completed but no new file was downloaded
            duration = data.get("duration_seconds", 0)
            message = data.get("message", "No new file downloaded")
            
            result = f"""⚠️ **Celus Automation Completed dengan Warning**

⏱️ **Duration**: {duration:.1f} detik
📁 **Downloaded File**: Tidak ada file baru

**Masalah**: {message}

**Kemungkinan penyebab**:
1. Celus gagal generate rangkaian (cek prompt)
2. Download button tidak terdeteksi (UI Celus berubah)
3. Session auth.json sudah expired

**Solusi**: Coba jalankan ulang dengan prompt yang lebih spesifik."""
            
            return result
        else:
            error = data.get("error", "Unknown error")
            duration = data.get("duration_seconds", 0)
            
            result = f"""❌ **Celus Automation Failed**

⏱️ **Duration**: {duration:.1f} detik
❗ **Error**: {error[:200]}

**Troubleshooting**:
1. Cek apakah auth.json masih valid
2. Pastikan Celus.io bisa diakses
3. Coba jalankan dengan headless=False untuk debug"""

            return result
        
    except httpx.ConnectError:
        logger.error("Cannot connect to Celus API server")
        return (
            "❌ Cannot connect to Celus API Server!\n\n"
            "Pastikan server berjalan:\n"
            "```\n"
            "cd automasicelus/celus-auto\n"
            "python celus_api_server.py\n"
            "```"
        )
    except httpx.TimeoutException:
        logger.error("Automation timeout")
        return (
            f"⏰ **Timeout** setelah {timeout_seconds} detik.\n\n"
            "Celus AI mungkin sedang sibuk. Coba:\n"
            "1. Tingkatkan timeout_seconds\n"
            "2. Simplifikasi prompt\n"
            "3. Jalankan ulang"
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return f"❌ HTTP Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error running automation: {e}")
        return f"❌ Error: {str(e)}"


async def _get_downloads_impl(limit: int = 5) -> str:
    """
    Implementation for celus_get_downloads.
    
    Returns list of downloaded files from Celus automation.
    """
    try:
        logger.info(f"📁 Fetching downloads list (limit: {limit})...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{CELUS_API_URL}/downloads")
            response.raise_for_status()
            data = response.json()
        
        if data.get("status") != "success":
            return f"❌ Failed to get downloads: Unknown error"
        
        downloads = data.get("downloads", [])
        total = data.get("total_count", 0)
        
        if not downloads:
            return "📁 Belum ada file yang di-download.\n\nJalankan `celus_run_automation` untuk generate rangkaian."
        
        result = f"📁 **Downloaded Files** ({total} total)\n\n"
        
        for i, file in enumerate(downloads[:limit]):
            filename = file.get("filename", "Unknown")
            size_kb = file.get("size_bytes", 0) / 1024
            modified = file.get("modified", "N/A")
            file_type = file.get("type", "file").upper()
            
            result += f"{i+1}. **{filename}**\n"
            result += f"   📊 Size: {size_kb:.1f} KB | Type: {file_type}\n"
            result += f"   📅 Modified: {modified[:19]}\n\n"
        
        if total > limit:
            result += f"... dan {total - limit} file lainnya\n"
        
        return result
        
    except httpx.ConnectError:
        logger.error("Cannot connect to Celus API server")
        return (
            "❌ Cannot connect to Celus API Server!\n\n"
            "Pastikan server berjalan di port 8002."
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return f"❌ HTTP Error: {str(e)}"
    except Exception as e:
        logger.error(f"Error getting downloads: {e}")
        return f"❌ Error: {str(e)}"


# ============================================
# Tool Factory Functions
# ============================================

def create_celus_config_tool() -> StructuredTool:
    """
    Create celus_update_config tool.
    
    Use this tool when user wants to:
    - Set up a new circuit design
    - Change the Celus prompt
    - Configure automation settings
    
    MUST be called BEFORE celus_run_automation.
    """
    return StructuredTool.from_function(
        func=_update_config_impl,
        coroutine=_update_config_impl,
        name="celus_update_config",
        description=(
            "Update konfigurasi Celus untuk generate rangkaian elektronik. "
            "HARUS dipanggil SEBELUM celus_run_automation. "
            "Input: prompt detail rangkaian (mikrokontroler, sensor, pin, power supply). "
            "Contoh prompt: 'Buat rangkaian ESP32-S3 dengan flame sensor pada GPIO4, "
            "buzzer pada GPIO2, LED pada GPIO16. Power 5V.' "
            "Gunakan tool ini ketika user minta buat skematik/rangkaian di Celus."
        ),
        args_schema=CelusConfigInput,
    )


def create_celus_run_tool() -> StructuredTool:
    """
    Create celus_run_automation tool.
    
    Use this tool when user wants to:
    - Generate a circuit design
    - Run Celus automation
    - Download schematic PDF
    
    Config must be set first with celus_update_config.
    """
    return StructuredTool.from_function(
        func=_run_automation_impl,
        coroutine=_run_automation_impl,
        name="celus_run_automation",
        description=(
            "Jalankan Celus automation untuk generate rangkaian elektronik dan download file. "
            "Proses: Buka Celus → Create project → Input prompt ke AI → Tunggu resolve → Download PDF. "
            "CATATAN: Panggil celus_update_config dulu untuk set prompt. "
            "Waktu eksekusi: 2-5 menit. Output: file PDF/ZIP rangkaian. "
            "Gunakan tool ini setelah config sudah di-set dan user siap generate."
        ),
        args_schema=CelusRunInput,
    )


def create_celus_downloads_tool() -> StructuredTool:
    """
    Create celus_get_downloads tool.
    
    Use this tool when user wants to:
    - See list of generated files
    - Check download history
    - Find specific output file
    """
    return StructuredTool.from_function(
        func=_get_downloads_impl,
        coroutine=_get_downloads_impl,
        name="celus_get_downloads",
        description=(
            "Lihat daftar file hasil download dari Celus automation. "
            "Returns: filename, size, type (PDF/ZIP), tanggal. "
            "Gunakan tool ini untuk melihat hasil generate rangkaian sebelumnya."
        ),
        args_schema=CelusDownloadsInput,
    )


# ============================================
# Combined Create Function (for easy import)
# ============================================

def create_all_celus_tools() -> List[StructuredTool]:
    """Create all Celus tools for registration."""
    return [
        create_celus_config_tool(),
        create_celus_run_tool(),
        create_celus_downloads_tool(),
    ]
