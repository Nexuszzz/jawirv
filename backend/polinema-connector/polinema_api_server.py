"""
Polinema API Server - FastAPI Wrapper for Node.js Scraper
===========================================================
Provides HTTP API endpoints for JAWIR tools to access Polinema SIAKAD/LMS data.

Architecture:
    Python FastAPI ← HTTP → This Server ← subprocess → Node.js Playwright Scraper

Endpoints:
    GET  /health              - Health check
    POST /scrape/biodata      - Get mahasiswa biodata
    POST /scrape/akademik     - Get kehadiran, nilai, jadwal, kalender
    POST /scrape/lms          - Get LMS SPADA courses and assignments
    
Run:
    uvicorn polinema_api_server:app --host 0.0.0.0 --port 8001
"""

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("polinema_api")

# Get current directory (polinema-connector/)
CURRENT_DIR = Path(__file__).parent
SCRAPER_PATH = CURRENT_DIR / "scraper_enhanced.js"

# App instance
app = FastAPI(
    title="Polinema API Server",
    description="HTTP API wrapper for Polinema SIAKAD/LMS scraper",
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


# ============================================
# Request/Response Models
# ============================================

class PolinemaCredentials(BaseModel):
    """Credentials for Polinema SIAKAD login."""
    nim: str = Field(default="244101060077", description="NIM mahasiswa")
    password: str = Field(default="Fahri080506!", description="Password SIAKAD")


class BiodataResponse(BaseModel):
    """Response for biodata endpoint."""
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str


class AkademikResponse(BaseModel):
    """Response for akademik endpoint."""
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str


class LMSResponse(BaseModel):
    """Response for LMS endpoint."""
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str


# ============================================
# Helper Functions
# ============================================

async def run_scraper(
    scrape_type: str,
    credentials: Optional[PolinemaCredentials] = None
) -> Dict[str, Any]:
    """
    Run Node.js scraper with specific type.
    
    Args:
        scrape_type: Type of scraping ('biodata', 'akademik', 'lms')
        credentials: Optional custom credentials (default uses hardcoded)
    
    Returns:
        Scraped data as dictionary
    
    Raises:
        HTTPException if scraper fails
    """
    try:
        # Check if scraper exists
        if not SCRAPER_PATH.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Scraper not found: {SCRAPER_PATH}"
            )
        
        # Prepare environment variables
        env = os.environ.copy()
        if credentials:
            env["POLINEMA_NIM"] = credentials.nim
            env["POLINEMA_PASSWORD"] = credentials.password
        
        # Build command
        cmd = ["node", str(SCRAPER_PATH)]
        
        # Run scraper
        logger.info(f"🚀 Running scraper: {scrape_type}")
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=str(CURRENT_DIR)
        )
        
        stdout, stderr = await process.communicate()
        
        # Check return code
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore')
            logger.error(f"❌ Scraper failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Scraper failed: {error_msg[:500]}"
            )
        
        # Parse output JSON
        output_file = CURRENT_DIR / "polinema_complete_data.json"
        if not output_file.exists():
            raise HTTPException(
                status_code=500,
                detail="Scraper completed but output file not found"
            )
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"✅ Scraper completed: {scrape_type}")
        
        # Extract only requested data
        if scrape_type == "biodata":
            return {"biodata": data.get("biodata", {})}
        elif scrape_type == "akademik":
            return {
                "kehadiran": data.get("kehadiran", []),
                "nilai": data.get("nilai", {}),
                "jadwal": data.get("jadwal", {}),
                "kalender": data.get("kalender", {})
            }
        elif scrape_type == "lms":
            lms = data.get("lms", {})
            return {
                "connected": lms.get("connected", False),
                "courses": lms.get("courses", []),
                "assignments": lms.get("assignments", [])
            }
        else:
            return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error running scraper: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run scraper: {str(e)}"
        )


