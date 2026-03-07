/**
 * JAWIR OS — Header Component
 * Gold batik trim bar with logo, status, and actions
 */

import { useAgentStore, useUIStore } from '@/stores';

const STATUS_CONFIG: Record<string, { label: string; icon: string; class: string }> = {
  idle:            { label: 'SIAP',          icon: 'check_circle',   class: 'status-connected' },
  thinking:        { label: 'BERPIKIR',      icon: 'psychology',     class: 'status-thinking' },
  planning:        { label: 'PLANNING',      icon: 'assignment',     class: 'status-thinking' },
  executing_tool:  { label: 'EKSEKUSI',      icon: 'build',          class: 'status-thinking' },
  tool_completed:  { label: 'TOOL SELESAI',  icon: 'check',          class: 'status-connected' },
  searching:       { label: 'MENCARI',       icon: 'travel_explore', class: 'status-thinking' },
  reading:         { label: 'MEMBACA',       icon: 'auto_stories',   class: 'status-thinking' },
  writing:         { label: 'MENULIS',       icon: 'edit_note',      class: 'status-thinking' },
  observation:     { label: 'OBSERVASI',     icon: 'visibility',     class: 'status-thinking' },
  iteration_start: { label: 'ITERASI',       icon: 'replay',         class: 'status-thinking' },
  done:            { label: 'SELESAI',       icon: 'done_all',       class: 'status-connected' },
  error:           { label: 'ERROR',         icon: 'error',          class: 'status-disconnected' },
};

export default function Header() {
  const { isConnected, status } = useAgentStore();
  const { setShowUploadModal, setShowSettingsModal } = useUIStore();

  const getStatusDisplay = () => {
    if (!isConnected) {
      return { label: 'TERPUTUS', icon: 'cloud_off', class: 'status-disconnected' };
    }
    return STATUS_CONFIG[status] || STATUS_CONFIG.idle;
  };

  const statusDisplay = getStatusDisplay();
  const isActive = isConnected && status !== 'idle' && status !== 'done';

  return (
    <header className="flex-none z-50 relative">
      {/* Batik trim */}
      <div className="batik-trim h-1.5 w-full" />

      {/* Header content */}
      <div className="bg-coffee-dark border-b border-coffee-light px-6 py-3 flex items-center justify-between">
        {/* Left: Logo + Title */}
        <div className="flex items-center gap-3">
          <img 
            src="/logo.png" 
            alt="Jawir OS" 
            className="h-10 w-auto drop-shadow-lg"
          />
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Jawir OS</h1>
            <p className="text-[10px] text-cream-muted uppercase tracking-widest">Desktop AI Agent</p>
          </div>
        </div>

        {/* Center: Status */}
        <div className={`status-badge ${statusDisplay.class}`}>
          <span className={`material-symbols-outlined text-sm ${isActive ? 'animate-pulse' : ''}`}>
            {statusDisplay.icon}
          </span>
          <span>{statusDisplay.label}</span>
          {isActive && (
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowUploadModal(true)}
            className="p-2 rounded-lg text-cream-muted hover:text-white hover:bg-coffee-light transition-colors"
            title="Upload File"
          >
            <span className="material-symbols-outlined text-xl">upload_file</span>
          </button>

          <button
            onClick={() => setShowSettingsModal(true)}
            className="p-2 rounded-lg text-cream-muted hover:text-white hover:bg-coffee-light transition-colors"
            title="Settings"
          >
            <span className="material-symbols-outlined text-xl">settings</span>
          </button>

          <div className="h-6 w-px bg-coffee-light mx-2" />

          {/* Avatar */}
          <div className="w-9 h-9 rounded-full bg-primary flex items-center justify-center text-background-dark font-bold text-sm">
            J
          </div>
        </div>
      </div>
    </header>
  );
}
