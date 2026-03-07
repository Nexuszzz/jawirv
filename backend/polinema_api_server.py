"""
Polinema API Server for JAWIR
FastAPI REST API wrapper untuk SIAKAD data
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
import os

from polinema_scraper import PolinemaScraper

app = FastAPI(
    title="Polinema SIAKAD API",
    description="API untuk mengakses data SIAKAD Polinema",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global scraper instance
scraper: Optional[PolinemaScraper] = None
is_logged_in = False

# Configuration from environment or defaults
NIM = os.getenv("POLINEMA_NIM", "244101060077")
PASSWORD = os.getenv("POLINEMA_PASSWORD", "Fahri080506!")


class LoginRequest(BaseModel):
    nim: Optional[str] = None
    password: Optional[str] = None


def _init_and_login(nim: str, password: str) -> bool:
    """Sync helper: init scraper + login (runs in thread)"""
    global scraper, is_logged_in
    try:
        # Close existing scraper if any
        if scraper:
            try:
                scraper.close()
            except:
                pass
        
        scraper = PolinemaScraper(nim, password, headless=True)
        scraper.init()
        success = scraper.login()
        if success:
            is_logged_in = True
        else:
            is_logged_in = False
        return success
    except Exception as e:
        print(f"❌ Init/Login error: {e}")
        is_logged_in = False
        return False


def _force_relogin() -> bool:
    """Force re-login when session expired"""
    global scraper, is_logged_in
    is_logged_in = False
    print("🔄 Session expired, forcing re-login...")
    return _init_and_login(NIM, PASSWORD)


async def ensure_logged_in(force_refresh: bool = False):
    """Ensure scraper is initialized and logged in"""
    global scraper, is_logged_in
    
    if is_logged_in and scraper and not force_refresh:
        return True
    
    try:
        print("🔐 Initializing scraper...")
        success = await asyncio.to_thread(_init_and_login, NIM, PASSWORD)
        if success:
            return True
        else:
            raise HTTPException(status_code=401, detail="Login failed - check credentials or SIAKAD availability")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper error: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Polinema SIAKAD API",
        "status": "running",
        "logged_in": is_logged_in,
        "endpoints": {
            "login": "POST /api/login",
            "biodata": "GET /api/biodata",
            "presensi": "GET /api/presensi",
            "kalender": "GET /api/kalender",
            "jadwal": "GET /api/jadwal",
            "nilai": "GET /api/nilai",
            "all": "GET /api/all"
        }
    }


@app.get("/health")
async def health():
    """Health check - always healthy if server is running (auto-login on demand)"""
    return {
        "status": "healthy",
        "logged_in": is_logged_in,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/login")
async def login(request: Optional[LoginRequest] = None):
    """Login to SIAKAD"""
    global scraper, is_logged_in
    
    try:
        nim = request.nim if request else NIM
        password = request.password if request else PASSWORD
        
        success = await asyncio.to_thread(_init_and_login, nim, password)
        
        if success:
            return {"success": True, "message": "Logged in successfully"}
        else:
            raise HTTPException(status_code=401, detail="Login failed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/biodata")
async def get_biodata():
    """Get biodata mahasiswa"""
    await ensure_logged_in()
    
    try:
        data = await asyncio.to_thread(scraper.get_biodata)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/presensi")
async def get_presensi(semester: str = "2025/2026 Genap"):
    """Get data presensi/kehadiran"""
    await ensure_logged_in()
    
    try:
        data = await asyncio.to_thread(scraper.get_presensi, semester)
        return {"success": True, "data": data, "semester": semester}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kalender")
async def get_kalender():
    """Get kalender akademik"""
    await ensure_logged_in()
    
    try:
        data = await asyncio.to_thread(scraper.get_kalender)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jadwal")
async def get_jadwal():
    """Get jadwal perkuliahan"""
    await ensure_logged_in()
    
    try:
        data = await asyncio.to_thread(scraper.get_jadwal)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/nilai")
async def get_nilai():
    """Get nilai/KHS"""
    await ensure_logged_in()
    
    try:
        data = await asyncio.to_thread(scraper.get_nilai)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/all")
async def get_all():
    """Get all data"""
    await ensure_logged_in()
    
    try:
        data = await asyncio.to_thread(scraper.get_all_data)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/logout")
async def logout():
    """Logout and cleanup"""
    global scraper, is_logged_in
    
    try:
        if scraper:
            await asyncio.to_thread(scraper.close)
        scraper = None
        is_logged_in = False
        return {"success": True, "message": "Logged out"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Stateless Scrape Endpoints (for JAWIR tools)
# ============================================

@app.post("/scrape/biodata")
async def scrape_biodata():
    """
    Stateless biodata scrape - auto-login if needed.
    Used by JAWIR agent tools.
    """
    try:
        await ensure_logged_in()
        data = await asyncio.to_thread(scraper.get_biodata)
        
        # Format summary
        summary = ""
        if isinstance(data, dict):
            for key, value in data.items():
                if value:
                    summary += f"- **{key}**: {value}\n"
        
        return {
            "status": "success",
            "data": {
                "raw": data,
                "summary": summary or str(data)
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/scrape/akademik")
async def scrape_akademik():
    """
    Stateless akademik data scrape - auto-login if needed.
    Gets kehadiran, nilai, jadwal, kalender.
    Used by JAWIR agent tools.
    """
    max_attempts = 2
    
    for attempt in range(max_attempts):
        try:
            # Force refresh on retry
            await ensure_logged_in(force_refresh=(attempt > 0))
            
            # Gather all akademik data
            akademik_data = {}
            scrape_success = False
            
            try:
                jadwal = await asyncio.to_thread(scraper.get_jadwal)
                if jadwal:
                    akademik_data["jadwal"] = jadwal
                    scrape_success = True
            except Exception as e:
                print(f"Warning: get_jadwal error: {e}")
                akademik_data["jadwal"] = None
                
            try:
                presensi = await asyncio.to_thread(scraper.get_presensi, "2025/2026 Genap")
                if presensi:
                    akademik_data["presensi"] = presensi
                    scrape_success = True
            except Exception as e:
                print(f"Warning: get_presensi error: {e}")
                akademik_data["presensi"] = None
                
            try:
                nilai = await asyncio.to_thread(scraper.get_nilai)
                if nilai:
                    akademik_data["nilai"] = nilai
                    scrape_success = True
            except Exception as e:
                print(f"Warning: get_nilai error: {e}")
                akademik_data["nilai"] = None
                
            try:
                kalender = await asyncio.to_thread(scraper.get_kalender)
                if kalender:
                    akademik_data["kalender"] = kalender
                    scrape_success = True
            except Exception as e:
                print(f"Warning: get_kalender error: {e}")
                akademik_data["kalender"] = None
            
            # If nothing scraped and we have more attempts, retry with re-login
            if not scrape_success and attempt < max_attempts - 1:
                print(f"⚠ No data scraped on attempt {attempt + 1}, retrying with re-login...")
                continue
            
            # Build summary
            summary_parts = []
            
            if akademik_data.get("jadwal"):
                jadwal = akademik_data["jadwal"]
                if isinstance(jadwal, dict):
                    mata_kuliah = jadwal.get("mata_kuliah", [])
                    kelas = jadwal.get("kelas", "")
                    tahun = jadwal.get("tahun_akademik", "")
                    
                    if mata_kuliah:
                        jadwal_lengkap = any(mk.get("hari") and mk.get("jam") for mk in mata_kuliah)
                        kelas_info = f" (Kelas {kelas})" if kelas else ""
                        tahun_info = f" - {tahun}" if tahun else ""
                        
                        jadwal_summary = f"📅 **Jadwal Perkuliahan**{kelas_info}{tahun_info}\n"
                        jadwal_summary += f"Total: {len(mata_kuliah)} Mata Kuliah\n\n"
                        
                        if jadwal_lengkap:
                            # Group by hari
                            jadwal_per_hari = jadwal.get("jadwal_per_hari", {})
                            for hari, items in jadwal_per_hari.items():
                                jadwal_summary += f"**{hari}:**\n"
                                for j in items:
                                    jam = j.get("jam", "")
                                    mk_name = j.get("mata_kuliah", "")
                                    dosen = j.get("dosen", "")
                                    jadwal_summary += f"  • {jam} | {mk_name}"
                                    if dosen:
                                        jadwal_summary += f" - {dosen}"
                                    jadwal_summary += "\n"
                                jadwal_summary += "\n"
                        else:
                            jadwal_summary += "⚠️ Jadwal hari & jam belum diinput oleh admin\n\n"
                            for i, mk in enumerate(mata_kuliah, 1):
                                kode = mk.get("kode_mk", "")
                                nama_mk = mk.get("mata_kuliah", "")
                                dosen = mk.get("dosen", "")
                                jadwal_summary += f"{i}. **{nama_mk}**"
                                if kode:
                                    jadwal_summary += f" ({kode})"
                                if dosen:
                                    jadwal_summary += f" - {dosen}"
                                jadwal_summary += "\n"
                        
                        summary_parts.append(jadwal_summary)
                    else:
                        summary_parts.append(f"📅 **Jadwal**: Data tersedia")
                elif isinstance(jadwal, list) and len(jadwal) > 0:
                    summary_parts.append(f"📅 **Jadwal**: {len(jadwal)} mata kuliah terjadwal")
            
            if akademik_data.get("presensi"):
                summary_parts.append(f"📊 **Presensi**: Data kehadiran tersedia")
            
            if akademik_data.get("nilai"):
                summary_parts.append(f"📈 **Nilai**: Data nilai tersedia")
                
            if akademik_data.get("kalender"):
                summary_parts.append(f"📆 **Kalender**: Kalender akademik tersedia")
            
            summary = "\n".join(summary_parts) if summary_parts else "Tidak ada data akademik"
            
            return {
                "status": "success",
                "data": {
                    "raw": akademik_data,
                    "summary": summary
                }
            }
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"⚠ Attempt {attempt + 1} failed: {e}, retrying with re-login...")
                continue
            return {"status": "error", "error": str(e)}
    
    return {"status": "error", "error": "All attempts failed"}


@app.post("/scrape/jadwal")
async def scrape_jadwal():
    """Stateless jadwal scrape."""
    try:
        await ensure_logged_in()
        data = await asyncio.to_thread(scraper.get_jadwal)
        
        # Format summary based on new format from extract_jadwal_table
        summary = ""
        
        if isinstance(data, dict):
            tahun = data.get("tahun_akademik", "")
            kelas = data.get("kelas", "")
            mata_kuliah = data.get("mata_kuliah", [])
            jadwal_per_hari = data.get("jadwal_per_hari", {})
            
            # Header
            if tahun or kelas:
                summary = f"📅 **Jadwal Perkuliahan**\n"
                if tahun:
                    summary += f"📆 Tahun Akademik: {tahun}\n"
                if kelas:
                    summary += f"🏫 Kelas: {kelas}\n"
                summary += "\n"
            
            # Check if jadwal hari/jam sudah lengkap
            jadwal_lengkap = any(mk.get("hari") and mk.get("jam") for mk in mata_kuliah)
            
            if mata_kuliah:
                summary += f"📚 **Daftar Mata Kuliah** ({len(mata_kuliah)} MK):\n\n"
                
                if jadwal_lengkap:
                    # Group by hari
                    for hari, jadwals in jadwal_per_hari.items():
                        summary += f"**{hari}:**\n"
                        for j in jadwals:
                            jam = j.get("jam", "")
                            mk = j.get("mata_kuliah", "")
                            ruang = j.get("ruangan", "")
                            dosen = j.get("dosen", "")
                            summary += f"  • {jam} | {mk}"
                            if ruang:
                                summary += f" ({ruang})"
                            if dosen:
                                summary += f" - {dosen}"
                            summary += "\n"
                        summary += "\n"
                else:
                    # Jadwal hari/jam belum diinput - tampilkan daftar MK saja
                    summary += "⚠️ *Jadwal hari & jam belum diinput oleh admin*\n\n"
                    for i, mk in enumerate(mata_kuliah, 1):
                        kode = mk.get("kode_mk", "")
                        nama_mk = mk.get("mata_kuliah", "")
                        dosen = mk.get("dosen", "")
                        
                        summary += f"{i}. **{nama_mk}**"
                        if kode:
                            summary += f" ({kode})"
                        if dosen:
                            summary += f"\n   👨‍🏫 {dosen}"
                        summary += "\n"
            else:
                summary = "📅 Tidak ada data jadwal ditemukan di SIAKAD."
        elif isinstance(data, list):
            # Old format fallback
            summary = f"📅 Ditemukan {len(data)} jadwal mata kuliah\n\n"
            for i, jadwal in enumerate(data[:10], 1):
                if isinstance(jadwal, dict):
                    mk = jadwal.get("mata_kuliah", jadwal.get("nama", "Unknown"))
                    hari = jadwal.get("hari", "")
                    jam = jadwal.get("jam", jadwal.get("waktu", ""))
                    summary += f"{i}. **{mk}** - {hari} {jam}\n"
        
        return {
            "status": "success",
            "data": {
                "raw": data,
                "summary": summary or str(data)[:2000]
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/scrape/lms")
async def scrape_lms():
    """
    Stateless LMS/SPADA data scrape.
    Note: LMS scraping may need separate implementation.
    """
    return {
        "status": "error",
        "error": "LMS SPADA scraping belum diimplementasikan. Gunakan jadwal SIAKAD."
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global scraper
    if scraper:
        scraper.close()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("POLINEMA_PORT", "8001"))
    print(f"\n🚀 Starting Polinema API Server...")
    print(f"📍 URL: http://localhost:{port}")
    print(f"📚 Docs: http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)
