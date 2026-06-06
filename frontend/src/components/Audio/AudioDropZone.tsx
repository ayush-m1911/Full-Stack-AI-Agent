import { useRef, useState } from 'react';
import { Mic, AlertCircle, Loader } from 'lucide-react';

interface Props {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  stage: 'idle' | 'uploading' | 'transcribing' | 'summarizing';
  hasResult: boolean;
}

const ACCEPTED = '.mp3,.wav,.m4a,.ogg,.flac,audio/mpeg,audio/wav,audio/mp4,audio/ogg,audio/flac';

const STAGE_LABELS: Record<string, string> = {
  uploading: 'Uploading audio…',
  transcribing: 'Whisper transcribing…',
  summarizing: 'Generating summaries…',
};

export function AudioDropZone({ onUpload, isUploading, uploadProgress, uploadError, stage, hasResult }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = (file: File | undefined) => {
    if (!file) return;
    const ok = file.type.startsWith('audio/') || file.name.match(/\.(mp3|wav|m4a|ogg|flac)$/i);
    if (!ok) return;
    onUpload(file);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  if (hasResult) return null;

  return (
    <div
      className="relative rounded-2xl cursor-pointer transition-all duration-200"
      style={{
        border: `2px dashed ${isDragging ? '#f59e0b' : 'var(--color-border)'}`,
        background: isDragging ? 'rgba(245,158,11,0.06)' : 'var(--color-bg-elevated)',
        padding: '20px 16px',
      }}
      onClick={() => !isUploading && inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={onDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        className="sr-only"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />

      <div className="flex flex-col items-center gap-2 text-center">
        {isUploading ? (
          <>
            <Loader size={22} className="animate-spin" style={{ color: '#fbbf24' }} />
            <p className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>
              {STAGE_LABELS[stage] ?? 'Processing…'}
            </p>
            <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--color-border)' }}>
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${uploadProgress}%`,
                  background: 'linear-gradient(90deg, #f59e0b, #ef4444)',
                }}
              />
            </div>
            <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
              First run downloads Whisper weights (~140 MB)
            </p>
          </>
        ) : (
          <>
            <div
              className="flex items-center justify-center w-10 h-10 rounded-xl"
              style={{
                background: 'linear-gradient(135deg, rgba(245,158,11,0.15), rgba(245,158,11,0.05))',
                border: '1px solid rgba(245,158,11,0.2)',
              }}
            >
              <Mic size={18} style={{ color: '#fbbf24' }} />
            </div>
            <p className="text-xs font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              Drop an audio file here
            </p>
            <p className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>
              MP3 · WAV · M4A · OGG · FLAC — up to 100 MB
            </p>
          </>
        )}
      </div>

      {uploadError && (
        <div
          className="mt-3 flex items-start gap-2 rounded-xl px-3 py-2 text-xs animate-fade-up"
          style={{
            background: 'rgba(244,63,94,0.08)',
            border: '1px solid rgba(244,63,94,0.2)',
            color: '#fda4af',
          }}
        >
          <AlertCircle size={12} className="mt-0.5 shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}
    </div>
  );
}
