"""
Polinema SIAKAD Scraper - Python Version
Integration with JAWIR AI Assistant
"""

from playwright.sync_api import sync_playwright, Page, Browser
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

class PolinemaScraper:
    """Scraper untuk mengambil data dari SIAKAD Polinema"""
    
    def __init__(self, nim: str, password: str, headless: bool = False):
        self.nim = nim
        self.password = password
        self.headless = headless
        self.siakad_url = "https://siakad.polinema.ac.id"
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None  # Playwright instance for cleanup
        
    def __enter__(self):
        """Context manager entry"""
        self.init()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        
    def init(self):
        """Initialize browser"""
        print("🚀 Launching browser...")
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=50  # Reduced slowmo for faster loading
        )
        context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            ignore_https_errors=True  # Ignore SSL certificate errors
        )
        # Set longer default timeout
        context.set_default_timeout(60000)
        self.page = context.new_page()
        
        print("✓ Browser ready")
        
    def login(self, max_retries: int = 3) -> bool:
        """Login to SIAKAD with retry logic"""
        print("\n📝 Logging into SIAKAD...")
        
        for attempt in range(max_retries):
            try:
                print(f"  Attempt {attempt + 1}/{max_retries}...")
                
                # Navigate to login page - use domcontentloaded for faster loading
                self.page.goto(self.siakad_url, wait_until='domcontentloaded', timeout=30000)
                time.sleep(2)
                
                # Check if already logged in
                if 'beranda' in self.page.url or 'dashboard' in self.page.url or 'mahasiswa' in self.page.url:
                    print("✓ Already logged in!")
                    return True
                
                # Wait for login form to be visible
                self.page.wait_for_selector('input[name="username"], input[name="nim"], #username, #nim', timeout=15000)
                
                # Multiple selectors for username field
                username_selectors = [
                    'input[name="username"]',
                    'input[name="nim"]',
                    '#username',
                    '#nim',
                    'input[type="text"]'
                ]
                
                username_filled = False
                for selector in username_selectors:
                    try:
                        locator = self.page.locator(selector)
                        if locator.count() > 0 and locator.first.is_visible():
                            locator.first.fill(self.nim)
                            username_filled = True
                            print(f"    ✓ Username filled using: {selector}")
                            break
                    except:
                        continue
                
                if not username_filled:
                    print("    ✗ Could not find username field")
                    self.screenshot(f'login_no_username_{attempt}')
                    continue
                
                # Multiple selectors for password field
                password_selectors = [
                    'input[name="password"]',
                    '#password',
                    'input[type="password"]'
                ]
                
                password_filled = False
                for selector in password_selectors:
                    try:
                        locator = self.page.locator(selector)
                        if locator.count() > 0 and locator.first.is_visible():
                            locator.first.fill(self.password)
                            password_filled = True
                            print(f"    ✓ Password filled using: {selector}")
                            break
                    except:
                        continue
                
                if not password_filled:
                    print("    ✗ Could not find password field")
                    self.screenshot(f'login_no_password_{attempt}')
                    continue
                
                # Small delay before clicking
                time.sleep(0.5)
                
                # Multiple selectors for submit button
                submit_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Masuk")',
                    'button:has-text("Sign")',
                    '#btn-login',
                    '.btn-login',
                    'form button'
                ]
                
                submit_clicked = False
                for selector in submit_selectors:
                    try:
                        locator = self.page.locator(selector)
                        if locator.count() > 0 and locator.first.is_visible():
                            locator.first.click()
                            submit_clicked = True
                            print(f"    ✓ Submit clicked using: {selector}")
                            break
                    except:
                        continue
                
                if not submit_clicked:
                    print("    ✗ Could not find submit button, trying Enter key...")
                    self.page.keyboard.press('Enter')
                
                # Wait for navigation to complete (check multiple possible URLs)
                try:
                    self.page.wait_for_url(
                        lambda url: 'beranda' in url or 'dashboard' in url or 'mahasiswa' in url,
                        timeout=20000
                    )
                except:
                    pass  # May have already navigated
                
                time.sleep(2)
                
                # Verify login success
                current_url = self.page.url
                if 'beranda' in current_url or 'dashboard' in current_url or 'mahasiswa' in current_url:
                    print(f"✓ Login successful!")
                    print(f"  URL: {current_url}")
                    return True
                else:
                    print(f"    URL after login: {current_url}")
                    # Check for error messages
                    error_msg = self.page.locator('.alert-danger, .error, .warning').first
                    if error_msg.count() > 0:
                        try:
                            print(f"    Error: {error_msg.text_content()}")
                        except:
                            pass
                    self.screenshot(f'login_failed_{attempt}')
                
            except Exception as e:
                print(f"    ✗ Attempt {attempt + 1} error: {e}")
                self.screenshot(f'login_error_{attempt}')
                time.sleep(2)
                continue
        
        print(f"✗ Login failed after {max_retries} attempts")
        return False
    
    def navigate_to_url(self, path: str, wait_strategy: str = 'domcontentloaded') -> bool:
        """Navigate directly to URL path"""
        url = f"{self.siakad_url}{path}"
        print(f"\n🎯 Navigating to: {url}")
        
        try:
            self.page.goto(url, wait_until=wait_strategy, timeout=30000)
            time.sleep(2)
            print(f"  ✓ Current URL: {self.page.url}")
            
            # Check if redirected to login
            if 'login' in self.page.url.lower() or 'auth' in self.page.url.lower():
                print("  ⚠ Redirected to login, session may have expired")
                return False
            
            return True
        except Exception as e:
            print(f"  ✗ Navigation error: {e}")
            return False
    
    def navigate_to_menu(self, search_terms: List[str]) -> bool:
        """Navigate to menu by searching for text"""
        print(f"\n🎯 Looking for: {' or '.join(search_terms)}...")
        
        for term in search_terms:
            try:
                locator = self.page.locator(f'a:has-text("{term}"), button:has-text("{term}")')
                if locator.count() > 0:
                    print(f"  Found '{term}', clicking...")
                    locator.first.click()
                    time.sleep(2)
                    print(f"  ✓ Navigated to: {self.page.url}")
                    return True
            except Exception as e:
                continue
        
        print("  ✗ Menu not found")
        return False
    
    def extract_page_data(self) -> Dict[str, Any]:
        """Extract data from current page"""
        print("\n📦 Extracting page data...")
        time.sleep(1)
        
        data = self.page.evaluate("""() => {
            const result = {
                url: window.location.href,
                title: document.title,
                tables: [],
                cards: [],
                lists: []
            };
            
            // Extract tables
            document.querySelectorAll('table').forEach((table, idx) => {
                const tableData = {
                    index: idx,
                    headers: [],
                    rows: []
                };
                
                // Headers
                table.querySelectorAll('thead th, thead td').forEach(th => {
                    tableData.headers.push(th.innerText.trim());
                });
                
                // Rows
                table.querySelectorAll('tbody tr').forEach(tr => {
                    const row = [];
                    tr.querySelectorAll('td').forEach(td => {
                        row.push(td.innerText.trim());
                    });
                    if (row.length > 0) {
                        tableData.rows.push(row);
                    }
                });
                
                if (tableData.rows.length > 0 || tableData.headers.length > 0) {
                    result.tables.push(tableData);
                }
            });
            
            // Extract cards
            document.querySelectorAll('.card, .box, [class*="card"], [class*="info"]').forEach((card, idx) => {
                const text = card.innerText.trim();
                if (text && text.length < 500) {
                    result.cards.push({
                        index: idx,
                        class: card.className,
                        content: text
                    });
                }
            });
            
            // Extract lists
            document.querySelectorAll('ul, ol').forEach((list, idx) => {
                const items = Array.from(list.querySelectorAll('li')).map(li => li.innerText.trim());
                if (items.length > 0) {
                    result.lists.push({index: idx, items: items});
                }
            });
            
            return result;
        }""")
        
        print(f"✓ Extracted - Tables: {len(data['tables'])}, Cards: {len(data['cards'])}, Lists: {len(data['lists'])}")
        return data
    
    def get_biodata(self) -> Optional[Dict]:
        """Get biodata mahasiswa"""
        print("\n📋 === BIODATA MAHASISWA ===")
        if self.navigate_to_url('/mahasiswa/biodata/index/gm/general'):
            return self.extract_page_data()
        return None
    
    def get_presensi(self, semester: str = "2025/2026 Genap") -> Optional[Dict]:
        """Get data presensi/kehadiran dengan filter semester"""
        print(f"\n📊 === PRESENSI MAHASISWA ({semester}) ===")
        
        if not self.navigate_to_url('/mahasiswa/presensi/index/gm/akademik'):
            return None
        
        # Wait for page to load completely
        time.sleep(3)
        
        # Select semester and click Filter
        try:
            print(f"  🔄 Selecting semester: {semester}")
            
            # Find and select semester dropdown - try multiple approaches
            dropdown = None
            dropdown_selectors = [
                'select[name*="semester"]',
                'select[id*="semester"]', 
                'select.form-control',
                'select'
            ]
            
            for selector in dropdown_selectors:
                try:
                    dropdown = self.page.locator(selector).first
                    if dropdown.is_visible():
                        break
                except:
                    continue
            
            if dropdown:
                # Try to select by label first, then by partial match
                try:
                    dropdown.select_option(label=semester)
                except:
                    # Get all options and find matching one
                    options = dropdown.locator('option').all_text_contents()
                    print(f"  Available semesters: {options}")
                    for opt in options:
                        if semester in opt or opt in semester:
                            dropdown.select_option(label=opt)
                            print(f"  ✓ Selected: {opt}")
                            break
                
                time.sleep(1)
            else:
                print("  ⚠️ Semester dropdown not found")
            
            # Click Filter button - more robust locator
            print("  🔍 Looking for Filter button...")
            filter_selectors = [
                'button:has-text("Filter")',
                'button.btn-info:has-text("Filter")',
                'button[type="submit"]:has-text("Filter")',
                'input[type="submit"][value*="Filter"]',
                'button.btn:has-text("Filter")',
                '.btn-info',  # The teal button in the screenshot
            ]
            
            filter_clicked = False
            for selector in filter_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible():
                        btn.click()
                        print(f"  ✓ Clicked filter button via: {selector}")
                        filter_clicked = True
                        break
                except Exception as e:
                    continue
            
            if not filter_clicked:
                print("  ⚠️ Filter button not found, trying JavaScript click...")
                self.page.evaluate("""() => {
                    const btns = document.querySelectorAll('button, input[type="submit"]');
                    for (const btn of btns) {
                        if (btn.textContent.toLowerCase().includes('filter') || 
                            btn.value?.toLowerCase().includes('filter')) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }""")
            
            print("  ⏳ Waiting for data to load...")
            
            # Wait for table to update - wait for network idle or specific element
            try:
                self.page.wait_for_load_state('networkidle', timeout=10000)
            except:
                pass
            
            time.sleep(3)
            
        except Exception as e:
            print(f"  ⚠️ Filter error: {e}")
            print("  Continuing with current data...")
        
        # Extract presensi specific data
        presensi_data = self.extract_presensi_table()
        
        return presensi_data
    
    def extract_presensi_table(self) -> Dict[str, Any]:
        """Extract presensi table data specifically"""
        print("  📦 Extracting presensi table...")
        
        data = self.page.evaluate("""() => {
            const result = {
                url: window.location.href,
                semester: '',
                mata_kuliah: [],
                summary: {
                    total_alpha: 0,
                    total_izin: 0,
                    total_sakit: 0,
                    total_ais: ''
                },
                raw_tables: []
            };
            
            // Get selected semester
            const semesterSelect = document.querySelector('select');
            if (semesterSelect) {
                result.semester = semesterSelect.options[semesterSelect.selectedIndex]?.text || '';
            }
            
            // Find the main presensi table
            const tables = document.querySelectorAll('table');
            
            tables.forEach((table, tableIdx) => {
                const headers = [];
                const rows = [];
                
                // Get headers
                table.querySelectorAll('thead th, thead td, tr:first-child th, tr:first-child td').forEach(th => {
                    headers.push(th.innerText.trim().toUpperCase());
                });
                
                // Check if this is the presensi table (has MATA KULIAH, ALPHA, IJIN, SAKIT columns)
                const isPresensiTable = headers.some(h => 
                    h.includes('MATA KULIAH') || h.includes('ALPHA') || h.includes('IJIN') || h.includes('SAKIT')
                );
                
                // Get all rows
                table.querySelectorAll('tbody tr, tr').forEach((tr, rowIdx) => {
                    // Skip header row if in tbody
                    if (rowIdx === 0 && tr.querySelector('th')) return;
                    
                    const cells = [];
                    tr.querySelectorAll('td').forEach(td => {
                        cells.push(td.innerText.trim());
                    });
                    
                    if (cells.length > 0) {
                        rows.push(cells);
                        
                        // Parse data rows for presensi table
                        if (isPresensiTable && cells.length >= 6) {
                            // Check if it's a data row (has a number in first column)
                            if (/^\\d+$/.test(cells[0])) {
                                result.mata_kuliah.push({
                                    no: cells[0],
                                    nama: cells[1] || '',
                                    pertemuan: cells[2] || '',
                                    tanggal: cells[3] || '',
                                    alpha: cells[4] || '0',
                                    izin: cells[5] || '0',
                                    sakit: cells[6] || '0'
                                });
                            }
                            // Check for summary row (Jumlah or Total)
                            else if (cells.some(c => c.toLowerCase().includes('jumlah'))) {
                                // Summary row with totals
                                const alphaIdx = headers.findIndex(h => h.includes('ALPHA'));
                                const izinIdx = headers.findIndex(h => h.includes('IJIN') || h.includes('IZIN'));
                                const sakitIdx = headers.findIndex(h => h.includes('SAKIT'));
                                
                                if (alphaIdx >= 0) result.summary.total_alpha = cells[alphaIdx] || '0';
                                if (izinIdx >= 0) result.summary.total_izin = cells[izinIdx] || '0';
                                if (sakitIdx >= 0) result.summary.total_sakit = cells[sakitIdx] || '0';
                            }
                            else if (cells.some(c => c.toLowerCase().includes('total ais'))) {
                                result.summary.total_ais = cells[cells.length - 1] || '';
                            }
                        }
                    }
                });
                
                result.raw_tables.push({
                    index: tableIdx,
                    headers: headers,
                    rows: rows,
                    isPresensiTable: isPresensiTable
                });
            });
            
            return result;
        }""")
        
        print(f"  ✓ Found {len(data.get('mata_kuliah', []))} mata kuliah records")
        print(f"  ✓ Semester: {data.get('semester', 'Unknown')}")
        print(f"  ✓ Summary - Alpha: {data['summary'].get('total_alpha', 0)}, Izin: {data['summary'].get('total_izin', 0)}, Sakit: {data['summary'].get('total_sakit', 0)}")
        
        return data
    
    def get_kalender(self) -> Optional[Dict]:
        """Get kalender akademik"""
        print("\n📅 === KALENDER AKADEMIK ===")
        if self.navigate_to_url('/mahasiswa/kalenderakd/index/gm/akademik'):
            return self.extract_page_data()
        return None
    
    def get_jadwal(self) -> Optional[Dict]:
        """Get jadwal perkuliahan dengan parsing yang lebih robust"""
        print("\n📆 === JADWAL PERKULIAHAN ===")
        if not self.navigate_to_url('/mahasiswa/jadwal/index/gm/akademik'):
            return None
        
        # Wait for page to load
        time.sleep(3)
        
        # Extract jadwal specific data
        return self.extract_jadwal_table()
    
    def extract_jadwal_table(self) -> Dict[str, Any]:
        """Extract jadwal table data specifically"""
        print("  📦 Extracting jadwal table...")
        
        data = self.page.evaluate("""() => {
            const result = {
                url: window.location.href,
                tahun_akademik: '',
                kelas: '',
                jadwal_per_hari: {},
                mata_kuliah: [],
                raw_tables: []
            };
            
            const hari = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
            hari.forEach(h => result.jadwal_per_hari[h] = []);
            
            // Try to get academic year and class info from page
            const pageText = document.body.innerText;
            const tahunMatch = pageText.match(/Tahun Akademik\\s*:\\s*([\\d\\/]+\\s+\\w+)/i);
            if (tahunMatch) result.tahun_akademik = tahunMatch[1].trim();
            
            const kelasMatch = pageText.match(/Kelas\\s*:\\s*(\\w+)/i);
            if (kelasMatch) result.kelas = kelasMatch[1].trim();
            
            // Find all tables
            const tables = document.querySelectorAll('table');
            
            tables.forEach((table, tableIdx) => {
                const headers = [];
                const rows = [];
                
                // Get headers from thead or first row
                const headerCells = table.querySelectorAll('thead th, thead td');
                if (headerCells.length > 0) {
                    headerCells.forEach(th => headers.push(th.innerText.trim().toUpperCase()));
                } else {
                    // Try first row as header
                    const firstRow = table.querySelector('tr');
                    if (firstRow) {
                        firstRow.querySelectorAll('th, td').forEach(th => headers.push(th.innerText.trim().toUpperCase()));
                    }
                }
                
                // Check if this is the jadwal table - look for KODE MK or MATA KULIAH
                const isJadwalTable = headers.some(h => 
                    h.includes('KODE MK') || h.includes('MATA KULIAH') || h.includes('DOSEN') || 
                    (h.includes('HARI') && h.includes('JAM'))
                ) || headers.length >= 5;
                
                // Get header indices for mapping
                const headerMap = {};
                headers.forEach((h, idx) => {
                    if (h.includes('NO') && !h.includes('PASSCODE')) headerMap.no = idx;
                    if (h.includes('HARI')) headerMap.hari = idx;
                    if (h.includes('JAM')) headerMap.jam = idx;
                    if (h.includes('KODE')) headerMap.kode_mk = idx;
                    if (h.includes('MATA KULIAH')) headerMap.mata_kuliah = idx;
                    if (h.includes('DOSEN')) headerMap.dosen = idx;
                    if (h.includes('RUANG') || h.includes('ROOM')) headerMap.ruangan = idx;
                    if (h.includes('IDZOOM') || h.includes('ZOOM')) headerMap.idzoom = idx;
                    if (h.includes('PASSCODE')) headerMap.passcode = idx;
                    if (h.includes('LINK') || h.includes('URL')) headerMap.link = idx;
                });
                
                // Get all body rows
                const bodyRows = table.querySelectorAll('tbody tr');
                const startIdx = bodyRows.length > 0 ? 0 : 1; // Skip first row if no tbody
                const allRows = bodyRows.length > 0 ? bodyRows : table.querySelectorAll('tr');
                
                allRows.forEach((tr, rowIdx) => {
                    if (bodyRows.length === 0 && rowIdx === 0) return; // Skip header row
                    
                    const cells = [];
                    tr.querySelectorAll('td').forEach(td => {
                        cells.push(td.innerText.trim());
                    });
                    
                    if (cells.length > 0) {
                        rows.push(cells);
                    }
                });
                
                result.raw_tables.push({
                    index: tableIdx,
                    headers: headers,
                    headerMap: headerMap,
                    rows: rows,
                    isJadwalTable: isJadwalTable,
                    rowCount: rows.length
                });
                
                // Parse jadwal if this is the jadwal table
                if (isJadwalTable && rows.length > 0) {
                    let currentHari = '';
                    
                    rows.forEach((row, ridx) => {
                        // Map cells based on header indices
                        let entry = {
                            no: '',
                            hari: '',
                            jam: '',
                            kode_mk: '',
                            mata_kuliah: '',
                            dosen: '',
                            ruangan: '',
                            idzoom: '',
                            passcode: '',
                            link: ''
                        };
                        
                        // Use header mapping if available
                        if (Object.keys(headerMap).length >= 2) {
                            entry.no = headerMap.no !== undefined ? row[headerMap.no] || '' : '';
                            entry.hari = headerMap.hari !== undefined ? row[headerMap.hari] || '' : '';
                            entry.jam = headerMap.jam !== undefined ? row[headerMap.jam] || '' : '';
                            entry.kode_mk = headerMap.kode_mk !== undefined ? row[headerMap.kode_mk] || '' : '';
                            entry.mata_kuliah = headerMap.mata_kuliah !== undefined ? row[headerMap.mata_kuliah] || '' : '';
                            entry.dosen = headerMap.dosen !== undefined ? row[headerMap.dosen] || '' : '';
                            entry.ruangan = headerMap.ruangan !== undefined ? row[headerMap.ruangan] || '' : '';
                            entry.idzoom = headerMap.idzoom !== undefined ? row[headerMap.idzoom] || '' : '';
                            entry.passcode = headerMap.passcode !== undefined ? row[headerMap.passcode] || '' : '';
                            entry.link = headerMap.link !== undefined ? row[headerMap.link] || '' : '';
                        } else {
                            // Fallback: assume format NO|HARI|JAM|KODE|MK|DOSEN|...
                            entry.no = row[0] || '';
                            entry.hari = row[1] || '';
                            entry.jam = row[2] || '';
                            entry.kode_mk = row[3] || '';
                            entry.mata_kuliah = row[4] || '';
                            entry.dosen = row[5] || '';
                            entry.ruangan = row[6] || '';
                        }
                        
                        // Track current hari for rowspan handling
                        if (entry.hari) {
                            currentHari = entry.hari;
                        } else if (currentHari) {
                            entry.hari = currentHari;
                        }
                        
                        // Add entry if it has meaningful data (mata kuliah OR kode_mk)
                        if (entry.mata_kuliah || entry.kode_mk) {
                            result.mata_kuliah.push(entry);
                            
                            // Group by hari if available
                            const hariKey = hari.find(h => entry.hari.toLowerCase().includes(h.toLowerCase()));
                            if (hariKey && result.jadwal_per_hari[hariKey]) {
                                result.jadwal_per_hari[hariKey].push(entry);
                            }
                        }
                    });
                }
            });
            
            // Clean up empty days
            Object.keys(result.jadwal_per_hari).forEach(hari => {
                if (result.jadwal_per_hari[hari].length === 0) {
                    delete result.jadwal_per_hari[hari];
                }
            });
            
            return result;
        }""")
        
        print(f"  ✓ Tahun Akademik: {data.get('tahun_akademik', 'N/A')}")
        print(f"  ✓ Kelas: {data.get('kelas', 'N/A')}")
        print(f"  ✓ Found {len(data.get('mata_kuliah', []))} mata kuliah entries")
        print(f"  ✓ Days with schedule: {list(data.get('jadwal_per_hari', {}).keys())}")
        
        return data
    
    def get_nilai(self) -> Optional[Dict]:
        """Get nilai/KHS"""
        print("\n📈 === NILAI MAHASISWA ===")
        if self.navigate_to_url('/mahasiswa/akademik/index/gm/akademik'):
            return self.extract_page_data()
        return None
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all data at once"""
        print("\n🔄 Getting all data...")
        
        # List of semesters to scrape
        semesters = [
            "2024/2025 Ganjil",
            "2025/2026 Ganjil",
            "2025/2026 Genap"
        ]
        
        # Get presensi for all semesters
        presensi_data = {}
        for semester in semesters:
            presensi_data[semester] = self.get_presensi(semester)
        
        data = {
            'nim': self.nim,
            'timestamp': datetime.now().isoformat(),
            'biodata': self.get_biodata(),
            'presensi': presensi_data,
            'kalender': self.get_kalender(),
            'jadwal': self.get_jadwal(),
            'nilai': self.get_nilai()
        }
        
        return data
    
    def screenshot(self, name: str = 'screenshot'):
        """Take screenshot"""
        filename = f"{name}_{int(time.time())}.png"
        self.page.screenshot(path=filename, full_page=True)
        print(f"📸 Screenshot: {filename}")
        return filename
    
    def close(self):
        """Close browser and playwright"""
        try:
            if self.browser:
                self.browser.close()
            if self._playwright:
                self._playwright.stop()
            print("\n✓ Browser closed")
        except Exception as e:
            print(f"Warning: Error closing browser: {e}")


def main():
    """Main execution"""
    # Configuration
    NIM = "244101060077"
    PASSWORD = "Fahri080506!"
    
    print("=" * 60)
    print("POLINEMA SIAKAD SCRAPER")
    print("=" * 60)
    
    # Use context manager for automatic cleanup
    with PolinemaScraper(NIM, PASSWORD, headless=False) as scraper:
        # Login
        if not scraper.login():
            print("❌ Login failed!")
            return
        
        scraper.screenshot('01_after_login')
        
        # Get all data
        data = scraper.get_all_data()
        
        # Save to JSON
        output_file = 'polinema_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Data saved to: {output_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 DATA SUMMARY")
        print("=" * 60)
        print(f"Biodata: {'✓' if data['biodata'] else '✗'}")
        print(f"Presensi: {'✓' if data['presensi'] else '✗'}")
        print(f"Kalender: {'✓' if data['kalender'] else '✗'}")
        print(f"Jadwal: {'✓' if data['jadwal'] else '✗'}")
        print(f"Nilai: {'✓' if data['nilai'] else '✗'}")
        print("=" * 60)
        
        # Keep browser open for inspection
        print("\n⏳ Browser stays open for 10 seconds...")
        time.sleep(10)


if __name__ == "__main__":
    main()
