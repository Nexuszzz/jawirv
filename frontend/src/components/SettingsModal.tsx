/**
 * JAWIR OS — Settings Modal
 * Backend configuration, voice settings, and preferences
 */

import { useState, useEffect } from 'react';
import { useUIStore, useSessionStore, useChatStore, useAgentStore, useVoiceStore } from '@/stores';

const API_BASE = 'http://localhost:8000';

interface SettingToggle {
  label: string;
  description: string;
  icon: string;
  value: boolean;
  onChange: (v: boolean) => void;
}

export default function SettingsModal() {
  const { showSettingsModal, setShowSettingsModal } = useUIStore();
  const { sessionId, resetSession } = useSessionStore();
  const { clearMessages } = useChatStore();
  const { clearReAct } = useAgentStore();
  const { config, setConfig, isEnabled } = useVoiceStore();

  const [soundEnabled, setSoundEnabled] = useState(() => localStorage.getItem('jawir_sound') !== 'false');
  const [compactMode, setCompactMode] = useState(() => localStorage.getItem('jawir_compact') === 'true');
  const [backendInfo, setBackendInfo] = useState<Record<string, unknown> | null>(null);
  
  // Voice settings local state
  const [deepgramKey, setDeepgramKey] = useState(config.deepgramApiKey);
  const [voiceLanguage, setVoiceLanguage] = useState(config.language);

  useEffect(() => {
    if (showSettingsModal) {
      fetch(`${API_BASE}/health`)
        .then(r => r.json())
        .then(setBackendInfo)
        .catch(() => setBackendInfo(null));
    }
  }, [showSettingsModal]);

  const handleToggle = (key: string, value: boolean, setter: (v: boolean) => void) => {
    setter(value);
    localStorage.setItem(`jawir_${key}`, String(value));
  };

  const handleClearSession = () => {
    clearMessages();
    clearReAct();
    resetSession();
  };

  const toggles: SettingToggle[] = [
    {
      label: 'Notifikasi Suara',
      description: 'Mainkan suara saat agent selesai merespon',
      icon: 'volume_up',
      value: soundEnabled,
      onChange: (v) => handleToggle('sound', v, setSoundEnabled),
    },
    {
      label: 'Mode Kompak',
      description: 'Tampilkan chat dengan jarak lebih rapat',
      icon: 'density_small',
      value: compactMode,
      onChange: (v) => handleToggle('compact', v, setCompactMode),
    },
  ];

  if (!showSettingsModal) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-coffee-dark rounded-2xl border border-coffee-light w-full max-w-lg mx-4 shadow-2xl animate-slide-in-right max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-coffee-light flex-none">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span className="material-symbols-outlined text-primary icon-filled">settings</span>
            Pengaturan
          </h3>
          <button onClick={() => setShowSettingsModal(false)} className="p-1 rounded-lg hover:bg-coffee-medium transition-colors">
            <span className="material-symbols-outlined text-cream-muted">close</span>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Toggles */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-cream-muted/60 uppercase tracking-wider">Preferensi</h4>
            {toggles.map((t) => (
              <div key={t.label} className="flex items-center justify-between p-3 rounded-xl bg-coffee-medium border border-coffee-light">
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-primary">{t.icon}</span>
                  <div>
                    <p className="text-sm font-semibold text-white">{t.label}</p>
                    <p className="text-[11px] text-cream-muted/60">{t.description}</p>
                  </div>
                </div>
                <label className="toggle-switch">
                  <input type="checkbox" checked={t.value} onChange={(e) => t.onChange(e.target.checked)} />
                  <span className="toggle-slider" />
                </label>
              </div>
            ))}
          </div>

          {/* Voice Settings */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-cream-muted/60 uppercase tracking-wider flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">mic</span>
              Voice Input (Deepgram)
            </h4>
            <div className="p-4 rounded-xl bg-coffee-medium border border-coffee-light space-y-4">
              {/* API Key Input */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-cream-muted">Deepgram API Key</label>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={deepgramKey}
                    onChange={(e) => setDeepgramKey(e.target.value)}
                    placeholder="Masukkan API key dari deepgram.com"
                    className="flex-1 px-3 py-2 bg-coffee-dark rounded-lg border border-coffee-light text-sm text-white placeholder:text-cream-muted/40 focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                  <button
                    onClick={() => setConfig({ deepgramApiKey: deepgramKey })}
                    className="px-3 py-2 rounded-lg bg-primary text-background-dark text-xs font-bold hover:bg-primary-hover transition-colors"
                  >
                    Simpan
                  </button>
                </div>
                <p className="text-[10px] text-cream-muted/50">
                  Dapatkan API key gratis di{' '}
                  <a href="https://deepgram.com" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    deepgram.com
                  </a>
                  {' '}($200 free credit)
                </p>
              </div>
              
              {/* Language Selection */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-cream-muted">Bahasa Voice</label>
                <div className="flex gap-2">
                  {[
                    { value: 'id', label: '🇮🇩 Indonesia' },
                    { value: 'en', label: '🇺🇸 English' },
                    { value: 'multi', label: '🌐 Multi' },
                  ].map((lang) => (
                    <button
                      key={lang.value}
                      onClick={() => {
                        setVoiceLanguage(lang.value as typeof voiceLanguage);
                        setConfig({ language: lang.value as typeof voiceLanguage });
                      }}
                      className={`flex-1 px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                        voiceLanguage === lang.value
                          ? 'bg-primary text-background-dark'
                          : 'bg-coffee-dark border border-coffee-light text-cream-muted hover:border-primary'
                      }`}
                    >
                      {lang.label}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Status */}
              <div className="flex items-center gap-2 pt-2 border-t border-coffee-light">
                <div className={`w-2 h-2 rounded-full ${isEnabled ? 'bg-green-400' : 'bg-red-400'}`} />
                <span className="text-xs text-cream-muted">
                  {isEnabled ? 'Voice aktif - tekan tombol mic atau Space untuk bicara' : 'Voice tidak aktif - masukkan API key'}
                </span>
              </div>
            </div>
          </div>

          {/* Backend Info */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-cream-muted/60 uppercase tracking-wider">Backend Info</h4>
            <div className="p-3 rounded-xl bg-coffee-medium border border-coffee-light text-xs font-mono text-cream-muted/60 space-y-1">
              {backendInfo ? (
                Object.entries(backendInfo).map(([key, val]) => (
                  <p key={key}>
                    <span className="text-cream-muted">{key}</span>: {String(val)}
                  </p>
                ))
              ) : (
                <p className="text-cream-muted/40">Memuat info backend...</p>
              )}
            </div>
          </div>

          {/* Session Management */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-cream-muted/60 uppercase tracking-wider">Sesi</h4>
            <div className="p-3 rounded-xl bg-coffee-medium border border-coffee-light space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-white">Session ID</p>
                  <p className="text-[10px] text-cream-muted/40 font-mono">{sessionId || 'Belum ada'}</p>
                </div>
              </div>
              <button
                onClick={handleClearSession}
                className="w-full py-2 px-3 rounded-lg bg-red-500/10 border border-red-500/30 text-sm text-red-400 font-semibold hover:bg-red-500/20 transition-colors flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-sm">delete_sweep</span>
                Reset Sesi (hapus chat & ReAct)
              </button>
            </div>
          </div>

          {/* About */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-cream-muted/60 uppercase tracking-wider">Tentang</h4>
            <div className="p-4 rounded-xl bg-coffee-medium border border-coffee-light text-center">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-[#bfa10a] flex items-center justify-center mx-auto mb-2 shadow-lg shadow-primary/20">
                <span className="material-symbols-outlined text-background-dark text-xl icon-filled">spa</span>
              </div>
              <p className="text-sm font-bold text-white">Jawir OS</p>
              <p className="text-[10px] text-cream-muted/60">Desktop AI Agent • 30 Tools • ReAct Loop</p>
              <p className="text-[10px] text-cream-muted/40 mt-1">Gemini AI × LangGraph × FastAPI</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
