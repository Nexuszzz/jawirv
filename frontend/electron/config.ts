/**
 * JAWIR OS - Server Configuration
 * Defines all backend servers to be managed by Electron
 */

import path from 'path';

export interface ServerConfig {
    name: string;
    displayName: string;
    port: number;
    workingDir: string;
    command: string[];
    healthEndpoint: string;
    restartOnCrash: boolean;
    maxRestarts: number;
    startupDelay: number; // ms to wait after starting before checking health
}

/**
 * Get server configurations based on resource path
 */
export function getServerConfigs(resourcePath: string, isDev: boolean): ServerConfig[] {
    // In dev mode, use relative paths from project root
    // In production, use paths relative to resourcePath

    const pythonExe = isDev
        ? path.join(resourcePath, 'backend', 'venv_fresh', 'Scripts', 'python.exe')
        : path.join(resourcePath, 'venv_fresh', 'Scripts', 'python.exe');

    return [
        {
            name: 'polinema-api',
            displayName: 'Polinema API',
            port: 8001,
            workingDir: isDev
                ? path.join(resourcePath, 'backend', 'polinema-connector')
                : path.join(resourcePath, 'polinema-connector'),
            command: [pythonExe, 'polinema_api_server.py'],
            healthEndpoint: '/health',
            restartOnCrash: true,
            maxRestarts: 3,
            startupDelay: 3000,
        },
        {
            name: 'jawir-backend',
            displayName: 'JAWIR Backend',
            port: 8000,
            workingDir: isDev
                ? path.join(resourcePath, 'backend')
                : resourcePath,
            command: [pythonExe, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'],
            healthEndpoint: '/health',
            restartOnCrash: true,
            maxRestarts: 3,
            startupDelay: 5000,
        },
    ];
}

export const HEALTH_CHECK_INTERVAL = 30000; // 30 seconds
export const HEALTH_CHECK_TIMEOUT = 5000;   // 5 seconds
export const SHUTDOWN_TIMEOUT = 5000;       // 5 seconds for graceful shutdown
