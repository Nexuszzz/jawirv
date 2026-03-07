/**
 * JAWIR OS — Chat Panel
 * Chat interface with user/bot message bubbles, input, file attachment, and voice
 */

import { useState, useRef, useEffect, useCallback, type FormEvent, type ChangeEvent } from 'react';
import ReactMarkdown from 'react-markdown';
import { useChatStore, useAgentStore, useSessionStore } from '@/stores';
import { useVoiceManager } from '@/hooks/useVoiceManager';
import VoiceButton from './VoiceButton';
import type { AgentStatus } from '@/types';

const PROCESSING_STATES: AgentStatus[] = ['thinking', 'planning', 'executing_tool', 'searching', 'reading', 'writing', 'observation', 'iteration_start'];

// Allowed file types for upload
const ALLOWED_FILE_TYPES = [
  'image/jpeg', 'image/png', 'image/gif', 'image/webp',
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
  'application/msword', // .doc
  'text/plain', 'text/markdown', 'text/csv',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
  'application/vnd.ms-excel', // .xls
  'application/json',
];

interface UploadedFile {
  file_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  url: string;
  base64_preview?: string;
}

interface ChatPanelProps {
  sendMessage: (data: Record<string, unknown>) => boolean;
}

export default function ChatPanel({ sendMessage }: ChatPanelProps) {
  const { messages, addMessage } = useChatStore();
  const { isConnected, status, statusMessage } = useAgentStore();
  const { getOrCreateSessionId } = useSessionStore();
  
  // File upload state - support multiple files
  const [attachedFiles, setAttachedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Max files limit
  const MAX_FILES = 10;
  
  // Voice input
  const handleVoiceTranscript = useCallback((transcript: string) => {
    // Add user message
    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: transcript,
      timestamp: Date.now(),
    });
    
    // Send via WebSocket
    sendMessage({
      type: 'user_message',
      data: {
        content: transcript,
        session_id: getOrCreateSessionId(),
      },
    });
  }, [addMessage, sendMessage, getOrCreateSessionId]);
  
  const {
    isRecording,
    isWakeWordListening,
    isWakeWordSupported,
    interimTranscript,
    audioLevel,
    startRecording,
    stopRecording,
    toggleWakeWord,
  } = useVoiceManager({ onTranscriptReady: handleVoiceTranscript });
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const isProcessing = PROCESSING_STATES.includes(status);

  // Handle file selection and upload - supports multiple files
  const handleFileSelect = async (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    // Check max files limit
    const remainingSlots = MAX_FILES - attachedFiles.length;
    if (remainingSlots <= 0) {
      alert(`Maksimal ${MAX_FILES} file. Hapus beberapa file terlebih dahulu.`);
      return;
    }
    
    const filesToUpload = Array.from(files).slice(0, remainingSlots);
    const invalidFiles: string[] = [];
    const oversizedFiles: string[] = [];
    const validFiles: File[] = [];
    
    // Validate all files first
    const maxSize = 20 * 1024 * 1024;
    for (const file of filesToUpload) {
      if (!ALLOWED_FILE_TYPES.includes(file.type)) {
        invalidFiles.push(file.name);
      } else if (file.size > maxSize) {
        oversizedFiles.push(file.name);
      } else {
        validFiles.push(file);
      }
    }
    
    // Show warnings for invalid files
    if (invalidFiles.length > 0) {
      alert(`Tipe file tidak didukung:\n${invalidFiles.join('\n')}\n\nTipe yang didukung: gambar, PDF, Word, Excel, text, CSV, JSON`);
    }
    if (oversizedFiles.length > 0) {
      alert(`File terlalu besar (maks 20MB):\n${oversizedFiles.join('\n')}`);
    }
    
    if (validFiles.length === 0) return;
    
    setIsUploading(true);
    const uploadedFiles: UploadedFile[] = [];
    
    try {
      for (let i = 0; i < validFiles.length; i++) {
        const file = validFiles[i];
        setUploadProgress(`Mengupload ${i + 1}/${validFiles.length}: ${file.name}`);
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload/file', {
          method: 'POST',
          body: formData,
        });
        
        if (!response.ok) {
          const error = await response.json();
          throw new Error(`${file.name}: ${error.detail || 'Upload gagal'}`);
        }
        
        const result: UploadedFile = await response.json();
        uploadedFiles.push(result);
      }
      
      // Add all successfully uploaded files
      setAttachedFiles(prev => [...prev, ...uploadedFiles]);
    } catch (error) {
      console.error('Upload error:', error);
      alert(`Gagal upload: ${error instanceof Error ? error.message : 'Unknown error'}`);
      // Still add the files that were successfully uploaded
      if (uploadedFiles.length > 0) {
        setAttachedFiles(prev => [...prev, ...uploadedFiles]);
      }
    } finally {
      setIsUploading(false);
      setUploadProgress('');
      // Reset input so same files can be selected again
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };
  
  // Remove attached file by index
  const removeAttachedFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  };
  
  // Clear all attached files
  const clearAllFiles = () => {
    setAttachedFiles([]);
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, statusMessage]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 150) + 'px';
    }
  }, [input]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || !isConnected || isProcessing) return;

    // Build message content with file info if attached
    let messageContent = text;
    if (attachedFiles.length > 0) {
      const fileList = attachedFiles.map(f => f.filename).join(', ');
      messageContent = `[Files: ${fileList}]\n\n${text}`;
    }

    // Add user message to chat
    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: messageContent,
      timestamp: Date.now(),
    });

    // Send via WebSocket - with or without files
    if (attachedFiles.length > 0) {
      sendMessage({
        type: 'user_message_with_files',
        data: {
          content: text,
          session_id: getOrCreateSessionId(),
          files: attachedFiles.map(f => ({
            file_id: f.file_id,
            filename: f.filename,
            file_type: f.file_type,
          })),
        },
      });
    } else {
      sendMessage({
        type: 'user_message',
        data: {
          content: text,
          session_id: getOrCreateSessionId(),
        },
      });
    }

    setInput('');
    setAttachedFiles([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as FormEvent);
    }
  };

  const formatTime = (ts: number) => {
    return new Date(ts).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {/* Empty state */}
        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center h-full text-center py-20">
            <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
              <span className="material-symbols-outlined text-primary text-3xl icon-filled">spa</span>
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Halo! Saya Jawir 👋</h3>
            <p className="text-sm text-cream-muted max-w-md">
              Desktop AI Agent dengan 30 tools — web search, KiCad, Python, Google Workspace, WhatsApp, Polinema, IoT, dan lainnya.
            </p>
            {/* Quick action chips */}
            <div className="flex flex-wrap gap-2 mt-6 max-w-lg justify-center">
              {[
                { label: 'Cari di internet', icon: 'travel_explore' },
                { label: 'Buat skematik LED', icon: 'memory' },
                { label: 'Jalankan Python', icon: 'code' },
                { label: 'Cek email', icon: 'mail' },
                { label: 'Baca jadwal kuliah', icon: 'school' },
                { label: 'Kirim WhatsApp', icon: 'chat' },
              ].map((chip) => (
                <button
                  key={chip.label}
                  onClick={() => setInput(chip.label)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-coffee-medium border border-coffee-light text-xs text-cream-muted hover:text-white hover:border-primary/40 transition-all"
                >
                  <span className="material-symbols-outlined text-sm">{chip.icon}</span>
                  {chip.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message list */}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
          >
            {/* Bot avatar */}
            {msg.role === 'assistant' && (
              <div className="flex-none w-8 h-8 rounded-full bg-primary flex items-center justify-center mt-1">
                <span className="material-symbols-outlined text-background-dark text-sm icon-filled">smart_toy</span>
              </div>
            )}

            <div className={`max-w-[75%] ${msg.role === 'user' ? 'order-1' : ''}`}>
              <div className={msg.role === 'user' ? 'bubble-user' : 'bubble-bot'}>
                {msg.role === 'user' ? (
                  <div className="text-sm whitespace-pre-wrap">
                    {msg.content}
                  </div>
                ) : (
                  <div className="text-sm prose prose-invert prose-sm max-w-none prose-p:my-1 prose-p:text-cream prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-li:text-cream prose-headings:text-primary prose-strong:text-primary prose-strong:font-semibold prose-em:text-cream-muted prose-code:text-primary prose-code:bg-black/30 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                )}
              </div>
              <div className={`text-[10px] text-cream-muted/60 mt-1 ${msg.role === 'user' ? 'text-right' : ''}`}>
                {formatTime(msg.timestamp)}
              </div>
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isProcessing && (
          <div className="flex gap-3 justify-start animate-fade-in-up">
            <div className="flex-none w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-background-dark text-sm icon-filled animate-pulse">smart_toy</span>
            </div>
            <div className="bubble-bot flex items-center gap-2">
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-background-dark/40 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-background-dark/40 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-background-dark/40 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-xs text-background-dark/60 ml-1">{statusMessage || 'Berpikir...'}</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="flex-none border-t border-coffee-light p-4">
        {/* Multiple files preview */}
        {attachedFiles.length > 0 && (
          <div className="mb-3 space-y-2">
            {/* Header with count and clear all button */}
            <div className="flex items-center justify-between px-1">
              <span className="text-xs text-cream-muted">
                {attachedFiles.length} file terlampir {attachedFiles.length < MAX_FILES && `(maks ${MAX_FILES})`}
              </span>
              {attachedFiles.length > 1 && (
                <button
                  type="button"
                  onClick={clearAllFiles}
                  className="text-xs text-cream-muted hover:text-red-400 transition-colors"
                >
                  Hapus semua
                </button>
              )}
            </div>
            
            {/* File list - scrollable if many files */}
            <div className={`space-y-2 ${attachedFiles.length > 3 ? 'max-h-32 overflow-y-auto pr-2' : ''}`}>
              {attachedFiles.map((file, index) => (
                <div 
                  key={file.file_id} 
                  className="p-2 bg-coffee-medium rounded-lg border border-coffee-light flex items-center gap-2"
                >
                  {/* File icon based on type */}
                  <div className="flex-none w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                    <span className="material-symbols-outlined text-primary text-sm">
                      {file.file_type.startsWith('image/') ? 'image' :
                       file.file_type.includes('pdf') ? 'picture_as_pdf' :
                       file.file_type.includes('word') || file.file_type.includes('document') ? 'description' :
                       file.file_type.includes('sheet') || file.file_type.includes('excel') ? 'table_chart' :
                       'insert_drive_file'}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-white truncate">{file.filename}</p>
                    <p className="text-[10px] text-cream-muted">
                      {(file.file_size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeAttachedFile(index)}
                    className="flex-none p-1 rounded hover:bg-coffee-light text-cream-muted hover:text-red-400 transition-colors"
                    title="Hapus file"
                  >
                    <span className="material-symbols-outlined text-sm">close</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Upload progress indicator */}
        {isUploading && uploadProgress && (
          <div className="mb-2 px-3 py-2 bg-primary/10 rounded-lg border border-primary/30">
            <p className="text-xs text-primary flex items-center gap-2">
              <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>
              {uploadProgress}
            </p>
          </div>
        )}
        
        {/* Hidden file input - supports multiple */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.docx,.doc,.txt,.md,.xlsx,.xls,.csv,.json"
          onChange={handleFileSelect}
          className="hidden"
        />
        
        <form onSubmit={handleSubmit} className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isConnected ? 'Ketik pesan atau perintah...' : 'Menunggu koneksi...'}
              disabled={!isConnected || isProcessing}
              rows={1}
              className="w-full bg-coffee-medium rounded-xl border-none py-3.5 pl-4 pr-12 text-sm text-white placeholder:text-cream-muted/50 focus:ring-2 focus:ring-primary focus:outline-none shadow-inner resize-none disabled:opacity-50"
            />
            {/* Attachment button (inside input) */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading || isProcessing || attachedFiles.length >= MAX_FILES}
              className={`absolute right-3 top-1/2 -translate-y-1/2 p-1 transition-colors ${
                isUploading ? 'text-primary animate-pulse' : 
                attachedFiles.length > 0 ? 'text-primary' : 'text-cream-muted hover:text-primary'
              } disabled:opacity-50`}
              title={
                isUploading ? 'Mengupload...' : 
                attachedFiles.length >= MAX_FILES ? `Maksimal ${MAX_FILES} file` :
                `Lampirkan file (${attachedFiles.length}/${MAX_FILES})`
              }
            >
              <span className="material-symbols-outlined text-xl">
                {isUploading ? 'hourglass_empty' : 'attach_file'}
              </span>
              {/* Badge showing file count */}
              {attachedFiles.length > 0 && !isUploading && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-primary text-background-dark text-[10px] font-bold rounded-full flex items-center justify-center">
                  {attachedFiles.length}
                </span>
              )}
            </button>
          </div>

          {/* Voice button */}
          <VoiceButton
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            disabled={!isConnected || isProcessing}
            isRecording={isRecording}
            audioLevel={audioLevel}
          />
          
          {/* Wake Word Toggle Button */}
          {isWakeWordSupported && (
            <button
              type="button"
              onClick={toggleWakeWord}
              disabled={!isConnected}
              className={`flex-none w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300 relative ${
                isWakeWordListening 
                  ? 'bg-green-600/20 border-2 border-green-500 text-green-400' 
                  : 'bg-coffee-medium border border-coffee-light text-cream-muted hover:text-white hover:border-primary/40'
              } disabled:opacity-40`}
              title={isWakeWordListening ? 'Wake Word aktif - Ucapkan "Jawir" untuk memulai' : 'Aktifkan Wake Word "Jawir"'}
            >
              <span className="material-symbols-outlined text-xl">
                {isWakeWordListening ? 'hearing' : 'hearing_disabled'}
              </span>
              {/* Pulse indicator when listening */}
              {isWakeWordListening && (
                <span className="absolute inset-0 rounded-xl border-2 border-green-500/50 animate-ping" />
              )}
            </button>
          )}

          {/* Send button */}
          <button
            type="submit"
            disabled={!input.trim() || !isConnected || isProcessing || isRecording}
            className="flex-none w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-[#bfa10a] shadow-lg shadow-primary/20 flex items-center justify-center text-background-dark hover:scale-105 active:scale-95 transition-transform disabled:opacity-40 disabled:hover:scale-100"
          >
            <span className="material-symbols-outlined text-xl icon-filled">send</span>
          </button>
        </form>
        
        {/* Voice interim transcript preview */}
        {isRecording && interimTranscript && (
          <div className="mt-2 px-4 py-2 bg-coffee-medium rounded-lg border border-coffee-light">
            <p className="text-xs text-cream-muted flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              <span className="italic">{interimTranscript}</span>
            </p>
          </div>
        )}
        
        {/* Wake word listening indicator */}
        {isWakeWordListening && !isRecording && (
          <div className="mt-2 px-4 py-2 bg-green-900/20 rounded-lg border border-green-700/30">
            <p className="text-xs text-green-400 flex items-center gap-2">
              <span className="material-symbols-outlined text-sm animate-pulse">hearing</span>
              <span>Mendengarkan... Ucapkan <strong>"Jawir"</strong> untuk memulai</span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
