/**
 * JAWIR OS — Wake Word Detection Hook
 * Listens continuously for "Jawir" wake word using Web Speech API
 * 
 * FLOW:
 * 1. Start listening (always-on background mode)
 * 2. Web Speech API transcribes in real-time
 * 3. Check each transcript for "jawir" keyword
 * 4. On detection → trigger callback → pause listening
 * 5. After command processed → resume listening
 * 
 * NOTE: Web Speech API is free but only works in Chrome/Edge
 */

import { useCallback, useRef, useEffect } from 'react';
import { useVoiceStore } from '@/stores';

// Web Speech API types (not fully typed in TypeScript)
interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onend: (() => void) | null;
  onerror: ((event: Event & { error: string }) => void) | null;
  onstart: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

interface SpeechRecognitionConstructor {
  new (): SpeechRecognition;
}

// Get the SpeechRecognition constructor (browser-specific)
const getSpeechRecognition = (): SpeechRecognitionConstructor | null => {
  if (typeof window === 'undefined') return null;
  
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const w = window as any;
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
};

interface UseWakeWordOptions {
  onWakeWord?: () => void;
  onError?: (error: string) => void;
  keywords?: string[]; // Default: ['jawir']
}

interface UseWakeWordReturn {
  isListening: boolean;
  isSupported: boolean;
  lastHeard: string;
  startListening: () => void;
  stopListening: () => void;
  pauseListening: () => void;
  resumeListening: () => void;
}

