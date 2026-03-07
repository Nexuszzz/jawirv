/**
 * JAWIR OS — Voice Manager Hook
 * Central controller: connects VoiceButton ↔ Deepgram ↔ ChatPanel
 * Now with Wake Word detection: say "Jawir" to activate voice input!
 * 
 * Usage in ChatPanel:
 *   const { startRecording, stopRecording, isRecording, ... } = useVoiceManager({
 *     onTranscriptReady: (text) => sendToJawir(text),
 *   });
 */

import { useCallback, useRef, useEffect } from 'react';
import { useVoiceStore } from '@/stores';
import { useDeepgram } from './useDeepgram';
import { useWakeWord } from './useWakeWord';
import type { VoiceMode } from '@/types';

interface UseVoiceManagerOptions {
  onTranscriptReady?: (transcript: string) => void;
  onError?: (error: string) => void;
}

interface UseVoiceManagerReturn {
  mode: VoiceMode;
  isEnabled: boolean;
  isRecording: boolean;
  isWakeWordListening: boolean;
  isWakeWordSupported: boolean;
  interimTranscript: string;
  finalTranscript: string;
  audioLevel: number;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  cancelRecording: () => void;
  startWakeWordListening: () => void;
  stopWakeWordListening: () => void;
  toggleWakeWord: () => void;
}

