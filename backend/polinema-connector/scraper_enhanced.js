/**
 * Enhanced Polinema SIAKAD Scraper
 * Navigates through actual menu structure
 */

const { chromium } = require('playwright');
const fs = require('fs');

const CONFIG = {
    nim: '244101060077',
    password: 'Fahri080506!',
    siakad_url: 'https://siakad.polinema.ac.id'
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
        this.browser = await chromium.launch({
            headless: false,
            slowMo: 100 // Slow down for debugging
        });
        this.context = await this.browser.newContext({
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            ignoreHTTPSErrors: true  // Ignore SSL certificate errors (LMS has expired cert)
        });
        this.page = await this.context.newPage();

        // Enable request interception to catch API calls
        this.page.on('response', async (response) => {
            const url = response.url();
            if (url.includes('/api/') || url.includes('.json')) {
                try {
                    const json = await response.json();
                    console.log(`📡 API Call: ${url}`);
                    console.log('Response:', JSON.stringify(json, null, 2).slice(0, 300));
                } catch (e) {
                    // Not JSON
                }
            }
        });

        console.log('✓ Browser ready');
    }

    async loginSIAKAD() {
        console.log('\n📝 Logging into SIAKAD...');

        try {
            await this.page.goto(this.config.siakad_url, { waitUntil: 'networkidle' });
            await this.page.waitForTimeout(2000);

            if (this.page.url().includes('dashboard') || this.page.url().includes('beranda')) {
                console.log('✓ Already logged in!');
                return true;
            }

            // Find and fill login form
            await this.page.locator('input[name="username"], input[name="nim"]').first().fill(this.config.nim);
            await this.page.locator('input[name="password"]').first().fill(this.config.password);

            // Click login and wait
            await Promise.all([
                this.page.waitForNavigation({ timeout: 30000 }),
                this.page.locator('button[type="submit"]').first().click()
            ]);

            if (this.page.url().includes('beranda') || this.page.url().includes('dashboard')) {
                console.log('✓ Login successful!');
                console.log('  URL:', this.page.url());
                return true;
            }

            return false;

        } catch (error) {
            console.error('✗ Login error:', error.message);
            await this.page.screenshot({ path: 'login_error.png' });
            return false;
        }
    }

    async exploreMenus() {
        console.log('\n🔍 Exploring available menus...');

        try {
            const menus = await this.page.evaluate(() => {
                const links = Array.from(document.querySelectorAll('a, button'));
                return links.map(link => ({
                    text: link.innerText?.trim(),
                    href: link.href || link.getAttribute('href') || '',
                    class: link.className,
                    onclick: link.onclick?.toString().slice(0, 100)
                })).filter(l => l.text && l.text.length > 0 && l.text.length < 50);
            });

            console.log('\n📋 Available menus:');
            menus.forEach((menu, i) => {
                console.log(`  ${i + 1}. ${menu.text} → ${menu.href || menu.onclick || 'no link'}`);
            });

            return menus;

        } catch (error) {
            console.error('✗ Menu exploration error:', error.message);
            return [];
        }
    }

    async navigateToUrl(path) {
        const url = `${this.config.siakad_url}${path}`;
        console.log(`\n🎯 Navigating to: ${url}`);

        try {
            await this.page.goto(url, { waitUntil: 'networkidle' });
            await this.page.waitForTimeout(2000);
            console.log(`  ✓ Current URL: ${this.page.url()}`);
            return true;
        } catch (error) {
            console.error(`  ✗ Navigation error: ${error.message}`);
            return false;
        }
    }

    async navigateToMenu(searchTerms) {
        console.log(`\n🎯 Looking for menu: ${searchTerms.join(' or ')}...`);

        try {
            for (const term of searchTerms) {
                try {
                    // Try clicking by text
                    const locator = this.page.locator(`a:has-text("${term}"), button:has-text("${term}")`);
                    const count = await locator.count();

                    if (count > 0) {
                        console.log(`  Found "${term}", clicking...`);
                        await locator.first().click();
                        await this.page.waitForTimeout(2000);
                        console.log(`  ✓ Navigated to: ${this.page.url()}`);
                        return true;
                    }
                } catch (e) {
                    console.log(`  "${term}" not found, trying next...`);
                    continue;
                }
            }

            console.log('  ✗ No matching menu found');
            return false;

        } catch (error) {
            console.error('✗ Navigation error:', error.message);
            return false;
        }
    }

    async extractPageData() {
        console.log('\n📦 Extracting page data...');

        try {
            await this.page.waitForTimeout(1000);

            const data = await this.page.evaluate(() => {
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

                // Extract cards/boxes
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
                        result.lists.push({ index: idx, items });
                    }
                });

                return result;
            });

            console.log('✓ Data extracted');
            console.log('  Tables:', data.tables.length);
            console.log('  Cards:', data.cards.length);
            console.log('  Lists:', data.lists.length);

            return data;

        } catch (error) {
            console.error('✗ Extraction error:', error.message);
            return null;
        }
    }

    async getBiodata() {
        console.log('\n📋 === FETCHING BIODATA ===');
        if (await this.navigateToUrl('/mahasiswa/biodata/index/gm/general')) {
            return await this.extractPageData();
        }
        return null;
    }

    async getKehadiran(semester = '2024/2025 Ganjil') {
        console.log(`\n📊 === FETCHING KEHADIRAN (${semester}) ===`);

        if (!await this.navigateToUrl('/mahasiswa/presensi/index/gm/akademik')) {
            return null;
        }

        // Wait and try to select semester
        await this.page.waitForTimeout(2000);

        try {
            console.log(`  🔄 Selecting semester: ${semester}`);

            // Select semester from dropdown
            await this.page.locator('select').first().selectOption({ label: semester });
            await this.page.waitForTimeout(1000);

            // Click Filter button
            await this.page.locator('button:has-text("Filter"), input[type="button"][value="Filter"]').first().click();

            console.log('  ✓ Filter applied, waiting for data...');
            await this.page.waitForTimeout(3000);

        } catch (error) {
            console.log(`  ⚠️ Filter error: ${error.message}`);
            console.log('  Continuing with default semester...');
        }

        return await this.extractPageData();
    }

    // DISABLED: Calendar endpoint returns 404 (slc.polinema.ac.id/calendar/view.php)
    // async getKalender() {
    //     console.log('\n📅 === FETCHING KALENDER ===');
    //     if (await this.navigateToUrl('/mahasiswa/kalenderakd/index/gm/akademik')) {
    //         return await this.extractPageData();
    //     }
    //     return null;
    // }
    async getKalender() {
        console.log('\n📅 === SKIPPING KALENDER (404 error) ===');
        return { skipped: true, reason: 'Calendar endpoint returns 404' };
    }

    async getNilai() {
        console.log('\n📈 === FETCHING NILAI ===');
        if (await this.navigateToUrl('/mahasiswa/akademik/index/gm/akademik')) {
            return await this.extractPageData();
        }
        return null;
    }

    async getJadwal() {
        console.log('\n📆 === FETCHING JADWAL ===');
        if (await this.navigateToUrl('/mahasiswa/jadwal/index/gm/akademik')) {
            return await this.extractPageData();
        }
        return null;
    }

    async loginToLMS() {
        console.log('\n🎓 === LOGGING INTO LMS SPADA via SIAKAD SSO ===');

        try {
            // Navigate to LMS connection page from SIAKAD
            console.log('  🔗 Navigating to SIAKAD LMS Connector...');
            await this.navigateToUrl('/mahasiswa/slc/index/gm/akademik');
            await this.page.waitForTimeout(3000);

            // Wait for page to fully load
            await this.page.waitForLoadState('domcontentloaded');

            console.log(`  📍 Current URL: ${this.page.url()}`);
            await this.takeScreenshot('lms_01_connector_page');

            // Debug: Show page content
            const pageContent = await this.page.evaluate(() => {
                return {
                    text: document.body.innerText.slice(0, 500),
                    buttons: Array.from(document.querySelectorAll('button, a.btn, input[type="button"]'))
                        .map(b => ({ text: b.innerText || b.value, class: b.className }))
                };
            });
            console.log('  📄 Page buttons found:', JSON.stringify(pageContent.buttons));

            // Look for "Connect to LMS Polinema" button - it's a green button
            const buttonSelectors = [
                'button:has-text("Connect to LMS Polinema")',
                'a:has-text("Connect to LMS Polinema")',
                'button:has-text("Connect to LMS")',
                'a:has-text("Connect to LMS")',
                '.btn-success',
                '.btn-primary',
                'button.btn',
                'a.btn'
            ];

            let clicked = false;
            for (const selector of buttonSelectors) {
                try {
                    const btn = this.page.locator(selector);
                    const count = await btn.count();

                    if (count > 0) {
                        const btnText = await btn.first().innerText().catch(() => '');
                        console.log(`  ✓ Found button: ${selector} - "${btnText}"`);

                        if (btnText.toLowerCase().includes('connect')) {
                            console.log('  🔐 Clicking Connect to LMS Polinema...');
                            await btn.first().click();
                            clicked = true;
                            await this.page.waitForTimeout(5000);
                            break;
                        }
                    }
                } catch (e) {
                    continue;
                }
            }

            if (!clicked) {
                console.log('  ⚠️ Connect button not clicked, page content:');
                console.log('  ', pageContent.text.slice(0, 300));
            }

            // Check current URL after click
            let currentUrl = this.page.url();
            console.log(`  📍 After click URL: ${currentUrl}`);

            // If still on SIAKAD, try direct SPADA access with SSL bypass
            if (currentUrl.includes('siakad.polinema.ac.id')) {
                console.log('  🔄 Still on SIAKAD, trying direct SPADA access...');

                // Try slc.polinema.ac.id/spada (from your screenshot)
                try {
                    await this.page.goto('https://slc.polinema.ac.id/spada/', {
                        waitUntil: 'domcontentloaded',
                        timeout: 30000
                    });
                    await this.page.waitForTimeout(3000);
                    currentUrl = this.page.url();
                    console.log(`  📍 SPADA URL: ${currentUrl}`);
                } catch (e) {
                    console.log(`  ⚠️ SPADA error: ${e.message}`);

                    // Try alternative LMS URL
                    try {
                        console.log('  🔄 Trying lmsslc.polinema.ac.id...');
                        await this.page.goto('https://lmsslc.polinema.ac.id/', {
                            waitUntil: 'domcontentloaded',
                            timeout: 30000
                        });
                        await this.page.waitForTimeout(3000);
                        currentUrl = this.page.url();
                        console.log(`  📍 LMSSLC URL: ${currentUrl}`);
                    } catch (e2) {
                        console.log(`  ⚠️ LMSSLC error: ${e2.message}`);
                    }
                }
            }

            await this.takeScreenshot('lms_02_after_connect');

            // Check if we're on LMS/SPADA
            if (currentUrl.includes('slc.polinema.ac.id') ||
                currentUrl.includes('lms') ||
                currentUrl.includes('spada') ||
                currentUrl.includes('moodle')) {
                console.log('  ✓ Successfully connected to LMS/SPADA!');
                return true;
            }

            console.log('  ⚠️ Could not verify LMS connection');
            return false;

        } catch (error) {
            console.error(`  ✗ LMS SSO error: ${error.message}`);
            await this.takeScreenshot('lms_error');
            return false;
        }
    }

    async getLMSCourses() {
        console.log('\n📚 === FETCHING LMS COURSES ===');

        try {
            // Wait for SPADA page to fully load
            await this.page.waitForTimeout(3000);

            // Parse courses from page text
            const courses = await this.page.evaluate(() => {
                const results = [];
                const pageText = document.body.innerText;
                const lines = pageText.split('\n');

                // Course names typically appear as lines in SPADA
                // Skip header lines like "LMS", "TUGAS KULIAH", etc
                const skipWords = ['MUHAMMAD', 'LMS', 'TUGAS KULIAH', 'VIDEO CONFERENCE',
                    'Kuliah daring', 'Semester', 'Spada'];

                lines.forEach(line => {
                    const trimmed = line.trim();

                    // Skip empty or short lines
                    if (trimmed.length < 5) return;

                    // Skip header/navigation lines
                    if (skipWords.some(word => trimmed.startsWith(word))) return;

                    // Look for course patterns - courses have subject names
                    const courseKeywords = [
                        'Praktikum', 'Workshop', 'Sistem', 'Antena', 'Agama',
                        'Jaringan', 'Komunikasi', 'Mikrokontroler', 'Rekayasa',
                        'Fiber', 'Seluler', 'Modulasi', 'Transmisi', 'Radio'
                    ];

                    if (courseKeywords.some(kw => trimmed.includes(kw))) {
                        // Check if it's a course with program info
                        if (trimmed.includes(':')) {
                            const parts = trimmed.split(':');
                            const title = parts[0].trim();
                            const program = parts.slice(1).join(':').trim();
                            if (!results.find(r => r.title === title)) {
                                results.push({ title, program, url: '' });
                            }
                        } else {
                            // Just course name
                            if (!results.find(r => r.title === trimmed)) {
                                results.push({ title: trimmed, program: '', url: '' });
                            }
                        }
                    }
                });

                return results;
            });

            console.log(`  ✓ Found ${courses.length} courses`);
            courses.forEach((c, i) => {
                console.log(`    ${i + 1}. ${c.title}`);
                if (c.program) console.log(`       Program: ${c.program}`);
            });

            return courses;

        } catch (error) {
            console.error(`  ✗ Error fetching courses: ${error.message}`);
            return [];
        }
    }

    async getLMSAssignments() {
        console.log('\n📋 === FETCHING LMS ASSIGNMENTS/TUGAS ===');

        try {
            const currentUrl = this.page.url();
            console.log(`  📍 Current LMS URL: ${currentUrl}`);

            await this.page.waitForTimeout(2000);
            await this.takeScreenshot('lms_03_before_tugas');

            let allAssignments = [];

            // Strategy 1: Click TUGAS KULIAH tab and look for tree items
            console.log('  🔍 Looking for TUGAS KULIAH tab...');

            const tabSelectors = [
                'a:has-text("TUGAS KULIAH")',
                'button:has-text("TUGAS KULIAH")',
                'li:has-text("TUGAS KULIAH") a'
            ];

            for (const selector of tabSelectors) {
                try {
                    const tab = this.page.locator(selector);
                    const count = await tab.count();
                    if (count > 0) {
                        console.log(`  ✓ Found TUGAS tab: ${selector}`);
                        await tab.first().click();
                        await this.page.waitForTimeout(3000);
                        console.log('  ✓ Clicked TUGAS KULIAH tab');
                        break;
                    }
                } catch (e) {
                    continue;
                }
            }

            await this.takeScreenshot('lms_04_tugas_tab');

            // SPADA uses FancyTree for course structure
            // We need to click on expander icons to expand tree nodes RECURSIVELY
            console.log('  🌳 SPADA uses FancyTree - expanding ALL tree nodes recursively...');

            // Keep expanding until no more collapsed nodes exist
            let round = 0;
            let totalClicked = 0;

            while (round < 6) { // Maximum 6 rounds of expansion
                round++;
                console.log(`\n  📂 Expansion round ${round}...`);

                // Get fresh list of expanders each round (new nodes may appear)
                const expanders = await this.page.locator('.fancytree-expander').all();
                console.log(`    Total expanders visible: ${expanders.length}`);

                // Check how many nodes are still collapsed
                const collapsedNodes = await this.page.locator('.fancytree-exp-c').count();
                console.log(`    Collapsed nodes (fancytree-exp-c): ${collapsedNodes}`);

                if (collapsedNodes === 0 && round > 1) {
                    console.log('    ✓ All nodes fully expanded!');
                    break;
                }

                // Click each expander
                let clickedThisRound = 0;
                for (let i = 0; i < expanders.length; i++) {
                    try {
                        const expander = expanders[i];
                        if (await expander.isVisible()) {
                            // Check if this node is collapsed (has class exp-c)
                            const parentNode = await this.page.locator('.fancytree-node').nth(i);
                            const isCollapsed = await parentNode.evaluate(el => el.classList.contains('fancytree-exp-c'));

                            if (isCollapsed || round === 1) {
                                await expander.click();
                                clickedThisRound++;
                                totalClicked++;
                                await this.page.waitForTimeout(800);
                            }
                        }
                    } catch (e) {
                        // Ignore click errors
                    }
                }

                console.log(`    Clicked ${clickedThisRound} expanders this round`);

                // Wait for AJAX content to load
                await this.page.waitForTimeout(1500);

                // If we clicked nothing, we're done
                if (clickedThisRound === 0) {
                    console.log('    No more expanders to click');
                    break;
                }
            }

            console.log(`\n  📊 Total expanders clicked: ${totalClicked}`);

            await this.takeScreenshot('lms_05_after_expand');

            // Wait for tree to fully expand
            await this.page.waitForTimeout(2000);

            // Get page content after expansion
            const pageContent = await this.page.evaluate(() => document.body.innerText);
            console.log('\n  📄 Page content after FancyTree expansion:');
            console.log(pageContent.slice(0, 2000));

            // Now extract assignments from expanded tree
            const assignments = await this.page.evaluate(() => {
                const results = [];

                // Get all tree node titles (assignments should be visible now)
                const treeNodes = document.querySelectorAll('.fancytree-title');

                let currentCourse = '';
                let currentPertemuan = '';

                treeNodes.forEach(node => {
                    const text = node.innerText?.trim();
                    if (!text) return;

                    // Update current course
                    if (text.includes('Workshop') ||
                        text.includes('Sistem Komunikasi') ||
                        text.includes('Praktikum')) {
                        const colonIdx = text.indexOf(':');
                        currentCourse = colonIdx > 0 ? text.substring(0, colonIdx).trim() : text;
                        return;
                    }

                    // Update current pertemuan
                    if (text.match(/Pertemuan\s+ke[-\s]?\d+/i)) {
                        currentPertemuan = text;
                        return;
                    }

                    // Detect assignments/quizzes
                    const lower = text.toLowerCase();
                    if ((lower.includes('quiz') ||
                        lower.includes('tugas') ||
                        lower.includes('pengumpulan') ||
                        lower.includes('essay') ||
                        lower.includes('ujian') ||
                        lower.includes('uts') ||
                        lower.includes('uas')) &&
                        !lower.includes('tugas kuliah') &&
                        text.length > 3 && text.length < 200) {

                        results.push({
                            title: text,
                            course: currentCourse || 'Unknown Course',
                            pertemuan: currentPertemuan || '',
                            type: 'Assignment/Quiz',
                            dueDate: 'Check in LMS',
                            status: 'Active'
                        });
                    }
                });

                return results;
            });

            console.log(`\n  📝 Assignments from FancyTree: ${assignments.length}`);
            assignments.forEach(a => {
                console.log(`    - ${a.title}`);
                console.log(`      📚 ${a.course}`);
            });

            allAssignments.push(...assignments);

            // Also check text-based extraction as backup
            const textAssignments = await this.page.evaluate(() => {
                const results = [];
                const pageText = document.body.innerText;
                const lines = pageText.split('\n');

                let currentCourse = '';
                let currentPertemuan = '';

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed || trimmed.length < 3) continue;

                    // Track course
                    if (trimmed.includes(':') && (
                        trimmed.includes('Workshop') ||
                        trimmed.includes('Sistem') ||
                        trimmed.includes('Praktikum')
                    )) {
                        currentCourse = trimmed.split(':')[0].trim();
                        continue;
                    }

                    // Track pertemuan
                    if (trimmed.match(/Pertemuan\s+ke[-\s]?\d+/i)) {
                        currentPertemuan = trimmed;
                        continue;
                    }

                    // Detect assignments
                    const lower = trimmed.toLowerCase();
                    if ((lower.includes('quiz') ||
                        lower.includes('tugas') ||
                        lower.includes('pengumpulan')) &&
                        !lower.includes('tugas kuliah') &&
                        trimmed.length > 5 && trimmed.length < 150) {

                        results.push({
                            title: trimmed,
                            course: currentCourse,
                            pertemuan: currentPertemuan,
                            type: 'From Text'
                        });
                    }
                }

                return results;
            });

            console.log(`  📝 Text-based assignments: ${textAssignments.length}`);

            // Merge and deduplicate
            for (const ta of textAssignments) {
                if (!allAssignments.find(a => a.title.toLowerCase() === ta.title.toLowerCase())) {
                    allAssignments.push(ta);
                }
            }

            await this.takeScreenshot('lms_05_after_courses');

            // Deduplicate
            const uniqueAssignments = [];
            const seenTitles = new Set();
            allAssignments.forEach(a => {
                const key = a.title.toLowerCase().slice(0, 40);
                if (!seenTitles.has(key)) {
                    seenTitles.add(key);
                    uniqueAssignments.push(a);
                }
            });

            console.log(`\n  ✓ Total assignments found: ${uniqueAssignments.length}`);

            if (uniqueAssignments.length > 0) {
                console.log('\n  📝 All Assignments:');
                uniqueAssignments.forEach((a, i) => {
                    console.log(`    ${i + 1}. ${a.title}`);
                    console.log(`       📚 Course: ${a.course}`);
                });
            }

            return uniqueAssignments;

        } catch (error) {
            console.error(`  ✗ Error fetching assignments: ${error.message}`);
            return [];
        }
    }

    // DISABLED: /calendar/view.php returns 404
    async getLMSCalendarEvents() {
        console.log('\n🗓️ === SKIPPING LMS CALENDAR (404 error) ===');
        return [];  // Skip - endpoint returns 404
    }

    async getAllLMSData() {
        console.log('\n🎓 === COLLECTING ALL LMS DATA ===');

        const lmsData = {
            connected: false,
            courses: [],
            assignments: [],
            calendar: []
        };

        // Login to LMS
        if (await this.loginToLMS()) {
            lmsData.connected = true;

            // Get courses
            lmsData.courses = await this.getLMSCourses();

            // Get assignments/tugas
            lmsData.assignments = await this.getLMSAssignments();

            // DISABLED: Calendar causes 404
            // lmsData.calendar = await this.getLMSCalendarEvents();
            lmsData.calendar = [];  // Skip calendar
        } else {
            console.log('  ✗ Could not connect to LMS');
        }

        return lmsData;
    }

    async takeScreenshot(name = 'screenshot') {
        const filename = `${name}_${Date.now()}.png`;
        await this.page.screenshot({ path: filename, fullPage: true });
        console.log(`📸 Screenshot: ${filename}`);
        return filename;
    }

    async close() {
        if (this.browser) {
            await this.browser.close();
            console.log('\n✓ Browser closed');
        }
    }
}

