"""Test format functions dengan mock data."""
import json
import sys

# Mock data matching scraper output format
mock_biodata = {
    "biodata": {
        "tables": [{
            "index": 0,
            "headers": [],
            "rows": [
                ["Nama Mahasiswa", "AKHMAD HISYAM ALBAB"],
                ["NIM", "244101060077"],
                ["Program Studi", "D4 Teknik Informatika"],
                ["Semester", "3"]
            ]
        }]
    }
}

mock_akademik = {
    "kehadiran": [
        {"semester": "Semester 1"},
        {"semester": "Semester 2"},
        {"semester": "Semester 3"}
    ],
    "nilai": {
        "tables": [{
            "rows": [
                ["Matkul 1", "A"],
                ["Matkul 2", "B+"],
                ["Matkul 3", "A-"]
            ]
        }]
    },
    "jadwal": {
        "tables": [{
            "rows": [
                ["Senin", "08:00", "Pemrograman Web"],
                ["Selasa", "10:00", "Basis Data"]
            ]
        }]
    },
    "kalender": {
        "lists": [
            ["Event 1", "Event 2", "Event 3"]
        ]
    }
}

mock_lms = {
    "connected": True,
    "courses": [
        {"name": "Course 1"},
        {"name": "Course 2"}
    ],
    "assignments": [
        {"title": "Tugas 1", "course": "Course 1"},
        {"title": "Tugas 2", "course": "Course 2"}
    ]
}

# Import format functions from server
sys.path.insert(0, '.')
from polinema_api_server import format_biodata_summary, format_akademik_summary, format_lms_summary

print("=" * 60)
print("TEST FORMAT FUNCTIONS WITH MOCK DATA")
print("=" * 60)

print("\n1. Testing format_biodata_summary:")
print("-" * 60)
try:
    result = format_biodata_summary(mock_biodata)
    print(result)
    print("✅ SUCCESS - No errors")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing format_akademik_summary:")
print("-" * 60)
try:
    result = format_akademik_summary(mock_akademik)
    print(result)
    print("✅ SUCCESS - No errors")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testing format_lms_summary:")
print("-" * 60)
try:
    result = format_lms_summary(mock_lms)
    print(result)
    print("✅ SUCCESS - No errors")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
