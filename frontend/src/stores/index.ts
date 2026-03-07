/**
 * JAWIR OS — Zustand State Management
 * Stores for Chat, Agent, UI, and Session state
 */

import { create } from 'zustand';
import type {
  ChatMessage, ReActStep, ReActIteration, ToolResult,
  AgentStatus, TabId, HealthStatus, ToolAnalytics,
} from '@/types';

// ===== Chat Store =====
interface ChatState {
  messages: ChatMessage[];
  addMessage: (msg: ChatMessage) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  clearMessages: () => set({ messages: [] }),
}));

// ===== Agent Store =====
interface AgentState {
  isConnected: boolean;
  status: AgentStatus;
  statusMessage: string;
  // ReAct iterations
  iterations: ReActIteration[];
  currentIteration: number;
  // Tool results
  toolResults: ToolResult[];
  // Actions
  setConnected: (connected: boolean) => void;
  setStatus: (status: AgentStatus, message?: string) => void;
  addReActStep: (step: ReActStep) => void;
  startIteration: (number: number, maxIterations: number) => void;
  addToolResult: (result: ToolResult) => void;
  updateToolResult: (id: string, update: Partial<ToolResult>) => void;
  clearReAct: () => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  isConnected: false,
  status: 'idle',
  statusMessage: '',
  iterations: [],
  currentIteration: 0,
  toolResults: [],

  setConnected: (connected) => set({ isConnected: connected }),

  setStatus: (status, message = '') => set({ status, statusMessage: message }),

  startIteration: (number, maxIterations) => set((s) => ({
    currentIteration: number,
    iterations: [...s.iterations, {
      number,
      maxIterations,
      steps: [],
      timestamp: Date.now(),
    }],
  })),

  addReActStep: (step) => set((s) => {
    const iterations = [...s.iterations];
    if (iterations.length === 0) {
      // Auto-create first iteration if none exists
      iterations.push({ number: 1, maxIterations: 25, steps: [], timestamp: Date.now() });
    }
    const last = { ...iterations[iterations.length - 1] };
    last.steps = [...last.steps, step];
    iterations[iterations.length - 1] = last;
    return { iterations };
  }),

  addToolResult: (result) => set((s) => ({
    toolResults: [result, ...s.toolResults],
  })),

  updateToolResult: (id, update) => set((s) => ({
    toolResults: s.toolResults.map((r) => r.id === id ? { ...r, ...update } : r),
  })),

  clearReAct: () => set({ iterations: [], currentIteration: 0, toolResults: [] }),
}));

// ===== UI Store =====
interface FireAlertData {
  isVisible: boolean;
  deviceName: string;
  room: string;
}

interface UIState {
  activeTab: TabId;
  sidebarCollapsed: boolean;
  showUploadModal: boolean;
  showSettingsModal: boolean;
  fireAlert: FireAlertData;
  setActiveTab: (tab: TabId) => void;
  toggleSidebar: () => void;
  setShowUploadModal: (show: boolean) => void;
  setShowSettingsModal: (show: boolean) => void;
  showFireAlert: (deviceName: string, room: string) => void;
  hideFireAlert: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  activeTab: 'chat',
  sidebarCollapsed: false,
  showUploadModal: false,
  showSettingsModal: false,
  fireAlert: { isVisible: false, deviceName: '', room: '' },
  setActiveTab: (tab) => set({ activeTab: tab }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setShowUploadModal: (show) => set({ showUploadModal: show }),
  setShowSettingsModal: (show) => set({ showSettingsModal: show }),
  showFireAlert: (deviceName, room) => set({ fireAlert: { isVisible: true, deviceName, room } }),
  hideFireAlert: () => set({ fireAlert: { isVisible: false, deviceName: '', room: '' } }),
}));

// ===== Session Store =====
interface SessionState {
  sessionId: string;
  getOrCreateSessionId: () => string;
  resetSession: () => void;
  // Backend status
  health: HealthStatus | null;
  toolAnalytics: ToolAnalytics[];
  setHealth: (h: HealthStatus) => void;
  setToolAnalytics: (a: ToolAnalytics[]) => void;
}