export function useWakeWord(options: UseWakeWordOptions = {}): UseWakeWordReturn {
  const { onWakeWord, onError, keywords = ['jawir', 'jawer', 'javier', 'jauir'] } = options;
  
  const { config, setMode, mode } = useVoiceStore();
  
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const isListeningRef = useRef(false);
  const isPausedRef = useRef(false);
  const lastHeardRef = useRef('');
  const restartTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Callback refs
  const onWakeWordRef = useRef(onWakeWord);
  const onErrorRef = useRef(onError);
  onWakeWordRef.current = onWakeWord;
  onErrorRef.current = onError;

  const SpeechRecognitionClass = getSpeechRecognition();
  const isSupported = SpeechRecognitionClass !== null;

  // Check if transcript contains wake word
  const containsWakeWord = useCallback((text: string): boolean => {
    const lower = text.toLowerCase().trim();
    return keywords.some(kw => lower.includes(kw.toLowerCase()));
  }, [keywords]);

  // Initialize recognition
  const initRecognition = useCallback(() => {
    if (!SpeechRecognitionClass) return null;
    
    const recognition = new SpeechRecognitionClass();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = config.language === 'en' ? 'en-US' : 'id-ID';
    recognition.maxAlternatives = 3;
    
    recognition.onstart = () => {
      console.log('[WakeWord] Started listening...');
      isListeningRef.current = true;
    };
    
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      // Check all results from this recognition session
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0].transcript;
        
        lastHeardRef.current = transcript;
        console.log('[WakeWord] Heard:', transcript, '| Final:', result.isFinal);
        
        // Check for wake word in any alternative
        for (let j = 0; j < result.length; j++) {
          const alt = result[j];
          if (containsWakeWord(alt.transcript)) {
            console.log('[WakeWord] 🎤 WAKE WORD DETECTED!', alt.transcript);
            
            // Stop listening before triggering (to release mic for Deepgram)
            recognition.stop();
            isListeningRef.current = false;
            isPausedRef.current = true;
            
            // Play activation sound
            playActivationSound();
            
            // Trigger callback
            onWakeWordRef.current?.();
            return;
          }
        }
      }
    };
    
    recognition.onerror = (event) => {
      console.warn('[WakeWord] Error:', event.error);
      
      // Ignore no-speech errors (normal when user is silent)
      if (event.error === 'no-speech') {
        return;
      }
      
      // Ignore aborted (we stopped it intentionally)
      if (event.error === 'aborted') {
        return;
      }
      
      // Handle network errors
      if (event.error === 'network') {
        onErrorRef.current?.('Network error during wake word detection');
      }
      
      // Handle not-allowed (permission denied)
      if (event.error === 'not-allowed') {
        onErrorRef.current?.('Microphone permission denied');
        isListeningRef.current = false;
        return;
      }
    };
    
    recognition.onend = () => {
      console.log('[WakeWord] Recognition ended. isPaused:', isPausedRef.current);
      isListeningRef.current = false;
      
      // Don't auto-restart if this recognition was replaced by a newer instance
      if (recognitionRef.current !== recognition) {
        console.log('[WakeWord] This recognition was replaced, skipping auto-restart');
        return;
      }
      
      // Auto-restart if not intentionally paused
      if (!isPausedRef.current && config.wakeWordEnabled) {
        // Small delay before restart to avoid rapid restarts
        restartTimeoutRef.current = setTimeout(() => {
          if (!isPausedRef.current && config.wakeWordEnabled) {
            console.log('[WakeWord] Auto-restarting...');
            try {
              recognition.start();
            } catch (e) {
              console.warn('[WakeWord] Restart failed:', e);
            }
          }
        }, 500);
      }
    };
    
    return recognition;
  }, [SpeechRecognitionClass, config.language, config.wakeWordEnabled, containsWakeWord]);

  // Play activation sound
  const playActivationSound = useCallback(() => {
    try {
      // Create a beep sound using Web Audio API
      const audioCtx = new AudioContext();
      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);
      
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note
      gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
      
      oscillator.start(audioCtx.currentTime);
      oscillator.stop(audioCtx.currentTime + 0.3);
    } catch (e) {
      console.warn('[WakeWord] Could not play activation sound:', e);
    }
  }, []);

  // Start listening for wake word
  const startListening = useCallback(() => {
    if (!isSupported) {
      onErrorRef.current?.('Wake word detection not supported in this browser');
      return;
    }
    
    if (isListeningRef.current) {
      console.log('[WakeWord] Already listening');
      return;
    }
    
    isPausedRef.current = false;
    
    // Clear any pending restart timeout from a previous recognition's onend
    if (restartTimeoutRef.current) {
      clearTimeout(restartTimeoutRef.current);
      restartTimeoutRef.current = null;
    }
    
    // Clean up existing
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch { /* ok */ }
    }
    
    // Create new instance
    const recognition = initRecognition();
    if (!recognition) return;
    
    recognitionRef.current = recognition;
    
    try {
      recognition.start();
      setMode('wake_listening');
    } catch (e) {
      console.error('[WakeWord] Failed to start:', e);
      onErrorRef.current?.('Failed to start wake word detection');
    }
  }, [isSupported, initRecognition, setMode]);

  // Stop listening completely
  const stopListening = useCallback(() => {
    isPausedRef.current = true;
    
    if (restartTimeoutRef.current) {
      clearTimeout(restartTimeoutRef.current);
      restartTimeoutRef.current = null;
    }
    
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch { /* ok */ }
    }
    
    isListeningRef.current = false;
    
    if (mode === 'wake_listening') {
      setMode('idle');
    }
  }, [mode, setMode]);

  // Pause temporarily (e.g., while Deepgram is recording)
  const pauseListening = useCallback(() => {
    console.log('[WakeWord] Pausing...');
    isPausedRef.current = true;
    
    if (restartTimeoutRef.current) {
      clearTimeout(restartTimeoutRef.current);
      restartTimeoutRef.current = null;
    }
    
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch { /* ok */ }
    }
    
    isListeningRef.current = false;
  }, []);

  // Resume after pause
  const resumeListening = useCallback(() => {
    console.log('[WakeWord] Resuming...');
    isPausedRef.current = false;
    startListening();
  }, [startListening]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (restartTimeoutRef.current) {
        clearTimeout(restartTimeoutRef.current);
      }
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch { /* ok */ }
      }
    };
  }, []);

  return {
    isListening: isListeningRef.current,
    isSupported,
    lastHeard: lastHeardRef.current,
    startListening,
    stopListening,
    pauseListening,
    resumeListening,
  };
}