async function main() {
    const scraper = new PolinemaScraper(CONFIG);
    const results = {};

    try {
        await scraper.init();

        const loginSuccess = await scraper.loginSIAKAD();

        if (!loginSuccess) {
            console.error('Login failed!');
            return;
        }

        await scraper.takeScreenshot('01_after_login');

        // Explore menus first
        const menus = await scraper.exploreMenus();
        results.menus = menus;

        // Get all data
        results.biodata = await scraper.getBiodata();
        await scraper.takeScreenshot('02_biodata');

        // Get kehadiran for all semesters
        const semesters = [
            '2024/2025 Ganjil',
            '2025/2026 Ganjil',
            '2025/2026 Genap'
        ];

        results.kehadiran = {};
        for (let i = 0; i < semesters.length; i++) {
            const semester = semesters[i];
            console.log(`\n\n🔄 Getting kehadiran for: ${semester}`);
            results.kehadiran[semester] = await scraper.getKehadiran(semester);
            await scraper.takeScreenshot(`03_kehadiran_${i + 1}_${semester.replace(/\//g, '_')}`);
        }

        // DISABLED: Calendar causes 404/hang
        // results.kalender = await scraper.getKalender();
        // await scraper.takeScreenshot('04_kalender');
        results.kalender = { skipped: true, reason: 'Calendar endpoint returns 404' };
        console.log('\n📅 Skipping calendar (known 404 issue)');

        results.nilai = await scraper.getNilai();
        await scraper.takeScreenshot('05_nilai');

        results.jadwal = await scraper.getJadwal();
        await scraper.takeScreenshot('06_jadwal');

        // Get LMS data (SPADA)
        console.log('\n\n' + '='.repeat(60));
        console.log('SCRAPING LMS SPADA DATA');
        console.log('='.repeat(60));
        results.lms = await scraper.getAllLMSData();
        await scraper.takeScreenshot('07_lms_data');

        // Save results
        results.timestamp = new Date().toISOString();
        results.nim = CONFIG.nim;

        const filename = 'polinema_complete_data.json';
        fs.writeFileSync(filename, JSON.stringify(results, null, 2));
        console.log(`\n✅ Complete data saved to: ${filename}`);

        // Print summary
        console.log('\n' + '='.repeat(60));
        console.log('📊 DATA SUMMARY');
        console.log('='.repeat(60));
        console.log(`Menus found: ${results.menus?.length || 0}`);
        console.log(`Biodata: ${results.biodata ? 'OK' : 'EMPTY'}`);
        console.log(`Kehadiran: ${results.kehadiran ? 'OK' : 'EMPTY'}`);
        console.log(`Kalender: SKIPPED (404)`);
        console.log(`Nilai: ${results.nilai ? 'OK' : 'EMPTY'}`);
        console.log(`Jadwal: ${results.jadwal ? 'OK' : 'EMPTY'}`);
        console.log(`LMS Connected: ${results.lms?.connected ? 'YES' : 'NO'}`);
        console.log(`LMS Courses: ${results.lms?.courses?.length || 0}`);
        console.log(`LMS Assignments: ${results.lms?.assignments?.length || 0}`);
        console.log(`LMS Calendar Events: ${results.lms?.calendar?.length || 0}`);
        console.log('='.repeat(60));

    } catch (error) {
        console.error('\n✗ Error:', error);
        await scraper.takeScreenshot('error');
    } finally {
        // Keep browser open for inspection
        console.log('\n⏳ Browser will stay open for 30 seconds for inspection...');
        await new Promise(resolve => setTimeout(resolve, 30000));
        await scraper.close();
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = { PolinemaScraper, CONFIG };
