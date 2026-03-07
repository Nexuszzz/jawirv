/**
 * JAWIR OS - Electron Main Process
 * Entry point for the desktop application
 */
import { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import { ServerManager } from './server-manager.js';
import { setupIpcHandlers } from './ipc-handlers.js';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Determine if we're in development mode
const isDev = !app.isPackaged;
let mainWindow = null;
let tray = null;
let serverManager = null;
let isQuitting = false; // Track if app is quitting
// Get the root directory for resources
function getResourcePath() {
    if (isDev) {
        // In dev, go up from dist-electron to frontend, then to jawirv2
        return path.join(__dirname, '..', '..');
    }
    return process.resourcesPath;
}
async function createWindow() {
    // Try to load icon, fallback if not exists
    let iconPath;
    try {
        iconPath = path.join(__dirname, '..', 'assets', 'icon.png');
    }
    catch {
        iconPath = undefined;
    }
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1000,
        minHeight: 700,
        title: 'JAWIR OS',
        icon: iconPath,
        frame: true, // Use native frame for now
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: false, // Need access to some Node APIs through preload
        },
        show: false, // Don't show until ready
        backgroundColor: '#1a1a2e',
    });
    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow?.show();
        if (isDev) {
            mainWindow?.webContents.openDevTools();
        }
    });
    // Load the app
    if (isDev) {
        await mainWindow.loadURL('http://localhost:5173');
    }
    else {
        await mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
    }
    // Handle window close - minimize to tray instead
    mainWindow.on('close', (event) => {
        if (!isQuitting) {
            event.preventDefault();
            mainWindow?.hide();
        }
    });
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}
function createTray() {
    try {
        const iconPath = path.join(__dirname, '..', 'assets', 'icon.png');
        const icon = nativeImage.createFromPath(iconPath);
        tray = new Tray(icon.resize({ width: 16, height: 16 }));
        const contextMenu = Menu.buildFromTemplate([
            {
                label: 'Show JAWIR OS',
                click: () => mainWindow?.show(),
            },
            {
                label: 'Server Status',
                submenu: [
                    {
                        label: 'Check Status',
                        click: () => {
                            mainWindow?.webContents.send('show-server-status');
                            mainWindow?.show();
                        },
                    },
                    {
                        label: 'Restart All Servers',
                        click: async () => {
                            await serverManager?.restartAll();
                        },
                    },
                ],
            },
            { type: 'separator' },
            {
                label: 'Quit',
                click: () => {
                    isQuitting = true;
                    app.quit();
                },
            },
        ]);
        tray.setToolTip('JAWIR OS - AI Desktop Agent');
        tray.setContextMenu(contextMenu);
        tray.on('double-click', () => {
            mainWindow?.show();
        });
    }
    catch (error) {
        console.warn('Could not create tray icon:', error);
    }
}
async function initializeApp() {
    const resourcePath = getResourcePath();
    console.log('🚀 JAWIR OS starting...');
    console.log(`📁 Resource path: ${resourcePath}`);
    console.log(`🔧 Development mode: ${isDev}`);
    // Initialize server manager
    serverManager = new ServerManager(resourcePath, isDev);
    // Setup IPC handlers
    setupIpcHandlers(ipcMain, serverManager);
    // Start all backend servers
    console.log('🔌 Starting backend servers...');
    try {
        await serverManager.startAll();
        console.log('✅ All servers started successfully');
    }
    catch (error) {
        console.error('❌ Failed to start some servers:', error);
        // Continue anyway - UI will show server status
    }
    // Create window and tray
    await createWindow();
    createTray();
    // Send ready event to renderer
    mainWindow?.webContents.on('did-finish-load', () => {
        mainWindow?.webContents.send('app-ready', {
            isDev,
            resourcePath,
        });
    });
}
// App lifecycle
app.whenReady().then(initializeApp);
app.on('window-all-closed', () => {
    // On macOS, apps typically stay in dock
    if (process.platform !== 'darwin') {
        // Don't quit - stay in tray
    }
});
app.on('activate', () => {
    // On macOS, re-create window when dock icon is clicked
    if (mainWindow === null) {
        createWindow();
    }
    else {
        mainWindow.show();
    }
});
app.on('before-quit', async (event) => {
    console.log('👋 JAWIR OS shutting down...');
    if (serverManager && !isQuitting) {
        event.preventDefault();
        isQuitting = true;
        try {
            await serverManager.shutdownAll();
            console.log('✅ All servers stopped');
        }
        catch (error) {
            console.error('⚠️ Error stopping servers:', error);
        }
        app.quit();
    }
});
// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error('Uncaught exception:', error);
});
process.on('unhandledRejection', (reason) => {
    console.error('Unhandled rejection:', reason);
});
//# sourceMappingURL=main.js.map