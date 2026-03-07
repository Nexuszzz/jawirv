/**
 * JAWIR OS — IoT Dashboard Panel
 * Display and control IoT devices (Fan + Fire Detector)
 * Connected via MQTT to ESP32 devices — ALL DATA FROM BACKEND (no mock)
 * Now with real-time WebSocket updates via useIoTStore
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useIoTStore } from '@/stores';

const API_BASE = 'http://localhost:8000';

// Device types from backend
interface IoTDevice {
    device_id: string;
    name: string;
    type: 'fan' | 'fire_detector';
    room: string;
    online: boolean;
    last_seen: string | null;
    // Fan specific
    mode?: 'manual' | 'auto';
    speed?: 'off' | 'low' | 'med' | 'high';
    // Common — may be null/undefined if DHT invalid or disconnected
    temperature?: number | null;
    // Fire detector specific
    humidity?: number | null;
    gas_analog?: number;
    flame_detected?: boolean;
    alarm_active?: boolean;
}

interface IoTEvent {
    device_id: string;
    event_type: string;
    payload: Record<string, unknown>;
    timestamp: string;
}

interface IoTStats {
    total_devices: number;
    online_devices: number;
    active_alerts: number;
    mqtt_connected: boolean;
    event_count: number;
}

interface IoTHealthResponse {
    status: string;
    message?: string;
    broker?: { status: string; broker: string } | null;
    devices?: IoTStats;
}

/** Safe number display — returns "—" if value is null/undefined/NaN */
function safeNum(value: number | null | undefined, decimals = 1, suffix = ''): string {
    if (value === null || value === undefined || Number.isNaN(value)) return '—';
    return `${value.toFixed(decimals)}${suffix}`;
}

