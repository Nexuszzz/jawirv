"""
JAWIR Tools - Polinema SIAKAD Integration
Function tools untuk AI Assistant
"""

import requests
from typing import Dict, Any, Optional

POLINEMA_API_BASE = "http://localhost:8000"


class PolinemaTools:
    """Tools untuk mengakses data SIAKAD Polinema"""
    
    def __init__(self, base_url: str = POLINEMA_API_BASE):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _call_api(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Internal API caller"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url, **kwargs)
            elif method == "POST":
                response = self.session.post(url, **kwargs)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_biodata_mahasiswa(self) -> Dict[str, Any]:
        """
        Mengambil biodata mahasiswa dari SIAKAD
        
        Returns:
            Dict dengan data biodata mahasiswa (NIM, nama, prodi, dll)
        """
        result = self._call_api("/api/biodata")
        if result.get("success"):
            return self._format_biodata(result["data"])
        return result
    
    def get_presensi(self, semester: str = "2025/2026 Genap") -> Dict[str, Any]:
        """
        Mengambil data presensi/kehadiran mahasiswa
        
        Args:
            semester: Semester yang ingin dilihat (default: semester aktif)
        
        Returns:
            Dict dengan data kehadiran per mata kuliah
        """
        result = self._call_api(f"/api/presensi?semester={semester}")
        if result.get("success"):
            return self._format_presensi(result["data"])
        return result
    
    def get_kalender_akademik(self) -> Dict[str, Any]:
        """
        Mengambil kalender akademik
        
        Returns:
            Dict dengan daftar event/kegiatan akademik beserta tanggalnya
        """
        result = self._call_api("/api/kalender")
        if result.get("success"):
            return self._format_kalender(result["data"])
        return result
    
    def get_jadwal_kuliah(self) -> Dict[str, Any]:
        """
        Mengambil jadwal perkuliahan
        
        Returns:
            Dict dengan jadwal kuliah (hari, jam, mata kuliah, ruangan, dosen)
        """
        result = self._call_api("/api/jadwal")
        if result.get("success"):
            return self._format_jadwal(result["data"])
        return result
    
    def get_nilai(self) -> Dict[str, Any]:
        """
        Mengambil nilai/KHS mahasiswa
        
        Returns:
            Dict dengan nilai per mata kuliah dan IPK
        """
        result = self._call_api("/api/nilai")
        if result.get("success"):
            return self._format_nilai(result["data"])
        return result
    
    def get_all_data(self) -> Dict[str, Any]:
        """
        Mengambil semua data sekaligus
        
        Returns:
            Dict dengan semua data (biodata, presensi, kalender, jadwal, nilai)
        """
        return self._call_api("/api/all")
    
    # Formatter methods
    def _format_biodata(self, data: Dict) -> Dict:
        """Format biodata untuk AI"""
        if not data or not data.get("tables"):
            return {"error": "No biodata found"}
        
        # Extract from first table
        table = data["tables"][0]
        biodata = {}
        
        for row in table.get("rows", []):
            if len(row) >= 2:
                key = row[0].strip()
                value = row[1].strip()
                biodata[key] = value
        
        return {
            "success": True,
            "biodata": biodata,
            "raw_tables": data["tables"]
        }
    
    def _format_presensi(self, data: Dict) -> Dict:
        """Format presensi untuk AI"""
        if not data:
            return {"error": "No presensi data found"}
        
        # New format from extract_presensi_table
        if data.get("mata_kuliah") is not None:
            mata_kuliah = data.get("mata_kuliah", [])
            summary = data.get("summary", {})
            
            # Format mata kuliah data
            matakuliah_list = []
            for mk in mata_kuliah:
                matakuliah_list.append({
                    "no": mk.get("no", ""),
                    "mata_kuliah": mk.get("nama", ""),
                    "pertemuan": mk.get("pertemuan", ""),
                    "tanggal": mk.get("tanggal", ""),
                    "alpha": mk.get("alpha", "0"),
                    "izin": mk.get("izin", "0"),
                    "sakit": mk.get("sakit", "0")
                })
            
            return {
                "success": True,
                "semester": data.get("semester", ""),
                "matakuliah": matakuliah_list,
                "total_mk": len(matakuliah_list),
                "summary": {
                    "total_alpha": summary.get("total_alpha", "0"),
                    "total_izin": summary.get("total_izin", "0"),
                    "total_sakit": summary.get("total_sakit", "0"),
                    "total_ais": summary.get("total_ais", "")
                },
                "url": data.get("url", "")
            }
        
        # Old format fallback - from extract_page_data
        if not data.get("tables"):
            return {"error": "No presensi data found", "raw": data}
        
        # Find presensi table
        for table in data["tables"]:
            headers = [h.lower() for h in table.get("headers", [])]
            if any(x in ' '.join(headers) for x in ['mata kuliah', 'hadir', 'alpha']):
                matakuliah_list = []
                
                for row in table.get("rows", []):
                    if len(row) >= 4:
                        mk_data = {
                            "mata_kuliah": row[0],
                            "hadir": row[1],
                            "izin": row[2] if len(row) > 2 else "0",
                            "alpha": row[3] if len(row) > 3 else "0",
                            "persentase": row[4] if len(row) > 4 else "0%"
                        }
                        matakuliah_list.append(mk_data)
                
                return {
                    "success": True,
                    "matakuliah": matakuliah_list,
                    "total_mk": len(matakuliah_list)
                }
        
        return {"error": "Presensi table not found", "raw": data}
    
    def _format_kalender(self, data: Dict) -> Dict:
        """Format kalender untuk AI"""
        if not data:
            return {"error": "No kalender data found"}
        
        events = []
        
        # Check if there's an embedded image/PDF
        if data.get("cards"):
            for card in data["cards"]:
                if "kalender" in card.get("content", "").lower():
                    return {
                        "success": True,
                        "type": "embedded",
                        "message": "Kalender akademik tersedia dalam bentuk gambar/PDF",
                        "url": data.get("url")
                    }
        
        # Try to extract from tables
        for table in data.get("tables", []):
            for row in table.get("rows", []):
                if len(row) >= 2:
                    events.append({
                        "tanggal": row[0],
                        "kegiatan": row[1],
                        "keterangan": row[2] if len(row) > 2 else ""
                    })
        
        return {
            "success": True,
            "events": events,
            "url": data.get("url")
        }
    
    def _format_jadwal(self, data: Dict) -> Dict:
        """Format jadwal untuk AI"""
        if not data:
            return {"error": "No jadwal data found"}
        
        # New format from extract_jadwal_table
        if data.get("mata_kuliah") is not None:
            mata_kuliah = data.get("mata_kuliah", [])
            jadwal_per_hari = data.get("jadwal_per_hari", {})
            tahun_akademik = data.get("tahun_akademik", "")
            kelas = data.get("kelas", "")
            
            # Check if jadwal hari/jam sudah diisi atau belum
            jadwal_lengkap = any(mk.get("hari") and mk.get("jam") for mk in mata_kuliah)
            
            return {
                "success": True,
                "tahun_akademik": tahun_akademik,
                "kelas": kelas,
                "jadwal": mata_kuliah,
                "jadwal_per_hari": jadwal_per_hari,
                "total": len(mata_kuliah),
                "jadwal_lengkap": jadwal_lengkap,
                "note": "" if jadwal_lengkap else "Jadwal hari dan jam belum diinput oleh admin. Hanya daftar mata kuliah yang tersedia.",
                "url": data.get("url", "")
            }
        
        # Old format fallback - from extract_page_data
        if not data.get("tables"):
            return {"error": "No jadwal data found", "raw": data}
        
        jadwal_list = []
        
        for table in data["tables"]:
            for row in table.get("rows", []):
                if len(row) >= 3:
                    jadwal_item = {
                        "hari": row[0] if len(row) > 0 else "",
                        "jam": row[1] if len(row) > 1 else "",
                        "kode_mk": row[2] if len(row) > 2 else "",
                        "mata_kuliah": row[3] if len(row) > 3 else "",
                        "dosen": row[4] if len(row) > 4 else "",
                        "ruangan": row[5] if len(row) > 5 else ""
                    }
                    jadwal_list.append(jadwal_item)
        
        return {
            "success": True,
            "jadwal": jadwal_list,
            "total": len(jadwal_list)
        }
    
    def _format_nilai(self, data: Dict) -> Dict:
        """Format nilai untuk AI"""
        if not data or not data.get("tables"):
            return {"error": "No nilai data found"}
        
        nilai_list = []
        ipk = None
        
        for table in data["tables"]:
            headers = table.get("headers", [])
            
            # Look for IPK/IPS info in cards
            for card in data.get("cards", []):
                content = card.get("content", "")
                if "ipk" in content.lower() or "ips" in content.lower():
                    # Extract IPK value
                    import re
                    match = re.search(r'ipk.*?(\d+\.\d+)', content.lower())
                    if match:
                        ipk = float(match.group(1))
            
            # Extract grades from table
            for row in table.get("rows", []):
                if len(row) >= 3:
                    nilai_item = {
                        "kode": row[0] if len(row) > 0 else "",
                        "mata_kuliah": row[1] if len(row) > 1 else "",
                        "sks": row[2] if len(row) > 2 else "",
                        "nilai": row[3] if len(row) > 3 else ""
                    }
                    nilai_list.append(nilai_item)
        
        return {
            "success": True,
            "nilai": nilai_list,
            "ipk": ipk,
            "total_mk": len(nilai_list)
        }


# Tool definitions for OpenAI/Gemini function calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_biodata_mahasiswa",
            "description": "Mendapatkan biodata mahasiswa dari SIAKAD (NIM, nama, prodi, jurusan, dll)",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_presensi",
            "description": "Mendapatkan data kehadiran/presensi mahasiswa per mata kuliah",
            "parameters": {
                "type": "object",
                "properties": {
                    "semester": {
                        "type": "string",
                        "description": "Semester (contoh: '2024/2025 Ganjil')",
                        "default": "2024/2025 Ganjil"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_kalender_akademik",
            "description": "Mendapatkan kalender akademik dengan jadwal kegiatan kampus",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_jadwal_kuliah",
            "description": "Mendapatkan jadwal perkuliahan (hari, jam, mata kuliah, ruangan, dosen)",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_nilai",
            "description": "Mendapatkan nilai/KHS mahasiswa dengan IPK",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]


# Example usage
if __name__ == "__main__":
    tools = PolinemaTools()
    
    print("Testing Polinema Tools...")
    print("\n1. Biodata:")
    print(tools.get_biodata_mahasiswa())
    
    print("\n2. Presensi:")
    print(tools.get_presensi())
    
    print("\n3. Kalender:")
    print(tools.get_kalender_akademik())
