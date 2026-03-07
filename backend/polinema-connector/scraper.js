/**
 * Polinema SIAKAD Scraper using Playwright
 * Extracts: Biodata, Kehadiran, Kalender
 */

const { chromium } = require('playwright');

const CONFIG = {
    nim: '244101060077',
    password: 'Fahri080506!',
    siakad_url: 'https://siakad.polinema.ac.id',
    lms_url: 'https://lmsslc.polinema.ac.id'
};

class PolinemaScraper {
    constructor(config) {
        this.config = config;
        this.browser = null;
        this.context = null;
        this.page = null;
    }

    async init() {
        console.log('🚀 Launching browser...');
        this.browser = await chromium.launch({ headless: false }); // headless: true for production
        this.context = await this.browser.newContext({
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        });
        this.page = await this.context.newPage();
        console.log('✓ Browser ready');
    }

    async loginSIAKAD() {
        console.log('\n📝 Logging into SIAKAD...');
        
        try {
            await this.page.goto(this.config.siakad_url, { waitUntil: 'networkidle' });
            console.log('  Loading login page...');

            // Try different login form selectors
            await this.page.waitForTimeout(2000);

            // Check if already logged in
            if (this.page.url().includes('dashboard') || this.page.url().includes('beranda')) {
                console.log('✓ Already logged in!');
                return true;
            }

            // Find login form
            const usernameSelector = 'input[name="username"], input[name="nim"], input[type="text"], #username, #nim';
            const passwordSelector = 'input[name="password"], input[type="password"], #password';
            const submitSelector = 'button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Masuk")';

            console.log('  Filling credentials...');
            await this.page.fill(usernameSelector, this.config.nim);
            await this.page.fill(passwordSelector, this.config.password);
            
            console.log('  Submitting login...');
            await Promise.all([
                this.page.waitForNavigation({ waitUntil: 'networkidle', timeout: 30000 }),
                this.page.click(submitSelector)
            ]);

            // Check if login successful
            if (this.page.url().includes('dashboard') || this.page.url().includes('beranda')) {
                console.log('✓ Login successful!');
                console.log('  Dashboard URL:', this.page.url());
                return true;
            } else {
                console.log('✗ Login may have failed. Current URL:', this.page.url());
                return false;
            }

        } catch (error) {
            console.error('✗ Login error:', error.message);
            return false;
        }
    }

    async getBiodata() {
        console.log('\n📋 Fetching Biodata...');
        
        try {
            // Try to find biodata menu/link
            const biodataSelectors = [
                'a:has-text("Biodata")',
                'a:has-text("Profile")',
                'a:has-text("Data Mahasiswa")',
                '[href*="biodata"]',
                '[href*="profile"]'
            ];

            let found = false;
            for (const selector of biodataSelectors) {
                try {
                    await this.page.click(selector, { timeout: 5000 });
                    found = true;
                    break;
                } catch (e) {
                    continue;
                }
            }

            if (!found) {
                console.log('  Trying direct URL: /biodata or /mahasiswa/biodata');
                try {
                    await this.page.goto(`${this.config.siakad_url}/biodata`, { waitUntil: 'networkidle' });
                } catch (e) {
                    await this.page.goto(`${this.config.siakad_url}/mahasiswa/biodata`, { waitUntil: 'networkidle' });
                }
            }

            await this.page.waitForTimeout(2000);

            // Extract biodata from page
            const biodata = await this.page.evaluate(() => {
                const data = {};
                
                // Try to extract from tables
                const tables = document.querySelectorAll('table');
                tables.forEach(table => {
                    const rows = table.querySelectorAll('tr');
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td, th');
                        if (cells.length >= 2) {
                            const key = cells[0].innerText.trim();
                            const value = cells[1].innerText.trim();
                            if (key && value) {
                                data[key] = value;
                            }
                        }
                    });
                });

                // Also try to get from any divs with class info/data
                const infoElements = document.querySelectorAll('.info, .data, [class*="biodata"]');
                infoElements.forEach(el => {
                    const text = el.innerText;
                    if (text) data['_raw_' + Math.random()] = text;
                });

                return data;
            });

