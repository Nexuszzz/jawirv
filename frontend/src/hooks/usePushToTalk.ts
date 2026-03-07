/**
 * JAWIR OS — Push-to-Talk Hook
 * Manages microphone capture with hold-to-record functionality
 */

import { useCallback, useRef, useState, useEffect } from 'react';
import { useVoiceStore } from '@/stores';

interface UsePushToTalkOptions {
  onStart?: () => void;
  onStop?: () => void;
  onAudioLevel?: (level: number) => void;
}

interface UsePushToTalkReturn {
  isRecording: boolean;
  isPressing: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  audioLevel: number;
}

export function usePushToTalk(options: UsePushToTalkOptions = {}): UsePushToTalkReturn {
  const { onStart, onStop, onAudioLevel } = options;
  
  const { setAudioLevel } = useVoiceStore();
  
  const [isRecording, setIsRecording] = useState(false);
  const [isPressing, setIsPressing] = useState(false);
  const [audioLevel, setLocalAudioLevel] = useState(0);
  
  const streamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  // Audio level analysis
  const updateAudioLevel = useCallback(() => {
    if (!analyserRef.current) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    // Calculate average volume
    const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
    const normalized = Math.min(1, average / 128); // Normalize to 0-1
    
    setLocalAudioLevel(normalized);
    setAudioLevel(normalized);
    onAudioLevel?.(normalized);
    
    animationRef.current = requestAnimationFrame(updateAudioLevel);
  }, [setAudioLevel, onAudioLevel]);

  // Start recording
  const startRecording = useCallback(async () => {
    if (isRecording) return;
    
    try {
      setIsPressing(true);
      
      // Request microphone
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      
      streamRef.current = stream;
      
      // Set up audio analysis
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;
      
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.3;
      
      source.connect(analyser);
      analyserRef.current = analyser;
      
      setIsRecording(true);
      onStart?.();
      
      // Start audio level monitoring
      updateAudioLevel();
      
    } catch (err) {
      console.error('[PTT] Error starting recording:', err);
      setIsPressing(false);
      setIsRecording(false);
    }
  }, [isRecording, onStart, updateAudioLevel]);

  // Stop recording
  const stopRecording = useCallback(() => {
    setIsPressing(false);
    
    // Stop animation
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    
    // Stop audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    // Stop stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    analyserRef.current = null;
    setIsRecording(false);
    setLocalAudioLevel(0);
    setAudioLevel(0);
    
    onStop?.();
  }, [setAudioLevel, onStop]);

  // Keyboard shortcut (Space key by default)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      
      if (e.code === 'Space' && !e.repeat && !isPressing) {
        e.preventDefault();
        startRecording();
      }
    };
    
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space' && isPressing) {
        e.preventDefault();
        stopRecording();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isPressing, startRecording, stopRecording]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return {
    isRecording,
    isPressing,
    startRecording,
    stopRecording,
    audioLevel,
  };
}
