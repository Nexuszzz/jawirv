/**
 * JAWIR OS — Deepgram Speech-to-Text Hook
 * Real-time transcription via WebSocket streaming to Deepgram Nova-2
 * 
 * FLOW:
 * 1. startListening() → get mic → connect Deepgram WS → stream PCM16
 * 2. Deepgram sends interim + final transcripts via onmessage
 * 3. stopListening() → send CloseStream → wait for final → close
 */

import { useCallback, useRef } from 'react';
import { useVoiceStore } from '@/stores';

interface UseDeepgramOptions {
  onFinalResult?: (fullText: string) => void;
  onError?: (error: string) => void;
}

export function useDeepgram(options: UseDeepgramOptions = {}) {
  const { config, setInterimTranscript, setFinalTranscript, setError, setMode, setAudioLevel } = useVoiceStore();
  
  // Refs for all resources
  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number>(0);
  const accumulatedRef = useRef('');
  const isStoppingRef = useRef(false);
  const hasFiredRef = useRef(false);
  const safetyTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Keep callbacks fresh
  const onFinalResultRef = useRef(options.onFinalResult);
  const onErrorRef = useRef(options.onError);
  onFinalResultRef.current = options.onFinalResult;
  onErrorRef.current = options.onError;

  // Fire the final result callback (only once per session)
  const fireResult = useCallback((text: string) => {
    if (hasFiredRef.current) return;
    hasFiredRef.current = true;
    console.log('[Voice] → Submit:', text || '(empty)');
    // Always call callback — even on empty text — so wake word can resume
    onFinalResultRef.current?.(text.trim());
  }, []);

  // Stop mic + audio nodes (but keep WS alive for final transcript)
  const stopMic = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = 0;
    }
    try { processorRef.current?.disconnect(); } catch { /* ok */ }
    try { sourceRef.current?.disconnect(); } catch { /* ok */ }
    try { analyserRef.current?.disconnect(); } catch { /* ok */ }
    processorRef.current = null;
    sourceRef.current = null;
    analyserRef.current = null;
    
    if (audioCtxRef.current?.state !== 'closed') {
      audioCtxRef.current?.close().catch(() => {});
    }
    audioCtxRef.current = null;
    
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    setAudioLevel(0);
  }, [setAudioLevel]);

  // Full cleanup
  const fullCleanup = useCallback(() => {
    stopMic();
    if (safetyTimeoutRef.current) {
      clearTimeout(safetyTimeoutRef.current);
      safetyTimeoutRef.current = null;
    }
    if (wsRef.current) {
      try { wsRef.current.close(1000); } catch { /* ok */ }
      wsRef.current = null;
    }
    isStoppingRef.current = false;
    accumulatedRef.current = '';
    hasFiredRef.current = false;
  }, [stopMic]);

  // Audio level animation
  const animateLevel = useCallback(() => {
    if (!analyserRef.current) return;
    const buf = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(buf);
    const avg = buf.reduce((a, b) => a + b, 0) / buf.length;
    setAudioLevel(Math.min(1, avg / 100));
    animFrameRef.current = requestAnimationFrame(animateLevel);
  }, [setAudioLevel]);

  // ====== START ======
  const startListening = useCallback(async () => {
    const apiKey = config.deepgramApiKey;
    if (!apiKey) {
      const msg = 'Deepgram API key belum ada. Buka Settings.';
      setError(msg);
      onErrorRef.current?.(msg);
      return;
    }

    fullCleanup();
    hasFiredRef.current = false;
    accumulatedRef.current = '';
    isStoppingRef.current = false;

    try {
      // 1. Get mic
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      streamRef.current = stream;
      console.log('[Voice] Mic OK');

      // 2. Create AudioContext first to know the actual sample rate
      //    Browser may ignore our 16kHz hint and give 48kHz instead
      const ctx = new AudioContext({ sampleRate: 16000 });
      audioCtxRef.current = ctx;
      const actualRate = ctx.sampleRate;
      console.log('[Voice] AudioContext sampleRate:', actualRate);

      // 3. Connect Deepgram with actual sample rate
      const lang = config.language === 'multi' ? 'multi' : config.language;
      const params = new URLSearchParams({
        model: 'nova-2', language: lang, smart_format: 'true',
        interim_results: 'true', endpointing: '400',
        utterance_end_ms: '1500', encoding: 'linear16',
        sample_rate: String(actualRate), channels: '1',
      });

      const ws = new WebSocket(`wss://api.deepgram.com/v1/listen?${params}`, ['token', apiKey]);
      wsRef.current = ws;

      await new Promise<void>((resolve, reject) => {
        const t = setTimeout(() => reject(new Error('Deepgram timeout')), 8000);
        ws.onopen = () => { clearTimeout(t); console.log('[Voice] Deepgram WS connected'); resolve(); };
        ws.onerror = (ev) => { clearTimeout(t); console.error('[Voice] WS error:', ev); reject(new Error('Deepgram koneksi gagal. Cek API key.')); };
      });

      setMode('recording');

      // 4. Handle transcripts
      ws.onmessage = (event) => {
        try {
          const d = JSON.parse(event.data);
          
          // Log first message to see Deepgram response structure
          if (!accumulatedRef.current && d.type) {
            console.log('[Voice] DG msg type:', d.type);
          }
          
          const alt = d.channel?.alternatives?.[0];
          if (!alt) return;
          const text = alt.transcript || '';
          
          if (d.is_final && text) {
            accumulatedRef.current += (accumulatedRef.current ? ' ' : '') + text;
            setFinalTranscript(accumulatedRef.current);
            setInterimTranscript('');
            console.log('[Voice] Final chunk:', text, '| Total:', accumulatedRef.current);
          } else if (text) {
            setInterimTranscript(text);
          }
        } catch (e) { console.warn('[Voice] Parse error:', e); }
      };

      ws.onclose = (ev) => {
        console.log('[Voice] WS closed, code:', ev.code, 'reason:', ev.reason);
        // Cancel safety timeout — we're handling cleanup here
        if (safetyTimeoutRef.current) {
          clearTimeout(safetyTimeoutRef.current);
          safetyTimeoutRef.current = null;
        }
        if (isStoppingRef.current) {
          fireResult(accumulatedRef.current);
        }
        fullCleanup();
        setInterimTranscript('');
        setFinalTranscript('');
        setMode('idle');
      };

      ws.onerror = (ev) => {
        console.error('[Voice] WS runtime error:', ev);
      };

      // 5. Audio pipeline: mic → analyser + scriptProcessor → Deepgram WS
      const src = ctx.createMediaStreamSource(stream);
      sourceRef.current = src;
      
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.3;
      analyserRef.current = analyser;
      src.connect(analyser);
      
      const proc = ctx.createScriptProcessor(4096, 1, 1);
      processorRef.current = proc;
      proc.onaudioprocess = (e) => {
        if (ws.readyState !== WebSocket.OPEN) return;
        const inp = e.inputBuffer.getChannelData(0);
        const pcm = new Int16Array(inp.length);
        for (let i = 0; i < inp.length; i++) {
          const s = Math.max(-1, Math.min(1, inp[i]));
          pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        ws.send(pcm.buffer);
      };
      src.connect(proc);
      proc.connect(ctx.destination);
      
      animateLevel();
      console.log('[Voice] Streaming audio to Deepgram...');

    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Voice error';
      console.error('[Voice] Error:', msg);
      setError(msg);
      onErrorRef.current?.(msg);
      fullCleanup();
      setMode('idle');
    }
  }, [config, fullCleanup, setMode, setInterimTranscript, setFinalTranscript, setError, setAudioLevel, animateLevel, fireResult]);

  // ====== STOP ======
  const stopListening = useCallback(() => {
    console.log('[Voice] Stop requested. Accumulated:', accumulatedRef.current);
    isStoppingRef.current = true;
    
    // Stop mic immediately (stops sending audio)
    stopMic();
    setMode('processing');

    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      // Tell Deepgram to flush remaining audio and send final
      try { ws.send(JSON.stringify({ type: 'CloseStream' })); } catch { /* ok */ }
      console.log('[Voice] Sent CloseStream, waiting for final...');
      
      // Safety timeout: if Deepgram doesn't close in 2s, force close
      // (cancelled by onclose handler if WS closes normally)
      safetyTimeoutRef.current = setTimeout(() => {
        safetyTimeoutRef.current = null;
        fireResult(accumulatedRef.current);
        fullCleanup();
        setInterimTranscript('');
        setFinalTranscript('');
        setMode('idle');
      }, 2000);
    } else {
      // WS not open, fire immediately
      fireResult(accumulatedRef.current);
      fullCleanup();
      setInterimTranscript('');
      setFinalTranscript('');
      setMode('idle');
    }
  }, [stopMic, fullCleanup, setMode, setInterimTranscript, setFinalTranscript, fireResult]);

  return { startListening, stopListening, cancelListening: fullCleanup };
}
