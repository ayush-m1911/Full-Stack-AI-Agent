import { useRef, useState } from 'react';
import { Image as ImageIcon, AlertCircle, Loader } from 'lucide-react';

interface Props {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  hasResult: boolean;
}

const ACCEPTED = '.png,.jpg,.jpeg,.webp,.bmp,image/png,image/jpeg,image/webp,image/bmp';

export function ImageDropZone({ onUpload, isUploading, uploadProgress, uploadError, hasResult }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = (file: File | undefined) => {
    if (!file) return;
    if (!file.type.startsWith('image/') && !file.name.match(/\.(png|jpg|jpeg|webp|bmp)$/i)) return;
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
        border: `2px dashed ${isDragging ? '#8b5cf6' : 'var(--color-border)'}`,
        background: isDragging ? 'rgba(139,92,246,0.06)' : 'var(--color-bg-elevated)',
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
            <Loader size={22} className="animate-spin" style={{ color: '#a78bfa' }} />
            <p className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>
              Running EasyOCR…
            </p>
            <div className="w-full h-1 rounded-full overflow-hidden" style={{ background: 'var(--color-border)' }}>
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{
                  width: `${uploadProgress}%`,
                  background: 'linear-gradient(90deg, #8b5cf6, #ec4899)',
                }}
              />
            </div>
            <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
              First run downloads model weights (~100 MB)
            </p>
          </>
        ) : (
          <>
            <div
              className="flex items-center justify-center w-10 h-10 rounded-xl"
              style={{
                background: 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(139,92,246,0.05))',
                border: '1px solid rgba(139,92,246,0.2)',
              }}
            >
              <ImageIcon size={18} style={{ color: '#a78bfa' }} />
            </div>
            <p className="text-xs font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              Drop an image here
            </p>
            <p className="text-[11px]" style={{ color: 'var(--color-text-muted)' }}>
              PNG · JPG · WEBP · BMP — up to 20 MB
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
