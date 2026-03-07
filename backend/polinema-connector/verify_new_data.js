/**
 * Verify New Scraped Data Quality
 * Check if kalender akademik and kehadiran data is correct
 */

const fs = require('fs');

const dataFile = 'polinema_complete_data.json';
const data = JSON.parse(fs.readFileSync(dataFile, 'utf-8'));

console.log('='.repeat(70));
console.log('VERIFIKASI DATA SCRAPING BARU');
console.log('='.repeat(70));

// Verify Biodata
console.log('\n📋 BIODATA:');
if (data.biodata) {
    console.log(`  ✓ Status: ADA DATA`);
    console.log(`  URL: ${data.biodata.url}`);
    console.log(`  Tables: ${data.biodata.tables?.length || 0}`);
    if (data.biodata.tables && data.biodata.tables.length > 0) {
        const table = data.biodata.tables[0];
        console.log(`  Rows: ${table.rows?.length || 0} data`);
    }
} else {
    console.log(`  ✗ Status: TIDAK ADA DATA`);
}

// Verify Kehadiran per semester
console.log('\n📊 KEHADIRAN/PRESENSI:');
const semesters = ['2024/2025 Ganjil', '2025/2026 Ganjil', '2025/2026 Genap'];

for (const semester of semesters) {
    console.log(`\n  Semester: ${semester}`);
    const semesterData = data.kehadiran?.[semester];
    
    if (semesterData) {
        console.log(`    ✓ Status: ADA DATA`);
        console.log(`    URL: ${semesterData.url}`);
        console.log(`    Tables: ${semesterData.tables?.length || 0}`);
        
        if (semesterData.tables && semesterData.tables.length > 0) {
            // Find attendance table (should have headers like "NO", "MATAKULIAH", etc.)
            const attendanceTable = semesterData.tables.find(t => 
                t.headers.some(h => h.includes('MATAKULIAH') || h.includes('MATA'))
            );
            
            if (attendanceTable) {
                console.log(`    Headers: ${attendanceTable.headers.join(', ')}`);
                console.log(`    Mata Kuliah: ${attendanceTable.rows?.length || 0}`);
                
                // Show sample attendance data
                if (attendanceTable.rows && attendanceTable.rows.length > 0) {
                    console.log(`\n    Sample Data (First 3):`);
                    attendanceTable.rows.slice(0, 3).forEach((row, i) => {
                        console.log(`      ${i+1}. ${row.slice(0, 4).join(' | ')}`);
                    });
                }
            } else {
                console.log(`    ⚠️  Tidak ditemukan tabel kehadiran`);
            }
        }
    } else {
        console.log(`    ✗ Status: TIDAK ADA DATA`);
    }
}

// Verify Kalender Akademik
console.log('\n\n📅 KALENDER AKADEMIK:');
if (data.kalender) {
    console.log(`  ✓ Status: ADA DATA`);
    console.log(`  URL: ${data.kalender.url}`);
    
    // Check if URL is correct (not beranda)
    if (data.kalender.url.includes('kalenderakd')) {
        console.log(`  ✓ URL BENAR - Halaman Kalender Akademik`);
    } else if (data.kalender.url.includes('beranda')) {
        console.log(`  ✗ URL SALAH - Masih di Beranda!`);
    }
    
    console.log(`  Tables: ${data.kalender.tables?.length || 0}`);
    console.log(`  Lists: ${data.kalender.lists?.length || 0}`);
    
    // Show what's in the calendar page
    if (data.kalender.lists && data.kalender.lists.length > 0) {
        console.log(`\n  Calendar Items Found:`);
        const calendarList = data.kalender.lists[0];
        if (calendarList.items && calendarList.items.length > 0) {
            calendarList.items.slice(0, 10).forEach((item, i) => {
                console.log(`    ${i+1}. ${item}`);
            });
            if (calendarList.items.length > 10) {
                console.log(`    ... dan ${calendarList.items.length - 10} item lainnya`);
            }
        }
    }
    
    if (data.kalender.tables && data.kalender.tables.length > 0) {
        console.log(`\n  ⚠️  Ada tables (seharusnya kalender tidak punya table):`);
        data.kalender.tables.forEach((table, i) => {
            console.log(`    Table ${i+1}: ${table.headers.join(', ')}`);
        });
    }
} else {
    console.log(`  ✗ Status: TIDAK ADA DATA`);
}

// Verify Jadwal
console.log('\n\n📆 JADWAL PERKULIAHAN:');
if (data.jadwal) {
    console.log(`  ✓ Status: ADA DATA`);
    console.log(`  URL: ${data.jadwal.url}`);
    console.log(`  Tables: ${data.jadwal.tables?.length || 0}`);
    
    if (data.jadwal.tables && data.jadwal.tables.length > 0) {
        const scheduleTable = data.jadwal.tables.find(t => 
            t.headers.some(h => h.includes('HARI') || h.includes('JAM'))
        );
        
        if (scheduleTable) {
            console.log(`  Headers: ${scheduleTable.headers.join(', ')}`);
            console.log(`  Jadwal: ${scheduleTable.rows?.length || 0} pertemuan`);
        }
    }
} else {
    console.log(`  ✗ Status: TIDAK ADA DATA`);
}

// Verify Nilai
console.log('\n\n📈 NILAI MAHASISWA:');
if (data.nilai) {
    console.log(`  ✓ Status: ADA DATA`);
    console.log(`  URL: ${data.nilai.url}`);
    console.log(`  Tables: ${data.nilai.tables?.length || 0}`);
    
    if (data.nilai.tables && data.nilai.tables.length > 0) {
        const gradeTable = data.nilai.tables.find(t => 
            t.headers.some(h => h.includes('NILAI') || h.includes('GRADE'))
        );
        
        if (gradeTable) {
            console.log(`  Headers: ${gradeTable.headers.join(', ')}`);
            console.log(`  Mata Kuliah: ${gradeTable.rows?.length || 0}`);
        }
    }
} else {
    console.log(`  ✗ Status: TIDAK ADA DATA`);
}

console.log('\n' + '='.repeat(70));
console.log('🎯 KESIMPULAN');
console.log('='.repeat(70));

const checks = {
    biodata: !!data.biodata,
    kehadiran_2024_ganjil: !!data.kehadiran?.['2024/2025 Ganjil'],
    kehadiran_2025_ganjil: !!data.kehadiran?.['2025/2026 Ganjil'],
    kehadiran_2025_genap: !!data.kehadiran?.['2025/2026 Genap'],
    kalender_url_correct: data.kalender?.url?.includes('kalenderakd'),
    kalender_not_beranda: !data.kalender?.url?.includes('beranda'),
    jadwal: !!data.jadwal,
    nilai: !!data.nilai
};

const passed = Object.values(checks).filter(v => v).length;
const total = Object.keys(checks).length;

console.log(`\n✓ ${passed}/${total} checks passed\n`);

Object.entries(checks).forEach(([key, value]) => {
    console.log(`  ${value ? '✓' : '✗'} ${key.replace(/_/g, ' ')}`);
});

if (passed === total) {
    console.log('\n🎉 SEMUA DATA BERHASIL DI-SCRAPE DENGAN BENAR!');
} else {
    console.log(`\n⚠️  Masih ada ${total - passed} data yang perlu diperbaiki`);
}

console.log('='.repeat(70));
