/**
 * JAWIR OS — Dashboard Panel
 * Backend health, tool analytics, session info, connected services
 */

import { useEffect, useState } from 'react';
import { useAgentStore, useSessionStore } from '@/stores';
import { TOOL_CATEGORIES, TOOL_COUNT } from '@/data/tools';
import type { HealthStatus } from '@/types';

const API_BASE = 'http://localhost:8000';

// Connected external services
const SERVICES = [
  { name: 'GoWA WhatsApp', url: 'http://3.0.50.218:3000', icon: 'chat', color: '#25D366' },
  { name: 'Polinema API', url: 'http://localhost:8001', icon: 'school', color: '#4f46e5' },
  { name: 'Jawir Backend', url: API_BASE, icon: 'dns', color: '#dab80b' },
  { name: 'IoT MQTT', url: 'http://localhost:8000/health/iot', icon: 'sensors', color: '#14b8a6' },
];

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

export default function DashboardPanel() {
  const { isConnected, toolResults, iterations } = useAgentStore();
  const { sessionId, health, setHealth } = useSessionStore();
  const [serviceStatus, setServiceStatus] = useState<Record<string, 'ok' | 'err' | 'loading'>>({});

  // Fetch backend health
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`);
        const data: HealthStatus = await res.json();
        setHealth(data);
      } catch {
        setHealth({ status: 'error', timestamp: Date.now(), version: 'unknown' });
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [setHealth]);

  // Probe external services
  useEffect(() => {
    const checkService = async (url: string, name: string) => {
      setServiceStatus((s) => ({ ...s, [name]: 'loading' }));
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 4000);
        await fetch(url, { signal: controller.signal, mode: 'no-cors' });
        clearTimeout(timeout);
        setServiceStatus((s) => ({ ...s, [name]: 'ok' }));
      } catch {
        setServiceStatus((s) => ({ ...s, [name]: 'err' }));
      }
    };
    SERVICES.forEach((s) => checkService(s.url, s.name));
  }, []);

  // Calculate stats
  const totalSteps = iterations.reduce((acc, it) => acc + it.steps.length, 0);
  const successTools = toolResults.filter((t) => t.status === 'success').length;
  const errorTools = toolResults.filter((t) => t.status === 'error').length;

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Panel Header */}
      <div className="flex-none px-6 py-4 border-b border-coffee-light">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <span className="material-symbols-outlined text-primary icon-filled">dashboard</span>
          Dashboard
        </h2>
        <p className="text-xs text-cream-muted/60 mt-0.5">
          Status sistem & analytics
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatCard icon="build" label="Total Tools" value={TOOL_COUNT} sub={`${TOOL_CATEGORIES.length} kategori`} color="#dab80b" />
          <StatCard icon="bolt" label="Tool Calls" value={toolResults.length} sub={`${successTools} ✓ ${errorTools} ✗`} color="#10b981" />
          <StatCard icon="repeat" label="Iterasi" value={iterations.length} sub={`${totalSteps} langkah`} color="#8b5cf6" />
          <StatCard
            icon="wifi"
            label="WebSocket"
            value={isConnected ? 'Online' : 'Offline'}
            sub={sessionId ? `#${sessionId.slice(0, 8)}` : '-'}
            color={isConnected ? '#10b981' : '#ef4444'}
          />
        </div>

        {/* Backend Health */}
        <div>
          <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-primary">monitor_heart</span>
            Backend Health
          </h3>
          <div className="bg-coffee-medium rounded-xl p-4 border border-coffee-light">
            {health ? (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-cream-muted/60">Status</p>
                  <p className={`text-sm font-bold ${health.status === 'healthy' || health.status === 'ok' ? 'text-green-400' : 'text-red-400'}`}>
                    {health.status === 'healthy' || health.status === 'ok' ? '🟢 Healthy' : '🔴 Unhealthy'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-cream-muted/60">Version</p>
                  <p className="text-sm font-semibold text-white">{health.version || '-'}</p>
                </div>
                {health.agent_model && (
                  <div>
                    <p className="text-xs text-cream-muted/60">AI Model</p>
                    <p className="text-sm font-semibold text-white">{health.agent_model}</p>
                  </div>
                )}
                {health.tools_count !== undefined && (
                  <div>
                    <p className="text-xs text-cream-muted/60">Active Tools</p>
                    <p className="text-sm font-semibold text-white">{health.tools_count}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-sm animate-spin text-cream-muted/40">progress_activity</span>
                <span className="text-sm text-cream-muted/40">Memuat...</span>
              </div>
            )}
          </div>
        </div>

        {/* Connected Services */}
        <div>
          <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-primary">hub</span>
            Connected Services
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {SERVICES.map((svc) => {
              const st = serviceStatus[svc.name] || 'loading';
              return (
                <div
                  key={svc.name}
                  className="bg-coffee-medium rounded-xl p-3 border border-coffee-light flex items-center gap-3"
                >
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center"
                    style={{ background: `${svc.color}15` }}
                  >
                    <span className="material-symbols-outlined icon-filled" style={{ color: svc.color }}>
                      {svc.icon}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-white truncate">{svc.name}</p>
                    <p className="text-[10px] text-cream-muted/40 truncate">{svc.url}</p>
                  </div>
                  <div className="flex-none">
                    {st === 'loading' && (
                      <span className="material-symbols-outlined text-sm animate-spin text-cream-muted/40">progress_activity</span>
                    )}
                    {st === 'ok' && (
                      <span className="w-2.5 h-2.5 rounded-full bg-green-400 inline-block shadow-sm shadow-green-400/50" />
                    )}
                    {st === 'err' && (
                      <span className="w-2.5 h-2.5 rounded-full bg-red-400/60 inline-block" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Tool Usage Breakdown */}
        {toolResults.length > 0 && (
          <div>
            <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-sm text-primary">bar_chart</span>
              Tool Usage (sesi ini)
            </h3>
            <div className="bg-coffee-medium rounded-xl p-4 border border-coffee-light space-y-2">
              {Object.entries(
                toolResults.reduce<Record<string, { count: number; success: number }>>((acc, tr) => {
                  if (!acc[tr.toolName]) acc[tr.toolName] = { count: 0, success: 0 };
                  acc[tr.toolName].count++;
                  if (tr.status === 'success') acc[tr.toolName].success++;
                  return acc;
                }, {})
              )
                .sort(([, a], [, b]) => b.count - a.count)
                .map(([name, stats]) => (
                  <div key={name} className="flex items-center gap-3">
                    <span className="text-xs text-cream-muted w-32 truncate">{name}</span>
                    <div className="flex-1 h-2 rounded-full bg-background-dark overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-primary to-[#bfa10a] rounded-full transition-all"
                        style={{
                          width: `${(stats.count / Math.max(...Object.values(toolResults.reduce<Record<string, number>>((a, t) => ({ ...a, [t.toolName]: (a[t.toolName] || 0) + 1 }), {})).map(Number))) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs text-cream-muted w-12 text-right">{stats.count}×</span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Session Info */}
        <div>
          <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
            <span className="material-symbols-outlined text-sm text-primary">info</span>
            Session Info
          </h3>
          <div className="bg-coffee-medium rounded-xl p-4 border border-coffee-light text-xs text-cream-muted/60 space-y-1 font-mono">
            <p>session_id: {sessionId || '-'}</p>
            <p>websocket: {isConnected ? 'connected' : 'disconnected'}</p>
            <p>backend: {API_BASE}</p>
            <p>frontend: {window.location.origin}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
