/**
 * JAWIR OS — Fire Alert Popup
 * Shows emergency popup when fire/flame is detected by IoT sensor
 */

import { useEffect, useRef } from 'react';

interface FireAlertProps {
  isVisible: boolean;
  deviceName: string;
  room: string;
  onDismiss: () => void;
}

export default function FireAlert({ isVisible, deviceName, room, onDismiss }: FireAlertProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Play alarm sound when visible
  useEffect(() => {
    if (isVisible) {
      // Create audio element for alarm
      const audio = new Audio();
      audio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1tZXR8gHx8dXl/c2luZnFpYWptZW9tb2hvam5rbG1sa2xpa2ltb3Byd3h5enl4d3V3eHp8fX9/f319fHt7enl4d3Z2dnZ3eHl7fH1+fn5+fn19fHx7enl4d3d3d3d4eXp7fH1+fn5+fn19fHx7enl4d3d3d3d4eXp7fH1+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn5+fn4=';
      audio.loop = true;
      audio.volume = 0.7;
      audio.play().catch(() => {}); // Ignore autoplay restrictions
      audioRef.current = audio;

      // Auto-dismiss after 30 seconds
      const timer = setTimeout(() => {
        onDismiss();
      }, 30000);

      return () => {
        clearTimeout(timer);
        if (audioRef.current) {
          audioRef.current.pause();
          audioRef.current = null;
        }
      };
    }
  }, [isVisible, onDismiss]);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 animate-pulse">
      {/* Alert Container */}
      <div className="relative bg-gradient-to-b from-red-900 to-red-950 border-4 border-red-500 rounded-2xl p-8 max-w-md mx-4 shadow-2xl animate-bounce">
        {/* Fire Icon */}
        <div className="flex justify-center mb-4">
          <div className="text-7xl animate-pulse">🔥</div>
        </div>

        {/* Alert Title */}
        <h1 className="text-4xl font-bold text-red-500 text-center mb-2 animate-pulse">
          AWAS GENI!
        </h1>

        {/* Subtitle */}
        <p className="text-2xl text-white text-center mb-4">
          🚨 API TERDETEKSI! 🚨
        </p>

        {/* Device Info */}
        <div className="bg-red-950/50 rounded-lg p-4 mb-6">
          <p className="text-lg text-red-200 text-center">
            <span className="font-bold">Device:</span> {deviceName}
          </p>
          <p className="text-lg text-red-200 text-center">
            <span className="font-bold">Lokasi:</span> {room}
          </p>
        </div>

        {/* Warning Text */}
        <p className="text-yellow-400 text-center text-sm mb-6">
          ⚠️ Segera evakuasi area dan hubungi pemadam kebakaran!
        </p>

        {/* Dismiss Button */}
        <button
          onClick={() => {
            if (audioRef.current) {
              audioRef.current.pause();
              audioRef.current = null;
            }
            onDismiss();
          }}
          className="w-full py-3 bg-yellow-500 hover:bg-yellow-600 text-black font-bold rounded-lg transition-colors text-lg"
        >
          ✓ Mengerti - Tutup Alert
        </button>
      </div>

      {/* Flashing border effect */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 border-8 border-red-500 animate-ping opacity-30" />
      </div>
    </div>
  );
}
