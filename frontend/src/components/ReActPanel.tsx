/**
 * JAWIR OS — ReAct Panel
 * Visualisasi ReAct Loop: Iteration → Steps (Thinking → Planning → Executing → Observation → Done)
 */

import { useAgentStore } from '@/stores';
import type { ReActStep } from '@/types';

const STEP_CONFIG: Record<string, { icon: string; label: string; color: string; bg: string }> = {
  thinking:       { icon: 'psychology',       label: 'Berpikir',     color: 'text-blue-400',   bg: 'bg-blue-400/10' },
  planning:       { icon: 'route',            label: 'Merencanakan', color: 'text-violet-400', bg: 'bg-violet-400/10' },
  executing_tool: { icon: 'build',            label: 'Menjalankan',  color: 'text-primary',    bg: 'bg-primary/10' },
  searching:      { icon: 'travel_explore',   label: 'Mencari',      color: 'text-emerald-400',bg: 'bg-emerald-400/10' },
  reading:        { icon: 'menu_book',        label: 'Membaca',      color: 'text-cyan-400',   bg: 'bg-cyan-400/10' },
  writing:        { icon: 'edit_note',        label: 'Menulis',      color: 'text-amber-400',  bg: 'bg-amber-400/10' },
  observation:    { icon: 'visibility',       label: 'Observasi',    color: 'text-orange-400', bg: 'bg-orange-400/10' },
  done:           { icon: 'check_circle',     label: 'Selesai',      color: 'text-green-400',  bg: 'bg-green-400/10' },
  error:          { icon: 'error',            label: 'Error',        color: 'text-red-400',    bg: 'bg-red-400/10' },
};

function StepCard({ step, index }: { step: ReActStep; index: number }) {
  const config = STEP_CONFIG[step.type] || STEP_CONFIG.thinking;

  return (
    <div className="react-step animate-step-enter" style={{ animationDelay: `${index * 80}ms` }}>
      <div className="flex items-start gap-3">
        {/* Step icon */}
        <div className={`flex-none w-8 h-8 rounded-lg ${config.bg} flex items-center justify-center`}>
          <span className={`material-symbols-outlined text-lg ${config.color} icon-filled`}>{config.icon}</span>
        </div>

        <div className="flex-1 min-w-0">
          {/* Step header */}
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-semibold uppercase tracking-wider ${config.color}`}>
              {config.label}
            </span>
            {step.toolName && (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-coffee-medium text-cream-muted border border-coffee-light">
                🔧 {step.toolName}
              </span>
            )}
            {step.duration && (
              <span className="text-[10px] text-cream-muted/50 ml-auto">
                {step.duration}ms
              </span>
            )}
          </div>

          {/* Step content */}
          {step.content && (
            <div className="text-sm text-cream-muted leading-relaxed whitespace-pre-wrap break-words">
              {step.content.length > 500 ? step.content.slice(0, 500) + '...' : step.content}
            </div>
          )}

          {/* Tool result preview */}
          {step.result !== undefined && step.result !== null && (
            <div className="mt-2 p-2.5 rounded-lg bg-background-dark/50 border border-coffee-light/50 text-xs text-cream-muted font-mono overflow-x-auto">
              {typeof step.result === 'string'
                ? step.result.slice(0, 300)
                : JSON.stringify(step.result, null, 2).slice(0, 300)}
              {(typeof step.result === 'string' ? step.result.length : JSON.stringify(step.result).length) > 300 ? '...' : null}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function IterationBlock({ iteration }: { iteration: { number: number; maxIterations: number; steps: ReActStep[] } }) {
  const progressPercent = iteration.maxIterations > 0
    ? Math.round((iteration.number / iteration.maxIterations) * 100)
    : 0;

  return (
    <div className="react-iteration animate-slide-in-right">
      {/* Iteration header */}
      <div className="flex items-center gap-3 mb-4 pb-3 border-b border-coffee-light/50">
        <div className="flex-none w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-[#bfa10a] flex items-center justify-center shadow-lg shadow-primary/20">
          <span className="text-sm font-bold text-background-dark">#{iteration.number}</span>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-bold text-white">Iterasi {iteration.number}</h3>
          <p className="text-[11px] text-cream-muted/60">
            {iteration.steps.length} langkah • max {iteration.maxIterations}
          </p>
        </div>
        {/* Mini progress bar */}
        <div className="w-20 h-1.5 rounded-full bg-background-dark overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary to-[#bfa10a] rounded-full transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3 ml-1">
        {/* Timeline connector line */}
        <div className="relative">
          <div className="absolute left-[15px] top-0 bottom-0 w-px bg-gradient-to-b from-coffee-light to-transparent" />
          <div className="space-y-3 relative">
            {iteration.steps.map((step, idx) => (
              <StepCard key={idx} step={step} index={idx} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ReActPanel() {
  const { iterations, status, statusMessage, toolResults } = useAgentStore();

  const isActive = !['idle', 'done', 'error', 'disconnected'].includes(status);

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Panel Header */}
      <div className="flex-none px-6 py-4 border-b border-coffee-light">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-primary icon-filled">account_tree</span>
              ReAct Loop
            </h2>
            <p className="text-xs text-cream-muted/60 mt-0.5">
              Visualisasi proses berpikir & aksi agent
            </p>
          </div>

          {/* Live indicator */}
          {isActive && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/30">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="text-xs text-primary font-medium">{statusMessage || 'Processing...'}</span>
            </div>
          )}
        </div>

        {/* Summary stats */}
        {(iterations.length > 0 || toolResults.length > 0) && (
          <div className="flex gap-4 mt-3">
            <div className="flex items-center gap-1.5 text-xs text-cream-muted/60">
              <span className="material-symbols-outlined text-sm">repeat</span>
              {iterations.length} iterasi
            </div>
            <div className="flex items-center gap-1.5 text-xs text-cream-muted/60">
              <span className="material-symbols-outlined text-sm">build</span>
              {toolResults.length} tool calls
            </div>
            <div className="flex items-center gap-1.5 text-xs text-cream-muted/60">
              <span className="material-symbols-outlined text-sm">footprint</span>
              {iterations.reduce((acc, it) => acc + it.steps.length, 0)} langkah
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {/* Empty state */}
        {iterations.length === 0 && !isActive && (
          <div className="flex-1 flex flex-col items-center justify-center h-full text-center py-20">
            <div className="w-16 h-16 rounded-2xl bg-coffee-medium flex items-center justify-center mb-4">
              <span className="material-symbols-outlined text-cream-muted/40 text-3xl">account_tree</span>
            </div>
            <h3 className="text-base font-bold text-white mb-1">Belum ada ReAct Loop</h3>
            <p className="text-sm text-cream-muted/60 max-w-sm">
              Kirim pesan di tab Chat untuk melihat proses berpikir agent secara real-time
            </p>
          </div>
        )}

        {/* Iteration list */}
        {iterations.map((iteration, idx) => (
          <IterationBlock key={idx} iteration={iteration} />
        ))}

        {/* Active processing pulse */}
        {isActive && iterations.length > 0 && (
          <div className="flex items-center gap-3 p-4 rounded-xl border border-dashed border-primary/30 bg-primary/5">
            <div className="relative">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <span className="material-symbols-outlined text-primary text-sm animate-spin">progress_activity</span>
              </div>
              <div className="absolute inset-0 rounded-full animate-pulse-ring" />
            </div>
            <span className="text-sm text-cream-muted">{statusMessage || 'Agent sedang berpikir...'}</span>
          </div>
        )}
      </div>
    </div>
  );
}
