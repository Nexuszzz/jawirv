/**
 * Polinema API Server for JAWIR AI
 * RESTful API wrapper for SIAKAD data
 */

const express = require('express');
const { PolinemaScraper, CONFIG } = require('./scraper_enhanced');

const app = express();
const PORT = 3001;

// Store scraper instance
let scraper = null;
let isLoggedIn = false;

app.use(express.json());

// Middleware to ensure scraper is ready
async function ensureLoggedIn(req, res, next) {
    if (isLoggedIn && scraper) {
        return next();
    }

    try {
        console.log('Initializing scraper...');
        scraper = new PolinemaScraper(CONFIG);
        await scraper.init();
        const success = await scraper.loginSIAKAD();
        
        if (success) {
            isLoggedIn = true;
            return next();
        } else {
            return res.status(401).json({ error: 'Login failed' });
        }
    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
}

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok',
        logged_in: isLoggedIn,
        timestamp: new Date().toISOString()
    });
});

// Login endpoint
app.post('/api/login', async (req, res) => {
    try {
        scraper = new PolinemaScraper(CONFIG);
        await scraper.init();
        const success = await scraper.loginSIAKAD();
        
        if (success) {
            isLoggedIn = true;
            res.json({ success: true, message: 'Logged in successfully' });
        } else {
            res.status(401).json({ success: false, message: 'Login failed' });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get biodata
app.get('/api/biodata', ensureLoggedIn, async (req, res) => {
    try {
        const data = await scraper.getBiodata();
        res.json({ success: true, data });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get kehadiran/presensi
app.get('/api/kehadiran', ensureLoggedIn, async (req, res) => {
    try {
        const data = await scraper.getKehadiran();
        res.json({ success: true, data });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get kalender
app.get('/api/kalender', ensureLoggedIn, async (req, res) => {
    try {
        const data = await scraper.getKalender();
        res.json({ success: true, data });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get nilai
app.get('/api/nilai', ensureLoggedIn, async (req, res) => {
    try {
        const data = await scraper.getNilai();
        res.json({ success: true, data });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get jadwal
app.get('/api/jadwal', ensureLoggedIn, async (req, res) => {
    try {
        const data = await scraper.getJadwal();
        res.json({ success: true, data });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get all data at once
app.get('/api/all', ensureLoggedIn, async (req, res) => {
    try {
        const [biodata, kehadiran, kalender, nilai, jadwal] = await Promise.all([
            scraper.getBiodata(),
            scraper.getKehadiran(),
            scraper.getKalender(),
            scraper.getNilai(),
            scraper.getJadwal()
        ]);

        res.json({
            success: true,
            data: {
                biodata,
                kehadiran,
                kalender,
                nilai,
                jadwal,
                timestamp: new Date().toISOString()
            }
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Logout and cleanup
app.post('/api/logout', async (req, res) => {
    try {
        if (scraper) {
            await scraper.close();
        }
        scraper = null;
        isLoggedIn = false;
        res.json({ success: true, message: 'Logged out' });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Error handler
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Internal server error', message: err.message });
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\nShutting down...');
    if (scraper) {
        await scraper.close();
    }
    process.exit(0);
});

app.listen(PORT, () => {
    console.log(`\n🚀 Polinema API Server running on http://localhost:${PORT}`);
    console.log(`\nAvailable endpoints:`);
    console.log(`  POST /api/login       - Login to SIAKAD`);
    console.log(`  GET  /api/biodata     - Get biodata mahasiswa`);
    console.log(`  GET  /api/kehadiran   - Get data kehadiran`);
    console.log(`  GET  /api/kalender    - Get kalender akademik`);
    console.log(`  GET  /api/nilai       - Get nilai/KHS`);
    console.log(`  GET  /api/jadwal      - Get jadwal kuliah`);
    console.log(`  GET  /api/all         - Get all data`);
    console.log(`  POST /api/logout      - Logout and cleanup`);
    console.log(`  GET  /health          - Health check`);
    console.log(`\n✓ Ready to receive requests\n`);
});
