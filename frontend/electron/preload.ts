/**
 * JAWIR OS - Preload Script
 * Secure IPC bridge between main and renderer processes
 */

import { contextBridge, ipcRenderer } from 'electron';

// Type definitions for the exposed API
export interface ElectronAPI {
    // Server management
    server: {
        getStatuses: () => Promise<ServerStatus[]>;
        restart: (name: string) => Promise<void>;
        restartAll: () => Promise<void>;
        getLogs: (name: string) => Promise<string[]>;
        onStatusChange: (callback: (statuses: ServerStatus[]) => void) => () => void;
    };

    // App info
    app: {
        getInfo: () => Promise<AppInfo>;
        quit: () => void;
        minimize: () => void;
        maximize: () => void;
        isMaximized: () => Promise<boolean>;
    };

    // Voice (will be implemented in Phase 3)
    voice: {
        startRecording: () => Promise<void>;
        stopRecording: () => Promise<string>;
        setMode: (mode: 'ptt' | 'wakeword' | 'off') => Promise<void>;
        getMode: () => Promise<string>;
        onTranscript: (callback: (text: string) => void) => () => void;
    };
}

interface ServerStatus {
    name: string;
    displayName: string;
    port: number;
    status: 'starting' | 'online' | 'offline' | 'error' | 'stopping';
    restartCount: number;
    lastError?: string;
    pid?: number;
}

interface AppInfo {
    version: string;
    isDev: boolean;
    platform: string;
}

// Expose protected APIs to renderer
contextBridge.exposeInMainWorld('electronAPI', {
    // Server management
    server: {
        getStatuses: () => ipcRenderer.invoke('server:get-statuses'),
        restart: (name: string) => ipcRenderer.invoke('server:restart', name),
        restartAll: () => ipcRenderer.invoke('server:restart-all'),
        getLogs: (name: string) => ipcRenderer.invoke('server:get-logs', name),
        onStatusChange: (callback: (statuses: ServerStatus[]) => void) => {
            const listener = (_event: Electron.IpcRendererEvent, statuses: ServerStatus[]) => {
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
        setMode: (mode: string) => ipcRenderer.invoke('voice:set-mode', mode),
        getMode: () => ipcRenderer.invoke('voice:get-mode'),
        onTranscript: (callback: (text: string) => void) => {
            const listener = (_event: Electron.IpcRendererEvent, text: string) => {
                callback(text);
            };
            ipcRenderer.on('voice:transcript', listener);
            return () => {
                ipcRenderer.removeListener('voice:transcript', listener);
            };
        },
    },
} as ElectronAPI);

// Notify main process that preload is ready
console.log('🔌 JAWIR OS Preload script loaded');
