import json

# Load data
with open('polinema-connector/polinema_complete_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 70)
print("📊 HASIL SCRAPING SIAKAD POLINEMA")
print("=" * 70)

print(f"\n👤 NIM: {data.get('nim', 'N/A')}")
print(f"⏰ Waktu: {data.get('timestamp', 'N/A')}")

print(f"\n📋 MENU YANG DITEMUKAN: {len(data.get('menus', []))} items")
print("\nBeberapa menu penting:")
important_menus = [m for m in data.get('menus', []) if any(x in m['text'] for x in ['Biodata', 'Presensi', 'Jadwal', 'Nilai', 'Kalender'])]
for i, menu in enumerate(important_menus[:10], 1):
    print(f"  {i}. {menu['text']}")

print("\n" + "=" * 70)
print("📊 DATA YANG BERHASIL DI-SCRAPE")
print("=" * 70)

# Kalender
if data.get('kalender'):
    kalender = data['kalender']
    print(f"\n📅 KALENDER AKADEMIK:")
    print(f"   URL: {kalender.get('url', 'N/A')}")
    print(f"   Tables: {len(kalender.get('tables', []))}")
    print(f"   Cards: {len(kalender.get('cards', []))}")
    if kalender.get('tables'):
        print("\n   Sample data:")
        for table in kalender['tables'][:1]:
            print(f"   - Headers: {table.get('headers', [])}")
            for row in table.get('rows', [])[:3]:
                print(f"   - Row: {row}")

# Nilai
if data.get('nilai'):
    nilai = data['nilai']
    print(f"\n📈 NILAI MAHASISWA:")
    print(f"   URL: {nilai.get('url', 'N/A')}")
    print(f"   Tables: {len(nilai.get('tables', []))}")
    if nilai.get('tables'):
        print("\n   Sample data:")
        for table in nilai['tables'][:1]:
            print(f"   - Headers: {table.get('headers', [])}")
            for row in table.get('rows', [])[:3]:
                print(f"   - Row: {row}")

# Jadwal
if data.get('jadwal'):
    jadwal = data['jadwal']
    print(f"\n📆 JADWAL KULIAH:")
    print(f"   URL: {jadwal.get('url', 'N/A')}")
    print(f"   Tables: {len(jadwal.get('tables', []))}")
    if jadwal.get('tables'):
        print("\n   Sample data:")
        for table in jadwal['tables'][:1]:
            print(f"   - Headers: {table.get('headers', [])}")
            for row in table.get('rows', [])[:5]:
                print(f"   - Row: {row}")

# Kehadiran
if data.get('kehadiran'):
    print(f"\n📊 KEHADIRAN: Ada data")
else:
    print(f"\n📊 KEHADIRAN: Tidak ada data (halaman tidak berhasil di-load)")

# Biodata
if data.get('biodata'):
    print(f"\n👤 BIODATA: Ada data")
else:
    print(f"\n👤 BIODATA: Tidak ada data (halaman tidak berhasil di-load)")

print("\n" + "=" * 70)
print("📸 SCREENSHOTS YANG DIHASILKAN:")
print("=" * 70)
print("""
  1. 01_after_login_*.png - Dashboard setelah login
  2. 02_biodata_*.png - Halaman biodata
  3. 03_kehadiran_*.png - Halaman kehadiran/presensi
  4. 04_kalender_*.png - Halaman kalender akademik
  5. 05_nilai_*.png - Halaman nilai/KHS
  6. 06_jadwal_*.png - Halaman jadwal kuliah
""")

print("=" * 70)
print("✅ SCRAPING SELESAI!")
print("=" * 70)
print("\nFile data: polinema-connector/polinema_complete_data.json")
print("Screenshots: polinema-connector/*.png")