function StatCard({ icon, label, value, sub, color }: {
    icon: string; label: string; value: string | number; sub?: string; color: string;
}) {
    return (
        <div className="bg-coffee-medium rounded-xl p-4 border border-coffee-light hover:border-primary/30 transition-colors">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${color}15` }}>
                    <span className="material-symbols-outlined text-xl icon-filled" style={{ color }}>{icon}</span>
                </div>
                <div className="flex-1 min-w-0">
                    <p className="text-xs text-cream-muted/60 uppercase tracking-wider">{label}</p>
                    <p className="text-xl font-bold text-white">{value}</p>
                    {sub && <p className="text-[10px] text-cream-muted/40">{sub}</p>}
                </div>
            </div>
        </div>
    );
}

function DeviceCard({ device, onAction }: {
    device: IoTDevice;
    onAction: (deviceId: string, action: string, value?: string) => void;
}) {
    const isFan = device.type === 'fan';
    const isFireDetector = device.type === 'fire_detector';

    const speedLevels = ['off', 'low', 'med', 'high'];

    return (
        <div className={`bg-coffee-medium rounded-xl p-4 border ${device.alarm_active ? 'border-red-500 animate-pulse' : 'border-coffee-light'
            }`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${device.online ? 'bg-teal-500/15' : 'bg-gray-500/15'
                        }`}>
                        <span className={`material-symbols-outlined text-xl icon-filled ${device.online ? 'text-teal-400' : 'text-gray-400'
                            }`}>
                            {isFan ? 'mode_fan' : 'local_fire_department'}
                        </span>
                    </div>
                    <div>
                        <p className="text-sm font-semibold text-white">{device.name}</p>
                        <p className="text-[10px] text-cream-muted/40">{device.room} • {device.device_id}</p>
                    </div>
                </div>
                <span className={`w-2.5 h-2.5 rounded-full ${device.online ? 'bg-green-400 shadow-sm shadow-green-400/50' : 'bg-gray-400/60'
                    }`} />
            </div>

            {/* Sensors — NaN-safe via safeNum helper */}
            <div className="grid grid-cols-2 gap-2 mb-4">
                {device.temperature !== undefined && device.temperature !== null && (
                    <div className="bg-background-dark rounded-lg px-3 py-2">
                        <p className="text-[10px] text-cream-muted/40">Suhu</p>
                        <p className="text-sm font-bold text-white">{safeNum(device.temperature, 1, '°C')}</p>
                    </div>
                )}
                {device.humidity !== undefined && device.humidity !== null && (
                    <div className="bg-background-dark rounded-lg px-3 py-2">
                        <p className="text-[10px] text-cream-muted/40">Kelembaban</p>
                        <p className="text-sm font-bold text-white">{safeNum(device.humidity, 0, '%')}</p>
                    </div>
                )}
                {isFireDetector && device.gas_analog !== undefined && (
                    <div className="bg-background-dark rounded-lg px-3 py-2">
                        <p className="text-[10px] text-cream-muted/40">Gas (analog)</p>
                        <p className="text-sm font-bold text-white">{device.gas_analog}</p>
                    </div>
                )}
                {isFan && device.mode && (
                    <div className="bg-background-dark rounded-lg px-3 py-2">
                        <p className="text-[10px] text-cream-muted/40">Mode</p>
                        <p className="text-sm font-bold text-white capitalize">{device.mode}</p>
                    </div>
                )}
            </div>

            {/* Controls */}
            {isFan && (
                <div className="space-y-2">
                    <p className="text-xs text-cream-muted/60">Kecepatan Kipas</p>
                    <div className="grid grid-cols-4 gap-1">
                        {speedLevels.map((speed) => (
                            <button
                                key={speed}
                                onClick={() => onAction(device.device_id, 'set_speed', speed)}
                                disabled={!device.online}
                                className={`py-2 rounded-lg text-xs font-bold transition-all ${device.speed === speed
                                    ? 'bg-primary text-background-dark'
                                    : 'bg-background-dark text-cream-muted hover:bg-coffee-light hover:text-white disabled:opacity-40'
                                    }`}
                            >
                                {speed === 'off' ? 'Off' : speed.toUpperCase()}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {isFireDetector && (
                <div className="space-y-2">
                    {/* Alarm Status */}
                    <div className={`flex items-center justify-between p-3 rounded-lg ${device.alarm_active ? 'bg-red-500/20' : 'bg-background-dark'
                        }`}>
                        <div className="flex items-center gap-2">
                            <span className={`material-symbols-outlined text-lg ${device.alarm_active ? 'text-red-400' : 'text-cream-muted/40'
                                }`}>
                                {device.alarm_active ? 'warning' : 'verified_user'}
                            </span>
                            <span className={`text-sm font-semibold ${device.alarm_active ? 'text-red-400' : 'text-cream-muted'
                                }`}>
                                {device.alarm_active ? 'ALARM AKTIF!' : 'Aman'}
                            </span>
                        </div>
                        {device.alarm_active && (
                            <button
                                onClick={() => onAction(device.device_id, 'buzzer_off')}
                                className="px-3 py-1.5 bg-red-500 text-white text-xs font-bold rounded-lg hover:bg-red-600 transition-colors"
                            >
                                Reset Alarm
                            </button>
                        )}
                    </div>

                    {/* Flame Status */}
                    {device.flame_detected && (
                        <div className="flex items-center gap-2 text-orange-400 text-xs">
                            <span className="material-symbols-outlined text-sm">local_fire_department</span>
                            <span>Api terdeteksi!</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default function IoTPanel() {
    const [health, setHealth] = useState<IoTHealthResponse | null>(null);
    const [devices, setDevices] = useState<IoTDevice[]>([]);
    const [events, setEvents] = useState<IoTEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [fetchError, setFetchError] = useState<string | null>(null);
    const pollRef = useRef<{ device: ReturnType<typeof setInterval> | null; health: ReturnType<typeof setInterval> | null; events: ReturnType<typeof setInterval> | null }>({ device: null, health: null, events: null });

    // Real-time updates from WebSocket via IoT store
    const { devices: wsDevices, lastUpdate: wsLastUpdate } = useIoTStore();
    
    // Merge WebSocket updates into devices state when store updates
    useEffect(() => {
        if (wsLastUpdate > 0 && Object.keys(wsDevices).length > 0) {
            setDevices(prev => prev.map(d => {
                const wsDevice = wsDevices[d.device_id];
                if (wsDevice) {
                    // Merge WebSocket data over existing device
                    return {
                        ...d,
                        mode: wsDevice.mode ?? d.mode,
                        speed: wsDevice.speed ?? d.speed,
                        temperature: wsDevice.temperature ?? d.temperature,
                        humidity: wsDevice.humidity ?? d.humidity,
                        gas_analog: wsDevice.gas_analog ?? d.gas_analog,
                        flame_detected: wsDevice.flame_detected ?? d.flame_detected,
                        alarm_active: wsDevice.alarm_active ?? d.alarm_active,
                        online: wsDevice.online ?? d.online,
                    };
                }
                return d;
            }));
        }
    }, [wsDevices, wsLastUpdate]);

    // Fetch IoT health status
    const fetchHealth = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/health/iot`);
            const data: IoTHealthResponse = await res.json();
            setHealth(data);
            setFetchError(null);
        } catch {
            setHealth({ status: 'error', message: 'Cannot connect to backend' });
            setFetchError('Backend tidak dapat dijangkau');
        }
    }, []);

    // Fetch device list via backend API
    const fetchDevices = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/iot/devices`);
            if (!res.ok) {
                // Fallback if IoT is disabled or API unavailable
                if (res.status === 404) {
                    setDevices([]);
                    return;
                }
                throw new Error('Failed to fetch devices');
            }

            const data = await res.json();

            if (!data.success || !data.devices) {
                setDevices([]);
                return;
            }

            // Map backend response to frontend IoTDevice type
            const deviceList: IoTDevice[] = data.devices.map((d: Record<string, unknown>) => ({
                device_id: d.device_id as string,
                name: d.name as string,
                type: d.device_type as 'fan' | 'fire_detector',
                room: d.room as string,
                online: d.online as boolean,
                last_seen: d.last_seen as string | null,
                // Fan fields
                mode: d.mode as 'manual' | 'auto' | undefined,
                speed: d.speed as 'off' | 'low' | 'med' | 'high' | undefined,
                temperature: d.temperature as number | undefined,
                // Fire detector fields
                humidity: d.humidity as number | undefined,
                gas_analog: d.gas_analog as number | undefined,
                flame_detected: d.flame_detected as boolean | undefined,
                alarm_active: d.alarm_active as boolean | undefined,
            }));

            setDevices(deviceList);
        } catch (error) {
            console.error('Error fetching IoT devices:', error);
            setFetchError('Gagal memuat perangkat IoT');
        } finally {
            setLoading(false);
        }
    }, []);

    // Fetch events from backend API (real events, not just local)
    const fetchEvents = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/iot/events?limit=20`);
            if (!res.ok) return;
            const data = await res.json();
            if (data.success && Array.isArray(data.events) && data.events.length > 0) {
                setEvents(data.events);
            }
        } catch {
            // silent — events are non-critical
        }
    }, []);

    // Handle device action via backend API with OPTIMISTIC UI UPDATE
    const handleAction = useCallback(async (deviceId: string, action: string, value?: string) => {
        setActionLoading(true);
        
        // OPTIMISTIC UI UPDATE: immediately update local state for instant feedback
        if (action === 'set_speed' && value) {
            setDevices(prev => prev.map(d => 
                d.device_id === deviceId ? { ...d, speed: value as 'off' | 'low' | 'med' | 'high' } : d
            ));
        } else if (action === 'set_mode' && value) {
            setDevices(prev => prev.map(d => 
                d.device_id === deviceId ? { ...d, mode: value as 'manual' | 'auto' } : d
            ));
        } else if (action === 'buzzer_off' || action === 'reset') {
            setDevices(prev => prev.map(d => 
                d.device_id === deviceId ? { ...d, alarm_active: false } : d
            ));
        }
        
        try {
            const res = await fetch(`${API_BASE}/api/iot/devices/${deviceId}/control`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action, value }),
            });

            if (!res.ok) {
                const error = await res.json();
                console.error('IoT Action failed:', error);
                // Revert optimistic update on failure
                await fetchDevices();
                throw new Error(error.detail || 'Control command failed');
            }

            const result = await res.json();
            console.log(`IoT Action success: ${result.message}`);

            // Quick re-fetch after 500ms to confirm ESP32 response, then again at 2s
            setTimeout(fetchDevices, 500);
            setTimeout(fetchDevices, 2000);

        } catch (error) {
            console.error('IoT Action failed:', error);
            // Revert on error
            await fetchDevices();
        } finally {
            setActionLoading(false);
        }
    }, [fetchDevices]);

    // Initial fetch and polling
    useEffect(() => {
        fetchHealth();
        fetchDevices();
        fetchEvents();

        // Optimised polling: devices 5s, health 30s, events 10s
        pollRef.current.device = setInterval(fetchDevices, 5000);
        pollRef.current.health = setInterval(fetchHealth, 30000);
        pollRef.current.events = setInterval(fetchEvents, 10000);

        return () => {
            if (pollRef.current.device) clearInterval(pollRef.current.device);
            if (pollRef.current.health) clearInterval(pollRef.current.health);
            if (pollRef.current.events) clearInterval(pollRef.current.events);
        };
    }, [fetchHealth, fetchDevices, fetchEvents]);

    const isDisabled = health?.status === 'disabled';
    const isConnected = health?.status === 'connected';
    const stats = health?.devices;

    return (
        <div className="flex-1 flex flex-col min-h-0">
            {/* Panel Header */}
            <div className="flex-none px-6 py-4 border-b border-coffee-light">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary icon-filled">sensors</span>
                    IoT Dashboard
                </h2>
                <p className="text-xs text-cream-muted/60 mt-0.5">
                    Kontrol kipas & monitoring deteksi api
                </p>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">

                {/* Backend Unreachable Banner */}
                {fetchError && !isDisabled && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
                        <div className="flex items-start gap-3">
                            <span className="material-symbols-outlined text-red-400">cloud_off</span>
                            <div>
                                <p className="text-sm font-semibold text-red-400">Koneksi Bermasalah</p>
                                <p className="text-xs text-cream-muted/60 mt-1">{fetchError}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* IoT Disabled Warning */}
                {isDisabled && (
                    <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
                        <div className="flex items-start gap-3">
                            <span className="material-symbols-outlined text-amber-400">info</span>
                            <div>
                                <p className="text-sm font-semibold text-amber-400">IoT Non-aktif</p>
                                <p className="text-xs text-cream-muted/60 mt-1">
                                    Set <code className="bg-background-dark px-1 rounded">IOT_ENABLED=true</code> di file .env backend untuk mengaktifkan fitur IoT.
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Stats Grid */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <StatCard
                        icon="devices"
                        label="Perangkat"
                        value={stats?.total_devices ?? devices.length}
                        sub={`${stats?.online_devices ?? 0} online`}
                        color="#14b8a6"
                    />
                    <StatCard
                        icon="wifi"
                        label="MQTT"
                        value={isConnected ? 'Terhubung' : isDisabled ? 'Disabled' : 'Offline'}
                        sub={health?.broker?.broker ?? '-'}
                        color={isConnected ? '#10b981' : isDisabled ? '#f59e0b' : '#ef4444'}
                    />
                    <StatCard
                        icon="warning"
                        label="Alert Aktif"
                        value={stats?.active_alerts ?? 0}
                        color={stats?.active_alerts ? '#ef4444' : '#6b7280'}
                    />
                    <StatCard
                        icon="history"
                        label="Event"
                        value={stats?.event_count ?? events.length}
                        sub="dari backend"
                        color="#8b5cf6"
                    />
                </div>

                {/* Device Cards */}
                <div>
                    <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                        <span className="material-symbols-outlined text-sm text-primary">home_iot_device</span>
                        Perangkat IoT
                    </h3>

                    {loading ? (
                        <div className="flex items-center gap-2 text-cream-muted/40">
                            <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                            <span className="text-sm">Memuat...</span>
                        </div>
                    ) : devices.length === 0 ? (
                        <div className="bg-coffee-medium rounded-xl p-6 text-center">
                            <span className="material-symbols-outlined text-4xl text-cream-muted/20 mb-2">devices_off</span>
                            <p className="text-sm text-cream-muted/40">Belum ada perangkat terhubung</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            {devices.map((device) => (
                                <DeviceCard
                                    key={device.device_id}
                                    device={device}
                                    onAction={handleAction}
                                />
                            ))}
                        </div>
                    )}
                </div>

                {/* Recent Events — fetched from backend /api/iot/events */}
                <div>
                    <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                        <span className="material-symbols-outlined text-sm text-primary">timeline</span>
                        Event Terbaru
                    </h3>
                    {events.length === 0 ? (
                        <div className="bg-coffee-medium rounded-xl p-4 text-center">
                            <p className="text-xs text-cream-muted/40">Belum ada event</p>
                        </div>
                    ) : (
                        <div className="bg-coffee-medium rounded-xl border border-coffee-light divide-y divide-coffee-light">
                            {events.slice(0, 8).map((event, idx) => (
                                <div key={idx} className="px-4 py-3 flex items-center gap-3">
                                    <span className="material-symbols-outlined text-sm text-cream-muted/40">
                                        {event.event_type.includes('alarm') ? 'warning' :
                                            event.event_type.includes('speed') ? 'speed' : 'sensors'}
                                    </span>
                                    <div className="flex-1">
                                        <p className="text-xs text-white">{event.device_id}: {event.event_type}</p>
                                        <p className="text-[10px] text-cream-muted/40">
                                            {new Date(event.timestamp).toLocaleTimeString('id-ID')}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Action Loading Overlay */}
                {actionLoading && (
                    <div className="fixed inset-0 bg-black/20 flex items-center justify-center z-50">
                        <div className="bg-coffee-medium rounded-xl p-4 flex items-center gap-3">
                            <span className="material-symbols-outlined animate-spin text-primary">progress_activity</span>
                            <span className="text-sm text-white">Mengirim perintah...</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