export function useVoiceManager(options: UseVoiceManagerOptions = {}): UseVoiceManagerReturn {
  const { onTranscriptReady, onError } = options;
  
  // Keep callback refs fresh
  const onTranscriptReadyRef = useRef(onTranscriptReady);
  const onErrorRef = useRef(onError);
  onTranscriptReadyRef.current = onTranscriptReady;
  onErrorRef.current = onError;
  
  const {
    mode, isEnabled, interimTranscript, finalTranscript,
    audioLevel, error, config, setMode, clearTranscripts, setError, setConfig,
  } = useVoiceStore();
  
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const shouldResumeWakeWordRef = useRef(false);

  // Wake word detection - triggers when user says "Jawir"
  const {
    isListening: isWakeWordListening,
    isSupported: isWakeWordSupported,
    startListening: startWakeWord,
    stopListening: stopWakeWord,
    pauseListening: pauseWakeWord,
    resumeListening: resumeWakeWord,
  } = useWakeWord({
    onWakeWord: () => {
      console.log('[VoiceManager] 🎤 Wake word detected! Starting recording...');
      shouldResumeWakeWordRef.current = true; // Remember to resume after recording
      handleWakeWordTrigger();
    },
    onError: (err) => {
      console.warn('[VoiceManager] Wake word error:', err);
    },
  });

  // Deepgram - onFinalResult fires when recording stops and transcript is ready
  const { startListening, stopListening, cancelListening } = useDeepgram({
    onFinalResult: (text) => {
      console.log('[VoiceManager] Got final result:', text);
      if (text.trim()) {
        onTranscriptReadyRef.current?.(text.trim());
      }
      clearTranscripts();
      
      // Resume wake word listening if it was active before
      if (shouldResumeWakeWordRef.current && config.wakeWordEnabled) {
        console.log('[VoiceManager] Resuming wake word listening...');
        setTimeout(() => {
          resumeWakeWord();
        }, 500); // Small delay to ensure mic is released
      }
    },
    onError: (err) => {
      onErrorRef.current?.(err);
    },
  });

  // Start recording
  const startRecording = useCallback(async () => {
    console.log('[VoiceManager] startRecording called. isEnabled:', isEnabled, 'mode:', mode, 'config.apiKey:', config.deepgramApiKey ? 'SET' : 'EMPTY');
    
    // Check API key directly from config (more reliable than isEnabled flag)
    if (!config.deepgramApiKey) {
      const msg = 'Voice tidak aktif. Masukkan Deepgram API key di Settings (⚙️).';
      console.warn('[VoiceManager]', msg);
      setError(msg);
      onErrorRef.current?.(msg);
      return;
    }
    if (mode === 'recording' || mode === 'processing') {
      console.log('[VoiceManager] Already recording/processing, skip');
      return;
    }
    
    // Pause wake word listening while recording (to release mic)
    if (isWakeWordListening) {
      pauseWakeWord();
    }
    
    clearTranscripts();
    
    // Max 60s recording
    timeoutRef.current = setTimeout(() => {
      console.log('[VoiceManager] Max time reached, stopping');
      stopRecording();
    }, 60000);
    
    console.log('[VoiceManager] Calling startListening...');
    await startListening();
    console.log('[VoiceManager] startListening returned');
  }, [isEnabled, mode, config.deepgramApiKey, clearTranscripts, startListening, setError, isWakeWordListening, pauseWakeWord]);

  // Handle wake word trigger - start recording automatically
  const handleWakeWordTrigger = useCallback(async () => {
    console.log('[VoiceManager] handleWakeWordTrigger called');
    
    if (!config.deepgramApiKey) {
      const msg = 'Deepgram API key tidak ada. Voice trigger tidak bisa diproses.';
      console.warn('[VoiceManager]', msg);
      setError(msg);
      return;
    }
    
    // Start recording immediately
    clearTranscripts();
    
    // Auto-stop after 15 seconds for wake word triggered recording
    timeoutRef.current = setTimeout(() => {
      console.log('[VoiceManager] Wake word recording timeout, stopping');
      stopRecording();
    }, 15000);
    
    console.log('[VoiceManager] Starting Deepgram after wake word...');
    await startListening();
  }, [config.deepgramApiKey, clearTranscripts, startListening, setError]);

  // Stop recording → triggers Deepgram to flush → onFinalResult fires → submits
  const stopRecording = useCallback(() => {
    console.log('[VoiceManager] stopRecording called');
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    stopListening();
  }, [stopListening]);

  // Cancel without submitting
  const cancelRecording = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    cancelListening();
    clearTranscripts();
    setMode('idle');
    
    // Resume wake word if it was enabled
    if (config.wakeWordEnabled) {
      setTimeout(() => resumeWakeWord(), 500);
    }
  }, [cancelListening, clearTranscripts, setMode, config.wakeWordEnabled, resumeWakeWord]);

  // Start wake word listening
  const startWakeWordListening = useCallback(() => {
    if (!isWakeWordSupported) {
      setError('Wake word tidak didukung di browser ini. Gunakan Chrome atau Edge.');
      return;
    }
    console.log('[VoiceManager] Starting wake word listening...');
    setConfig({ wakeWordEnabled: true });
    startWakeWord();
  }, [isWakeWordSupported, setConfig, startWakeWord, setError]);

  // Stop wake word listening
  const stopWakeWordListening = useCallback(() => {
    console.log('[VoiceManager] Stopping wake word listening...');
    setConfig({ wakeWordEnabled: false });
    stopWakeWord();
    shouldResumeWakeWordRef.current = false;
  }, [setConfig, stopWakeWord]);

  // Toggle wake word
  const toggleWakeWord = useCallback(() => {
    if (config.wakeWordEnabled) {
      stopWakeWordListening();
    } else {
      startWakeWordListening();
    }
  }, [config.wakeWordEnabled, startWakeWordListening, stopWakeWordListening]);

  // Auto-start wake word listening if enabled on mount
  useEffect(() => {
    if (config.wakeWordEnabled && config.deepgramApiKey && isWakeWordSupported) {
      console.log('[VoiceManager] Auto-starting wake word (enabled in config)');
      startWakeWord();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    mode,
    isEnabled,
    isRecording: mode === 'recording',
    isWakeWordListening,
    isWakeWordSupported,
    interimTranscript,
    finalTranscript,
    audioLevel,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
    startWakeWordListening,
    stopWakeWordListening,
    toggleWakeWord,
  };
}
