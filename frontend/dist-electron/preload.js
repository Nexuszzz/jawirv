/**
 * JAWIR OS - Preload Script
 * Secure IPC bridge between main and renderer processes
 */
import { contextBridge, ipcRenderer } from 'electron';
// Expose protected APIs to renderer
contextBridge.exposeInMainWorld('electronAPI', {
    // Server management
    server: {
        getStatuses: () => ipcRenderer.invoke('server:get-statuses'),
        restart: (name) => ipcRenderer.invoke('server:restart', name),
        restartAll: () => ipcRenderer.invoke('server:restart-all'),
        getLogs: (name) => ipcRenderer.invoke('server:get-logs', name),
        onStatusChange: (callback) => {
            const listener = (_event, statuses) => {
                callback(statuses);
            };
            ipcRenderer.on('server:status-change', listener);
            // Return cleanup function
            return () => {
                ipcRenderer.removeListener('server:status-change', listener);
            };
        },
    },
    // App control
    app: {
        getInfo: () => ipcRenderer.invoke('app:get-info'),
        quit: () => ipcRenderer.send('app:quit'),
        minimize: () => ipcRenderer.send('app:minimize'),
        maximize: () => ipcRenderer.send('app:maximize'),
        isMaximized: () => ipcRenderer.invoke('app:is-maximized'),
    },
    // Voice (placeholder for Phase 3)
    voice: {
        startRecording: () => ipcRenderer.invoke('voice:start-recording'),
        stopRecording: () => ipcRenderer.invoke('voice:stop-recording'),
        setMode: (mode) => ipcRenderer.invoke('voice:set-mode', mode),
        getMode: () => ipcRenderer.invoke('voice:get-mode'),
        onTranscript: (callback) => {
            const listener = (_event, text) => {
                callback(text);
            };
            ipcRenderer.on('voice:transcript', listener);
            return () => {
                ipcRenderer.removeListener('voice:transcript', listener);
            };
        },
    },
});
// Notify main process that preload is ready
console.log('🔌 JAWIR OS Preload script loaded');
//# sourceMappingURL=preload.js.map