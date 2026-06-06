import { useRef, useState, useEffect } from 'react';
import { Send, Paperclip, X, FileText, Image, Mic, File } from 'lucide-react';

interface Props {
  onSend: (message: string) => void;
  isLoading: boolean;
  files?: File[];
  onAttachFiles?: (files: File[]) => void;
  onRemoveFile?: (idx: number) => void;
  onClearFiles?: () => void;
}

const getFileIcon = (fileName: string) => {
  const name = fileName?.toLowerCase() || '';
  if (name.endsWith('.pdf')) {
    return <FileText size={12} className="text-red-400" />;
  }
  if (name.match(/\.(png|jpg|jpeg|webp)$/)) {
    return <Image size={12} className="text-purple-400" />;
  }
  if (name.match(/\.(mp3|wav|m4a|ogg|flac)$/)) {
    return <Mic size={12} className="text-amber-400" />;
  }
  return <File size={12} className="text-blue-400" />;
};

export function InputBox({
  onSend,
  isLoading,
  files = [],
  onAttachFiles,
  onRemoveFile,
  onClearFiles,
}: Props) {
  const [value, setValue] = useState('');
  const [dragging, setDragging] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 180)}px`;
  }, [value]);

  const handleSend = () => {
    const hasFiles = Array.isArray(files) && files.length > 0;
    if (!value?.trim() && !hasFiles) return;
    if (isLoading) return;
    if (typeof onSend === 'function') {
      onSend(value.trim());
    }
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && typeof onAttachFiles === 'function') {
      onAttachFiles(Array.from(e.target.files));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files && typeof onAttachFiles === 'function') {
      onAttachFiles(Array.from(e.dataTransfer.files));
    }
  };

  const safeFiles = Array.isArray(files) ? files : [];

  return (
    <div
      className="rounded-2xl p-3 transition-all duration-200"
      style={{
        background: 'var(--color-bg-elevated)',
        border: `1.5px ${dragging ? 'dashed #818cf8' : 'solid var(--color-border)'}`,
        boxShadow: dragging ? '0 0 25px rgba(129, 140, 248, 0.25)' : '0 0 30px rgba(0,0,0,0.3)',
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={handleFileInputChange}
        accept=".pdf,.png,.jpg,.jpeg,.mp3,.wav,.m4a,.ogg,.flac"
      />

      { }
      {safeFiles.length > 0 && (
        <div className="pb-2.5 mb-2.5" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
          <div className="flex items-center justify-between mb-1.5 px-1">
            <span className="text-[10px] font-bold tracking-wider uppercase" style={{ color: 'var(--color-text-muted)' }}>
              Attached Files
            </span>
            <button
              onClick={onClearFiles}
              className="text-[10px] hover:underline"
              style={{ color: '#f87171' }}
            >
              Clear All
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto pr-1">
            {safeFiles.map((file, idx) => {
              if (!file) return null;
              return (
                <div
                  key={`${file?.name || 'file'}-${idx}`}
                  className="flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs animate-fade-in"
                  style={{
                    background: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border)',
                    color: 'var(--color-text-secondary)',
                    maxWidth: '220px',
                  }}
                >
                  <span className="shrink-0">{getFileIcon(file?.name)}</span>
                  <span className="truncate flex-1 font-medium">{file?.name || 'file'}</span>
                  <button
                    onClick={() => typeof onRemoveFile === 'function' && onRemoveFile(idx)}
                    className="shrink-0 opacity-60 hover:opacity-100 hover:text-red-400"
                  >
                    <X size={10} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      { }
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={
          safeFiles.length > 0
            ? "Ask anything about these files… (Enter to analyze)"
            : "Ask your agent or drop files here… (Enter to send)"
        }
        disabled={isLoading}
        rows={1}
        className="w-full resize-none outline-none text-sm leading-relaxed bg-transparent"
        style={{
          color: 'var(--color-text-primary)',
          caretColor: 'var(--color-brand-400)',
          minHeight: '40px',
          maxHeight: '180px',
        }}
      />

      { }
      <div
        className="flex items-center justify-between mt-2 pt-2"
        style={{ borderTop: '1px solid var(--color-border-subtle)' }}
      >
        <div className="flex items-center gap-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="btn-ghost"
            style={{ padding: '6px 10px' }}
            title="Attach files (PDF, PNG, JPG, WAV, MP3, etc.)"
          >
            <Paperclip size={14} />
            <span>Attach Files</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            {(value?.length || 0) > 0 && `${value.length} chars`}
          </span>
          <button
            onClick={handleSend}
            disabled={(!value?.trim() && safeFiles.length === 0) || isLoading}
            className="btn-primary"
            style={{
              padding: '8px 16px',
              background: (!value?.trim() && safeFiles.length === 0) || isLoading
                ? undefined
                : 'linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))',
            }}
            id="send-button"
          >
            {isLoading ? (
              <div
                className="w-4 h-4 rounded-full border-2 border-transparent animate-spin-slow"
                style={{ borderTopColor: 'white' }}
              />
            ) : (
              <Send size={14} />
            )}
            <span>{isLoading ? 'Processing…' : 'Send'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
