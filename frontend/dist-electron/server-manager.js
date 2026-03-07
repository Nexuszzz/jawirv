/**
 * JAWIR OS - Server Manager
 * Manages lifecycle of all backend servers with health monitoring and crash recovery
 */
import { spawn } from 'child_process';
import { EventEmitter } from 'events';
import { getServerConfigs, HEALTH_CHECK_INTERVAL, HEALTH_CHECK_TIMEOUT, SHUTDOWN_TIMEOUT } from './config.js';
export class ServerManager extends EventEmitter {
    resourcePath;
    isDev;
    servers = new Map();
    healthCheckInterval = null;
    isShuttingDown = false;
    constructor(resourcePath, isDev) {
        super();
        this.resourcePath = resourcePath;
        this.isDev = isDev;
        // Initialize server configs
        const configs = getServerConfigs(resourcePath, isDev);
        for (const config of configs) {
            this.servers.set(config.name, {
                config,
                process: null,
                status: {
                    name: config.name,
                    displayName: config.displayName,
                    port: config.port,
                    status: 'offline',
                    restartCount: 0,
                },
            });
        }
    }
    /**
     * Start all servers in order
     */
    async startAll() {
        console.log('🚀 Starting all servers...');
        for (const [name, server] of this.servers) {
            try {
                await this.startServer(name);
                // Wait for startup delay before starting next
                await this.delay(server.config.startupDelay);
            }
            catch (error) {
                console.error(`❌ Failed to start ${name}:`, error);
                // Continue with other servers
            }
        }
        // Start health check loop
        this.startHealthCheck();
    }
    /**
     * Start a specific server
     */
    async startServer(name) {
        const server = this.servers.get(name);
        if (!server) {
            throw new Error(`Server ${name} not found`);
        }
        if (server.status.status === 'online') {
            console.log(`⚠️ ${name} already running`);
            return;
        }
        // Check if port is available
        if (await this.isPortInUse(server.config.port)) {
            console.log(`⚠️ Port ${server.config.port} already in use, assuming ${name} is running externally`);
            server.status.status = 'online';
            this.emit('status-change', this.getAllStatuses());
            return;
        }
        console.log(`🔌 Starting ${server.config.displayName}...`);
        server.status.status = 'starting';
        this.emit('status-change', this.getAllStatuses());
        try {
            const [cmd, ...args] = server.config.command;
            const proc = spawn(cmd, args, {
                cwd: server.config.workingDir,
                stdio: ['ignore', 'pipe', 'pipe'],
                shell: true,
                windowsHide: true,
            });
            server.process = proc;
            server.status.pid = proc.pid;
            // Handle stdout
            proc.stdout?.on('data', (data) => {
                if (this.isDev) {
                    console.log(`[${name}] ${data.toString().trim()}`);
                }
            });
            // Handle stderr
            proc.stderr?.on('data', (data) => {
                const msg = data.toString().trim();
                if (msg && !msg.includes('INFO:') && !msg.includes('DEBUG:')) {
                    console.error(`[${name}] ${msg}`);
                }
            });
            // Handle process exit
            proc.on('exit', (code, signal) => {
                console.log(`[${name}] Process exited with code ${code}, signal ${signal}`);
                server.process = null;
                server.status.pid = undefined;
                if (!this.isShuttingDown && server.config.restartOnCrash) {
                    this.handleCrash(name, code, signal);
                }
                else {
                    server.status.status = 'offline';
                    this.emit('status-change', this.getAllStatuses());
                }
            });
            proc.on('error', (error) => {
                console.error(`[${name}] Process error:`, error);
                server.status.status = 'error';
                server.status.lastError = error.message;
                this.emit('status-change', this.getAllStatuses());
            });
            // Wait for health check
            await this.waitForHealthy(name, server.config.port, 30000);
            server.status.status = 'online';
            console.log(`✅ ${server.config.displayName} started on port ${server.config.port}`);
            this.emit('status-change', this.getAllStatuses());
        }
        catch (error) {
            server.status.status = 'error';
            server.status.lastError = error instanceof Error ? error.message : String(error);
            this.emit('status-change', this.getAllStatuses());
            throw error;
        }
    }
    /**
     * Stop a specific server
     */
    async stopServer(name) {
        const server = this.servers.get(name);
        if (!server || !server.process) {
            return;
        }
        console.log(`🛑 Stopping ${server.config.displayName}...`);
        server.status.status = 'stopping';
        this.emit('status-change', this.getAllStatuses());
        return new Promise((resolve) => {
            const proc = server.process;
            // Set timeout for force kill
            const forceKillTimeout = setTimeout(() => {
                console.log(`⚠️ Force killing ${name}...`);
                proc.kill('SIGKILL');
            }, SHUTDOWN_TIMEOUT);
            proc.once('exit', () => {
                clearTimeout(forceKillTimeout);
                server.process = null;
                server.status.status = 'offline';
                server.status.pid = undefined;
                this.emit('status-change', this.getAllStatuses());
                resolve();
            });
            // Send graceful shutdown signal
            proc.kill('SIGTERM');
        });
    }
    /**
     * Restart a specific server
     */
    async restartServer(name) {
        await this.stopServer(name);
        await this.delay(1000);
        await this.startServer(name);
    }
    /**
     * Restart all servers
     */
    async restartAll() {
        console.log('🔄 Restarting all servers...');
        await this.shutdownAll();
        await this.delay(2000);
        await this.startAll();
    }
    /**
     * Shutdown all servers gracefully
     */
    async shutdownAll() {
        console.log('👋 Shutting down all servers...');
        this.isShuttingDown = true;
        // Stop health check
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
            this.healthCheckInterval = null;
        }
        // Stop all servers in parallel
        const stopPromises = Array.from(this.servers.keys()).map(name => this.stopServer(name).catch(err => {
            console.error(`Error stopping ${name}:`, err);
        }));
        await Promise.all(stopPromises);
        console.log('✅ All servers stopped');
    }
    /**
     * Get all server statuses
     */
    getAllStatuses() {
        return Array.from(this.servers.values()).map(s => ({ ...s.status }));
    }
    /**
     * Get server logs (last N lines)
     */
    getServerLogs(name, lines = 100) {
        // TODO: Implement log buffering
        return [];
    }
    // === Private Methods ===
    async handleCrash(name, code, signal) {
        const server = this.servers.get(name);
        if (!server)
            return;
        server.status.restartCount++;
        server.status.lastError = `Crashed with code ${code}, signal ${signal}`;
        if (server.status.restartCount <= server.config.maxRestarts) {
            console.log(`🔄 Auto-restarting ${name} (attempt ${server.status.restartCount}/${server.config.maxRestarts})...`);
            server.status.status = 'starting';
            this.emit('status-change', this.getAllStatuses());
            await this.delay(2000); // Wait before restart
            try {
                await this.startServer(name);
            }
            catch (error) {
                console.error(`❌ Failed to restart ${name}:`, error);
            }
        }
        else {
            console.error(`❌ ${name} exceeded max restarts (${server.config.maxRestarts})`);
            server.status.status = 'error';
            this.emit('status-change', this.getAllStatuses());
        }
    }
    startHealthCheck() {
        this.healthCheckInterval = setInterval(async () => {
            for (const [name, server] of this.servers) {
                if (server.status.status === 'online') {
                    const healthy = await this.checkHealth(server.config.port);
                    if (!healthy) {
                        console.warn(`⚠️ ${name} health check failed`);
                        // Don't immediately mark as offline, let process exit handler deal with it
                    }
                }
            }
        }, HEALTH_CHECK_INTERVAL);
    }
    async checkHealth(port) {
        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), HEALTH_CHECK_TIMEOUT);
            const response = await fetch(`http://localhost:${port}/health`, {
                signal: controller.signal,
            });
            clearTimeout(timeout);
            return response.ok;
        }
        catch {
            return false;
        }
    }
    async waitForHealthy(name, port, timeout) {
        const startTime = Date.now();
        while (Date.now() - startTime < timeout) {
            if (await this.checkHealth(port)) {
                return;
            }
            await this.delay(1000);
        }
        throw new Error(`${name} did not become healthy within ${timeout}ms`);
    }
    async isPortInUse(port) {
        try {
            const response = await fetch(`http://localhost:${port}/health`, {
                signal: AbortSignal.timeout(2000),
            });
            return response.ok;
        }
        catch {
            return false;
        }
    }
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
//# sourceMappingURL=server-manager.js.map