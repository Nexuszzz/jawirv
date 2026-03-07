/**
 * JAWIR OS — Push-to-Talk Voice Button
 * Hold to record, release to send.
 * Uses PointerCapture so the hold never breaks even when button
 * transforms (scale, pulse) or pointer drifts off the element.
 */

import React, { useState, useRef, useEffect } from 'react';

interface VoiceButtonProps {
  onStartRecording: () => void;
  onStopRecording: () => void;
  disabled?: boolean;
  isRecording?: boolean;
  audioLevel?: number;
}

const VoiceButton: React.FC<VoiceButtonProps> = ({
  onStartRecording,
  onStopRecording,
  disabled = false,
  isRecording = false,
  audioLevel = 0,
}) => {
  const [isPressing, setIsPressing] = useState(false);
  const pressTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const didStartRef = useRef(false);
  const activePointerRef = useRef<number | null>(null);
  const btnRef = useRef<HTMLButtonElement>(null);

  // ── Pointer down: capture + start ──
  const handlePointerDown = (e: React.PointerEvent<HTMLButtonElement>) => {
    console.log('[VoiceBtn] PointerDown. disabled:', disabled, 'activePointer:', activePointerRef.current);
    if (disabled || activePointerRef.current !== null) return;
    e.preventDefault();

    // Lock all future pointer events to this button
    btnRef.current?.setPointerCapture(e.pointerId);
    activePointerRef.current = e.pointerId;
    setIsPressing(true);
    didStartRef.current = false;

    // Require 150ms hold to avoid accidental taps
    pressTimerRef.current = setTimeout(() => {
      console.log('[VoiceBtn] 150ms hold passed, calling onStartRecording');
      didStartRef.current = true;
      onStartRecording();
    }, 150);
  };

  // ── Pointer up / cancel: stop ──
  const handlePointerUp = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (e.pointerId !== activePointerRef.current) return;
    finish();
  };

  const handlePointerCancel = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (e.pointerId !== activePointerRef.current) return;
    finish();
  };

  const finish = () => {
    console.log('[VoiceBtn] finish() called. didStart:', didStartRef.current);
    activePointerRef.current = null;
    setIsPressing(false);

    if (pressTimerRef.current) {
      clearTimeout(pressTimerRef.current);
      pressTimerRef.current = null;
    }

    if (didStartRef.current) {
      didStartRef.current = false;
      console.log('[VoiceBtn] Calling onStopRecording');
      onStopRecording();
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pressTimerRef.current) clearTimeout(pressTimerRef.current);
    };
  }, []);

  // Animated waveform bars
  const bars = 5;
  const barHeights = Array.from({ length: bars }, (_, i) => {
    const base = isRecording ? 12 : 4;
    const wave = isRecording ? Math.sin(Date.now() / 200 + i) * 8 * Math.max(0.3, audioLevel) : 0;
    return base + wave;
  });

  return (
    <div className="relative inline-flex items-center justify-center">
      {/* Pulse ring when recording */}
      {isRecording && (
        <span className="absolute inset-0 rounded-full bg-red-500/30 animate-ping pointer-events-none" />
      )}

      <button
        ref={btnRef}
        type="button"
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerCancel}
        onContextMenu={(e) => e.preventDefault()}
        disabled={disabled}
        style={{ touchAction: 'none' }}
        className={`
          relative z-10 flex items-center justify-center
          w-12 h-12 rounded-full
          transition-all duration-200 select-none
          ${disabled
            ? 'bg-coffee-medium/30 text-coffee-text/30 cursor-not-allowed'
            : isRecording
              ? 'bg-red-600 text-white shadow-lg shadow-red-600/40 scale-110'
              : isPressing
                ? 'bg-coffee-gold/80 text-coffee-dark scale-105'
                : 'bg-coffee-medium/60 text-coffee-gold hover:bg-coffee-medium/80 hover:scale-105'
          }
        `}
        title={disabled ? 'Set Deepgram API key di Settings' : 'Tahan untuk bicara'}
      >
        {isRecording ? (
          /* Waveform bars */
          <div className="flex items-center gap-[2px] h-5">
            {barHeights.map((h, i) => (
              <div
                key={i}
                className="w-[3px] rounded-full bg-white transition-all duration-100"
                style={{ height: `${h}px` }}
              />
            ))}
          </div>
        ) : (
          /* Mic icon */
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="9" y="1" width="6" height="11" rx="3" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="8" y1="23" x2="16" y2="23" />
          </svg>
        )}
      </button>

      {/* Recording duration indicator */}
      {isRecording && (
        <RecordingTimer />
      )}
    </div>
  );
};

/** Little timer that counts up while recording */
const RecordingTimer: React.FC = () => {
  const [seconds, setSeconds] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => setSeconds(s => s + 1), 1000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, []);

  const m = Math.floor(seconds / 60);
  const s = seconds % 60;

  return (
    <span className="absolute -bottom-5 text-[10px] text-red-400 font-mono tabular-nums">
      {m}:{s.toString().padStart(2, '0')}
    </span>
  );
};

export default VoiceButton;