def format_biodata_summary(data: Dict[str, Any]) -> str:
    """Format biodata for human-readable summary."""
    try:
        biodata = data.get("biodata", {})

        # Handle both dict and direct data
        if not isinstance(biodata, dict):
            return "Invalid biodata format"

        # Initialize info dict
        info = {}

        # Try to extract from lists first (NIM/Nama usually in List 0)
        lists = biodata.get("lists", [])
        if lists and len(lists) > 0:
            first_list = lists[0]
            if isinstance(first_list, dict):
                items = first_list.get("items", [])
                if isinstance(items, list) and len(items) > 1:
                    # Format: "244101060077 / MUHAMMAD F.Z"
                    first_item = str(items[1]).strip() if len(items) > 1 else ""
                    if "/" in first_item:
                        parts = first_item.split("/")
                        if len(parts) >= 2:
                            info["NIM"] = parts[0].strip()
                            info["Nama Mahasiswa"] = parts[1].strip()

        # Try to extract from tables
        tables = biodata.get("tables", [])
        if tables and len(tables) > 0:
            first_table = tables[0]
            if isinstance(first_table, dict):
                rows = first_table.get("rows", [])
                if rows:
                    for row in rows:
                        try:
                            if isinstance(row, list):
                                if len(row) >= 2:
                                    key = str(row[0]).strip().rstrip(":")
                                    value = str(row[1]).strip()
                                    info[key] = value
                            elif isinstance(row, dict):
                                cells = row.get("cells", [])
                                if isinstance(cells, list) and len(cells) >= 2:
                                    key = str(cells[0]).strip().rstrip(":")
                                    value = str(cells[1]).strip()
                                    info[key] = value
                        except Exception as e:
                            logger.warning(f"Error parsing row: {e}")
                            continue

        if not info:
            return "No biodata data found"

        summary = "👤 **Biodata Mahasiswa**\n"
        summary += f"- Nama: {info.get('Nama Mahasiswa', 'N/A')}\n"
        summary += f"- NIM: {info.get('NIM', 'N/A')}\n"
        summary += f"- Program Studi: {info.get('Program Studi', 'N/A')}\n"
        summary += f"- Semester: {info.get('Semester', 'N/A')}\n"

        return summary
    except Exception as e:
        logger.error(f"Error formatting biodata: {e}")
        return f"Error formatting biodata: {str(e)}"


def format_akademik_summary(data: Dict[str, Any]) -> str:
    """Format akademik data for human-readable summary."""
    try:
        summary = "📚 **Data Akademik**\n\n"

        # Kehadiran (can be dict or list)
        kehadiran = data.get("kehadiran", [])
        if isinstance(kehadiran, dict) and kehadiran:
            # Dict with semester names as keys
            semester_count = len([k for k in kehadiran.keys() if k])
            summary += f"📊 Kehadiran: {semester_count} semester\n"
            for i, sem_name in enumerate(list(kehadiran.keys())[:3]):
                summary += f"  - {sem_name}\n"
        elif isinstance(kehadiran, list) and kehadiran:
            summary += f"📊 Kehadiran: {len(kehadiran)} semester\n"
            for sem in kehadiran[:3]:  # Show first 3
                if isinstance(sem, dict):
                    semester = sem.get("semester", "N/A")
                    summary += f"  - {semester}\n"

        # Nilai
        nilai = data.get("nilai", {})
        if isinstance(nilai, dict):
            nilai_tables = nilai.get("tables", [])
            if isinstance(nilai_tables, list) and len(nilai_tables) > 0:
                first_table = nilai_tables[0]
                if isinstance(first_table, dict):
                    rows = first_table.get("rows", [])
                    if isinstance(rows, list):
                        summary += f"\n📈 Nilai: {len(rows)} mata kuliah\n"

        # Jadwal
        jadwal = data.get("jadwal", {})
        if isinstance(jadwal, dict):
            jadwal_tables = jadwal.get("tables", [])
            if isinstance(jadwal_tables, list) and len(jadwal_tables) > 0:
                first_table = jadwal_tables[0]
                if isinstance(first_table, dict):
                    rows = first_table.get("rows", [])
                    if isinstance(rows, list):
                        summary += f"\n📅 Jadwal: {len(rows)} pertemuan\n"

        # Kalender
        kalender = data.get("kalender", {})
        if isinstance(kalender, dict):
            kal_lists = kalender.get("lists", [])
            if isinstance(kal_lists, list) and len(kal_lists) > 0:
                summary += f"\n📆 Kalender: {len(kal_lists)} event akademik\n"

        return summary
    except Exception as e:
        logger.error(f"Error formatting akademik: {e}")
        return f"Error formatting akademik: {str(e)}"


