/**
 * JAWIR OS - IPC Handlers
 * Handle IPC calls from renderer process
 */

import { IpcMain, BrowserWindow, app } from 'electron';
import { ServerManager } from './server-manager.js';

export function setupIpcHandlers(ipcMain: IpcMain, serverManager: ServerManager): void {
    // === Server Management ===

    ipcMain.handle('server:get-statuses', () => {
        return serverManager.getAllStatuses();
    });

    ipcMain.handle('server:restart', async (_event, name: string) => {
        await serverManager.restartServer(name);
    });

    ipcMain.handle('server:restart-all', async () => {
        await serverManager.restartAll();
    });

    ipcMain.handle('server:get-logs', (_event, name: string) => {
        return serverManager.getServerLogs(name);
    });

    // Forward server status changes to renderer
    serverManager.on('status-change', (statuses) => {
        const windows = BrowserWindow.getAllWindows();
        for (const win of windows) {
            win.webContents.send('server:status-change', statuses);
        }
    });

    // === App Control ===

    ipcMain.handle('app:get-info', () => {
        return {
            version: app.getVersion(),
            isDev: !app.isPackaged,
            platform: process.platform,
        };
    });

    ipcMain.on('app:quit', () => {
        app.quit();
    });

    ipcMain.on('app:minimize', (event) => {
        const win = BrowserWindow.fromWebContents(event.sender);
        win?.minimize();
    });

    ipcMain.on('app:maximize', (event) => {
        const win = BrowserWindow.fromWebContents(event.sender);
        if (win?.isMaximized()) {
            win.unmaximize();
        } else {
            win?.maximize();
        }
    });

    ipcMain.handle('app:is-maximized', (event) => {
        const win = BrowserWindow.fromWebContents(event.sender);
        return win?.isMaximized() ?? false;
    });

    // === Voice (Placeholder for Phase 3) ===

    ipcMain.handle('voice:start-recording', async () => {
        // TODO: Implement in Phase 3
        console.log('Voice: start recording');
    });

    ipcMain.handle('voice:stop-recording', async () => {
        // TODO: Implement in Phase 3
        console.log('Voice: stop recording');
        return '';
    });

    ipcMain.handle('voice:set-mode', async (_event, mode: string) => {
        // TODO: Implement in Phase 3
        console.log('Voice: set mode', mode);
    });

    ipcMain.handle('voice:get-mode', async () => {
        // TODO: Implement in Phase 3
        return 'off';
    });

    console.log('✅ IPC handlers registered');
}