function generateSessionId(): string {
  return crypto.randomUUID();
}

function loadSessionId(): string {
  const stored = localStorage.getItem('jawir_session_id');
  if (stored) return stored;
  const newId = generateSessionId();
  localStorage.setItem('jawir_session_id', newId);
  return newId;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessionId: loadSessionId(),
  health: null,
  toolAnalytics: [],

  getOrCreateSessionId: () => {
    return get().sessionId;
  },

  resetSession: () => {
    const newId = generateSessionId();
    localStorage.setItem('jawir_session_id', newId);
    set({ sessionId: newId });
  },

  setHealth: (h) => set({ health: h }),
  setToolAnalytics: (a) => set({ toolAnalytics: a }),
}));

// ===== Voice Store =====
import type { VoiceMode, VoiceConfig } from '@/types';

interface VoiceStoreState {
  // State
  mode: VoiceMode;
  isEnabled: boolean;
  interimTranscript: string;
  finalTranscript: string;
  error: string | null;
  audioLevel: number;
  
  // Config
  config: VoiceConfig;
  
  // Actions
  setMode: (mode: VoiceMode) => void;
  setEnabled: (enabled: boolean) => void;
  setInterimTranscript: (text: string) => void;
  setFinalTranscript: (text: string) => void;
  clearTranscripts: () => void;
  setError: (error: string | null) => void;
  setAudioLevel: (level: number) => void;
  setConfig: (config: Partial<VoiceConfig>) => void;
}

const DEFAULT_VOICE_CONFIG: VoiceConfig = {
  deepgramApiKey: localStorage.getItem('jawir_deepgram_key') || '',
  language: 'id',
  wakeWordEnabled: false,
  pushToTalkKey: 'Space',
  autoSubmit: true,
  endpointingMs: 500,
};

export const useVoiceStore = create<VoiceStoreState>((set) => ({
  // Initial state
  mode: 'idle',
  isEnabled: !!localStorage.getItem('jawir_deepgram_key'),
  interimTranscript: '',
  finalTranscript: '',
  error: null,
  audioLevel: 0,
  config: DEFAULT_VOICE_CONFIG,
  
  // Actions
  setMode: (mode) => set({ mode }),
  setEnabled: (enabled) => set({ isEnabled: enabled }),
  setInterimTranscript: (text) => set({ interimTranscript: text }),
  setFinalTranscript: (text) => set({ finalTranscript: text }),
  clearTranscripts: () => set({ interimTranscript: '', finalTranscript: '' }),
  setError: (error) => set({ error, mode: error ? 'error' : 'idle' }),
  setAudioLevel: (level) => set({ audioLevel: level }),
  setConfig: (partial) => set((s) => {
    const newConfig = { ...s.config, ...partial };
    // Persist API key
    if (partial.deepgramApiKey !== undefined) {
      localStorage.setItem('jawir_deepgram_key', partial.deepgramApiKey);
    }
    return { config: newConfig, isEnabled: !!newConfig.deepgramApiKey };
  }),
}));


// ===== IoT Store =====
interface IoTDevice {
  device_id: string;
  name: string;
  device_type: 'fan' | 'fire_detector';
  room: string;
  online: boolean;
  last_seen: string | null;
  mode?: 'manual' | 'auto';
  speed?: 'off' | 'low' | 'med' | 'high';
  temperature?: number | null;
  humidity?: number | null;
  gas_analog?: number;
  flame_detected?: boolean;
  alarm_active?: boolean;
}

interface IoTStoreState {
  devices: Record<string, IoTDevice>;
  lastUpdate: number;
  updateDevice: (device: IoTDevice) => void;
  setDevices: (devices: IoTDevice[]) => void;
}

export const useIoTStore = create<IoTStoreState>((set) => ({
  devices: {},
  lastUpdate: 0,
  
  updateDevice: (device) => set((s) => ({
    devices: { ...s.devices, [device.device_id]: device },
    lastUpdate: Date.now(),
  })),
  
  setDevices: (devices) => set({
    devices: devices.reduce((acc, d) => ({ ...acc, [d.device_id]: d }), {}),
    lastUpdate: Date.now(),
  }),
}));
