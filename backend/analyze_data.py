import json

with open('polinema-connector/polinema_complete_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 70)
print("ANALISIS DATA SCRAPING")
print("=" * 70)

print("\n📊 KEHADIRAN/PRESENSI:")
if data.get('kehadiran'):
    print("  Status: ADA DATA")
    kehadiran = data['kehadiran']
    print(f"  URL: {kehadiran.get('url')}")
    print(f"  Tables: {len(kehadiran.get('tables', []))}")
else:
    print("  Status: TIDAK ADA DATA ❌")
    print("  Alasan: Scraper gagal navigasi ke halaman Presensi")
    print("  Solusi: Perlu perbaikan selector untuk klik menu Presensi")

print("\n📅 KALENDER AKADEMIK:")
if data.get('kalender'):
    kalender = data['kalender']
    print(f"  Status: Ada data (tapi BUKAN kalender akademik!)")
    print(f"  URL: {kalender.get('url')}")
    print(f"  Problem: Scraper tidak navigasi ke halaman kalender,")
    print(f"           masih di halaman Beranda/Dashboard")
    print(f"\n  Yang ter-scrape di halaman Beranda:")
    
    for i, table in enumerate(kalender.get('tables', []), 1):
        headers = table.get('headers', [])
        rows = table.get('rows', [])
        
        print(f"\n  Table {i}:")
        print(f"    Headers: {headers}")
        print(f"    Rows: {len(rows)} items")
        
        if 'TAHUN AKADEMIK' in headers:
            print(f"    → Ini data PEMBAYARAN UKT")
            print(f"    Semester yang ada:")
            for row in rows:
                print(f"      - {row[1]}: {row[-1]}")
        
        elif 'Jurusan' in headers and 'Tanggal' in headers:
            print(f"    → Ini data PENGAMBILAN ALMAMATER per jurusan")
        
        elif 'Item' in headers:
            print(f"    → Ini data KELENGKAPAN MAHASISWA")

print("\n\n" + "=" * 70)
print("🔍 KESIMPULAN")
print("=" * 70)

print("\n❌ MASALAH:")
print("  1. Scraper gagal klik menu 'Presensi' → data kehadiran kosong")
print("  2. Scraper gagal navigasi ke 'Kalender Akademik' → masih di Beranda")
print("  3. Yang ter-scrape adalah data pembayaran UKT, bukan kalender")

print("\n✅ SOLUSI:")
print("  1. Perlu perbaikan selector untuk menu Presensi")
print("  2. Perlu navigasi langsung ke URL kalender akademik:")
print("     https://siakad.polinema.ac.id/mahasiswa/kalenderakd/index/gm/akademik")
print("  3. Untuk Presensi dengan filter semester, perlu:")
print("     - Navigasi ke: https://siakad.polinema.ac.id/mahasiswa/presensi/index/gm/akademik")
print("     - Select dropdown semester")
print("     - Klik button Filter")

print("\n📋 SEMESTER YANG TERSEDIA (dari data UKT):")
semesters = []
if data.get('kalender'):
    for table in data['kalender'].get('tables', []):
        if 'TAHUN AKADEMIK' in table.get('headers', []):
            for row in table.get('rows', []):
                semesters.append(row[1])

for sem in semesters:
    print(f"  - {sem}")

print("\n" + "=" * 70)
