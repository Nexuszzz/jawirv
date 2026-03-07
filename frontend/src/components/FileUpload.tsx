/**
 * JAWIR OS — File Upload Modal
 * Upload files to POST /api/upload
 * Supports: JPEG, PNG, GIF, WebP, PDF — max 10MB
 */

import { useState, useRef, useCallback, type DragEvent } from 'react';
import { useUIStore, useSessionStore, useChatStore } from '@/stores';

const ACCEPT_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'];
const MAX_SIZE = 10 * 1024 * 1024; // 10MB
const API_BASE = 'http://localhost:8000';

interface UploadState {
  status: 'idle' | 'uploading' | 'success' | 'error';
  progress: number;
  filename: string;
  error?: string;
}

export default function FileUpload() {
  const { showUploadModal, setShowUploadModal } = useUIStore();
  const { getOrCreateSessionId } = useSessionStore();
  const { addMessage } = useChatStore();
  const [upload, setUpload] = useState<UploadState>({ status: 'idle', progress: 0, filename: '' });
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClose = () => {
    setShowUploadModal(false);
    setUpload({ status: 'idle', progress: 0, filename: '' });
  };

  const uploadFile = useCallback(async (file: File) => {
    // Validate type
    if (!ACCEPT_TYPES.includes(file.type)) {
      setUpload({ status: 'error', progress: 0, filename: file.name, error: 'Tipe file tidak didukung. Gunakan JPEG, PNG, GIF, WebP, atau PDF.' });
      return;
    }
    // Validate size
    if (file.size > MAX_SIZE) {
      setUpload({ status: 'error', progress: 0, filename: file.name, error: 'Ukuran file melebihi 10MB.' });
      return;
    }

    setUpload({ status: 'uploading', progress: 10, filename: file.name });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', getOrCreateSessionId());

      const res = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Upload gagal' }));
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }

      setUpload({ status: 'success', progress: 100, filename: file.name });

      // Add system message to chat
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `📎 File "${file.name}" berhasil di-upload. Anda bisa merujuk file ini dalam percakapan.`,
        timestamp: Date.now(),
      });

      // Auto close after 1.5s
      setTimeout(handleClose, 1500);
    } catch (err) {
      setUpload({
        status: 'error',
        progress: 0,
        filename: file.name,
        error: err instanceof Error ? err.message : 'Upload gagal',
      });
    }
  }, [getOrCreateSessionId, addMessage]);

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  }, [uploadFile]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
  };

  if (!showUploadModal) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-coffee-dark rounded-2xl border border-coffee-light w-full max-w-md mx-4 shadow-2xl animate-slide-in-right">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-coffee-light">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span className="material-symbols-outlined text-primary icon-filled">upload_file</span>
            Upload File
          </h3>
          <button onClick={handleClose} className="p-1 rounded-lg hover:bg-coffee-medium transition-colors">
            <span className="material-symbols-outlined text-cream-muted">close</span>
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          {/* Drop zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`
              border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
              ${dragOver
                ? 'border-primary bg-primary/10 scale-[1.02]'
                : 'border-coffee-light hover:border-cream-muted/30 hover:bg-coffee-medium/30'
              }
            `}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPT_TYPES.join(',')}
              onChange={handleFileSelect}
              className="hidden"
            />

            {upload.status === 'idle' && (
              <>
                <span className="material-symbols-outlined text-4xl text-cream-muted/40 mb-2">cloud_upload</span>
                <p className="text-sm text-cream-muted mb-1">
                  Drag & drop file di sini, atau <span className="text-primary font-semibold">klik untuk pilih</span>
                </p>
                <p className="text-[10px] text-cream-muted/40">
                  JPEG, PNG, GIF, WebP, PDF • Maks 10MB
                </p>
              </>
            )}

            {upload.status === 'uploading' && (
              <div className="space-y-3">
                <span className="material-symbols-outlined text-4xl text-primary animate-pulse">cloud_sync</span>
                <p className="text-sm text-white">{upload.filename}</p>
                <div className="w-full h-2 rounded-full bg-background-dark overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-[#bfa10a] rounded-full transition-all animate-shimmer"
                    style={{ width: `${upload.progress}%` }}
                  />
                </div>
                <p className="text-xs text-cream-muted/60">Mengupload...</p>
              </div>
            )}

            {upload.status === 'success' && (
              <div className="space-y-2">
                <span className="material-symbols-outlined text-4xl text-green-400 icon-filled">check_circle</span>
                <p className="text-sm text-green-400 font-semibold">Upload berhasil!</p>
                <p className="text-xs text-cream-muted">{upload.filename}</p>
              </div>
            )}

            {upload.status === 'error' && (
              <div className="space-y-2">
                <span className="material-symbols-outlined text-4xl text-red-400 icon-filled">error</span>
                <p className="text-sm text-red-400 font-semibold">Upload gagal</p>
                <p className="text-xs text-cream-muted/60">{upload.error}</p>
                <button
                  onClick={(e) => { e.stopPropagation(); setUpload({ status: 'idle', progress: 0, filename: '' }); }}
                  className="text-xs text-primary hover:underline mt-1"
                >
                  Coba lagi
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