            console.log('✓ Biodata extracted:', JSON.stringify(biodata, null, 2));
            return biodata;

        } catch (error) {
            console.error('✗ Biodata error:', error.message);
            return null;
        }
    }

    async getKehadiran() {
        console.log('\n📊 Fetching Kehadiran...');
        
        try {
            // Try to find kehadiran/presensi menu
            const kehadiranSelectors = [
                'a:has-text("Kehadiran")',
                'a:has-text("Presensi")',
                'a:has-text("Absensi")',
                '[href*="kehadiran"]',
                '[href*="presensi"]',
                '[href*="absensi"]'
            ];

            let found = false;
            for (const selector of kehadiranSelectors) {
                try {
                    await this.page.click(selector, { timeout: 5000 });
                    found = true;
                    break;
                } catch (e) {
                    continue;
                }
            }

            if (!found) {
                console.log('  Trying direct URLs...');
                const urls = [
                    `${this.config.siakad_url}/kehadiran`,
                    `${this.config.siakad_url}/mahasiswa/kehadiran`,
                    `${this.config.siakad_url}/presensi`,
                    `${this.config.siakad_url}/mahasiswa/presensi`
                ];

                for (const url of urls) {
                    try {
                        await this.page.goto(url, { waitUntil: 'networkidle', timeout: 10000 });
                        if (!this.page.url().includes('404')) break;
                    } catch (e) {
                        continue;
                    }
                }
            }

            await this.page.waitForTimeout(2000);

            // Extract kehadiran data
            const kehadiran = await this.page.evaluate(() => {
                const data = {
                    matakuliah: [],
                    summary: {}
                };

                // Try to extract from tables
                const tables = document.querySelectorAll('table');
                tables.forEach(table => {
                    const rows = table.querySelectorAll('tbody tr');
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 4) {
                            data.matakuliah.push({
                                nama: cells[0]?.innerText.trim(),
                                hadir: cells[1]?.innerText.trim(),
                                izin: cells[2]?.innerText.trim(),
                                alpha: cells[3]?.innerText.trim(),
                                persentase: cells[4]?.innerText.trim()
                            });
                        }
                    });
                });

                // Extract summary statistics
                const summaryElements = document.querySelectorAll('[class*="summary"], [class*="total"], .card');
                summaryElements.forEach(el => {
                    const text = el.innerText;
                    if (text.toLowerCase().includes('hadir')) {
                        data.summary.hadir = text.match(/\\d+/)?.[0];
                    }
                    if (text.toLowerCase().includes('alpha')) {
                        data.summary.alpha = text.match(/\\d+/)?.[0];
                    }
                });

                return data;
            });

            console.log('✓ Kehadiran extracted:', JSON.stringify(kehadiran, null, 2));
            return kehadiran;

        } catch (error) {
            console.error('✗ Kehadiran error:', error.message);
            return null;
        }
    }

    async getKalender() {
        console.log('\n📅 Fetching Kalender Akademik...');
        
        try {
            // Try to find kalender menu
            const kalenderSelectors = [
                'a:has-text("Kalender")',
                'a:has-text("Akademik")',
                'a:has-text("Kalender Akademik")',
                '[href*="kalender"]'
            ];

            let found = false;
            for (const selector of kalenderSelectors) {
                try {
                    await this.page.click(selector, { timeout: 5000 });
                    found = true;
                    break;
                } catch (e) {
                    continue;
                }
            }

            if (!found) {
                await this.page.goto(`${this.config.siakad_url}/kalender`, { waitUntil: 'networkidle' });
            }

            await this.page.waitForTimeout(2000);

            // Extract calendar events
            const kalender = await this.page.evaluate(() => {
                const events = [];

                // Try to extract from tables or list
                const tables = document.querySelectorAll('table');
                tables.forEach(table => {
                    const rows = table.querySelectorAll('tbody tr');
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 2) {
                            events.push({
                                tanggal: cells[0]?.innerText.trim(),
                                kegiatan: cells[1]?.innerText.trim(),
                                keterangan: cells[2]?.innerText.trim()
                            });
                        }
                    });
                });

                // Try calendar elements
                const calendarItems = document.querySelectorAll('[class*="event"], [class*="calendar-item"], .list-group-item');
                calendarItems.forEach(item => {
                    const text = item.innerText.trim();
                    if (text) {
                        events.push({ raw: text });
                    }
                });

                return events;
            });

            console.log('✓ Kalender extracted:', JSON.stringify(kalender, null, 2));
            return kalender;

        } catch (error) {
            console.error('✗ Kalender error:', error.message);
            return null;
        }
    }

    async takeScreenshot(name = 'screenshot') {
        const filename = `${name}_${Date.now()}.png`;
        await this.page.screenshot({ path: filename, fullPage: true });
        console.log(`📸 Screenshot saved: ${filename}`);
    }

    async close() {
        if (this.browser) {
            await this.browser.close();
            console.log('\n✓ Browser closed');
        }
    }
}

// Main execution
async function main() {
    const scraper = new PolinemaScraper(CONFIG);
    
    try {
        await scraper.init();
        
        const loginSuccess = await scraper.loginSIAKAD();
        
        if (loginSuccess) {
            await scraper.takeScreenshot('after_login');
            
            const biodata = await scraper.getBiodata();
            const kehadiran = await scraper.getKehadiran();
            const kalender = await scraper.getKalender();
            
            console.log('\n' + '='.repeat(60));
            console.log('RESULTS SUMMARY');
            console.log('='.repeat(60));
            console.log('\n📋 Biodata:', biodata);
            console.log('\n📊 Kehadiran:', kehadiran);
            console.log('\n📅 Kalender:', kalender);
            
            // Save to file
            const fs = require('fs');
            const results = { biodata, kehadiran, kalender, timestamp: new Date().toISOString() };
            fs.writeFileSync('polinema_data.json', JSON.stringify(results, null, 2));
            console.log('\n✓ Data saved to polinema_data.json');
        }
        
    } catch (error) {
        console.error('\n✗ Main error:', error);
        await scraper.takeScreenshot('error');
    } finally {
        await scraper.close();
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = { PolinemaScraper, CONFIG };