def format_lms_summary(data: Dict[str, Any]) -> str:
    """Format LMS data for human-readable summary."""
    try:
        summary = "🎓 **LMS SPADA**\n\n"
        
        if not data.get("connected", False):
            return summary + "❌ Not connected to LMS"
        
        courses = data.get("courses", [])
        assignments = data.get("assignments", [])
        
        if not isinstance(courses, list):
            courses = []
        if not isinstance(assignments, list):
            assignments = []
        
        summary += f"📚 Courses: {len(courses)}\n"
        for course in courses[:5]:  # Show first 5
            if isinstance(course, dict):
                summary += f"  - {course.get('name', 'N/A')}\n"
            elif isinstance(course, str):
                summary += f"  - {course}\n"
        
        if len(courses) > 5:
            summary += f"  ... and {len(courses) - 5} more\n"
        
        summary += f"\n📝 Assignments: {len(assignments)}\n"
        for assignment in assignments[:5]:  # Show first 5
            if isinstance(assignment, dict):
                title = assignment.get("title", "N/A")
                course = assignment.get("course", "N/A")
                summary += f"  - {title} ({course})\n"
            elif isinstance(assignment, str):
                summary += f"  - {assignment}\n"
        
        if len(assignments) > 5:
            summary += f"  ... and {len(assignments) - 5} more\n"
        
        return summary
    except Exception as e:
        logger.error(f"Error formatting LMS: {e}")
        return f"Error formatting LMS: {str(e)}"


# ============================================
# API Endpoints
# ============================================

@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "Polinema API Server",
        "version": "1.0.0",
        "description": "HTTP API wrapper for Polinema SIAKAD/LMS scraper",
        "endpoints": [
            "/health",
            "/scrape/biodata",
            "/scrape/akademik",
            "/scrape/lms"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    scraper_exists = SCRAPER_PATH.exists()
    node_installed = subprocess.run(
        ["node", "--version"],
        capture_output=True
    ).returncode == 0
    
    return {
        "status": "healthy" if (scraper_exists and node_installed) else "degraded",
        "scraper_exists": scraper_exists,
        "node_installed": node_installed,
        "scraper_path": str(SCRAPER_PATH),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/scrape/biodata", response_model=BiodataResponse)
async def scrape_biodata(credentials: Optional[PolinemaCredentials] = None):
    """
    Get mahasiswa biodata from SIAKAD.
    
    Returns:
        - Nama, NIM, Program Studi
        - Status mahasiswa
        - Data kontak
    """
    try:
        data = await run_scraper("biodata", credentials)
        summary = format_biodata_summary(data)
        
        return BiodataResponse(
            status="success",
            data={
                "raw": data,
                "summary": summary
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"❌ /scrape/biodata error: {e}")
        return BiodataResponse(
            status="error",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


@app.post("/scrape/akademik", response_model=AkademikResponse)
async def scrape_akademik(credentials: Optional[PolinemaCredentials] = None):
    """
    Get akademik data from SIAKAD.
    
    Returns:
        - Kehadiran per semester
        - Nilai mata kuliah
        - Jadwal perkuliahan
        - Kalender akademik
    """
    try:
        data = await run_scraper("akademik", credentials)
        summary = format_akademik_summary(data)
        
        return AkademikResponse(
            status="success",
            data={
                "raw": data,
                "summary": summary
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"❌ /scrape/akademik error: {e}")
        return AkademikResponse(
            status="error",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


@app.post("/scrape/lms", response_model=LMSResponse)
async def scrape_lms(credentials: Optional[PolinemaCredentials] = None):
    """
    Get LMS SPADA data (courses and assignments).
    
    Returns:
        - List of enrolled courses
        - Current assignments/tugas
        - Assignment details (title, course, deadline)
    """
    try:
        data = await run_scraper("lms", credentials)
        summary = format_lms_summary(data)
        
        return LMSResponse(
            status="success",
            data={
                "raw": data,
                "summary": summary
            },
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"❌ /scrape/lms error: {e}")
        return LMSResponse(
            status="error",
            error=str(e),
            timestamp=datetime.now().isoformat()
        )


# ============================================
# Run Server
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Polinema API Server...")
    logger.info(f"📂 Scraper path: {SCRAPER_PATH}")
    logger.info(f"📂 Current dir: {CURRENT_DIR}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
