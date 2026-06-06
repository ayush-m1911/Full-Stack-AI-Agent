import { useRef, useState, useCallback } from 'react';
import { Upload, X, FileText, ImageIcon, FileSpreadsheet } from 'lucide-react';
import type { UploadedFile } from '../../types';
import { clsx } from 'clsx';

interface Props {
  onUpload: (files: File[]) => void;
  uploadedFiles: UploadedFile[];
  onRemove: (id: string) => void;
  isUploading: boolean;
}

const ICON_MAP: Record<string, React.ReactNode> = {
  'application/pdf': <FileText size={12} />,
  'text/plain': <FileText size={12} />,
  'text/csv': <FileSpreadsheet size={12} />,
  'image/png': <ImageIcon size={12} />,
  'image/jpeg': <ImageIcon size={12} />,
};

function getIcon(type: string) {
  return ICON_MAP[type] ?? <FileText size={12} />;
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function FileUpload({ onUpload, uploadedFiles, onRemove, isUploading }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      onUpload(Array.from(files));
    },
    [onUpload],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles],
  );

  return (
    <div className="space-y-2">
      { }
      <div
        className={clsx(
          'relative flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed cursor-pointer transition-all duration-200',
          dragging ? 'border-blue-500 bg-blue-500/10' : 'border-[var(--color-border)] hover:border-[var(--color-brand-500)] hover:bg-[rgba(59,130,246,0.05)]',
        )}
        style={{ padding: '20px 12px' }}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <div
          className="flex items-center justify-center w-10 h-10 rounded-xl transition-all"
          style={{
            background: dragging
              ? 'rgba(59,130,246,0.2)'
              : 'var(--color-bg-elevated)',
            border: '1px solid var(--color-border)',
          }}
        >
          {isUploading ? (
            <div
              className="w-5 h-5 rounded-full border-2 border-transparent animate-spin-slow"
              style={{ borderTopColor: 'var(--color-brand-400)' }}
            />
          ) : (
            <Upload size={18} style={{ color: 'var(--color-brand-400)' }} />
          )}
        </div>
        <div className="text-center">
          <p className="text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>
            {isUploading ? 'Uploading…' : 'Drop files or click to browse'}
          </p>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
            PDF, CSV, TXT, XLSX, PNG, JPG · max 50 MB
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
          accept=".pdf,.txt,.csv,.xlsx,.xls,.png,.jpg,.jpeg,.json"
        />
      </div>

      { }
      {uploadedFiles.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {uploadedFiles.map((f) => (
            <div
              key={f.id}
              className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium animate-fade-in"
              style={{
                background: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border)',
                color: 'var(--color-text-secondary)',
                maxWidth: '180px',
              }}
            >
              <span style={{ color: 'var(--color-brand-400)' }}>
                {getIcon(f.content_type)}
              </span>
              <span className="truncate flex-1">{f.original_name}</span>
              <span style={{ color: 'var(--color-text-muted)' }}>
                {formatSize(f.size_bytes)}
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); onRemove(f.id); }}
                className="ml-0.5 rounded transition-colors hover:text-red-400"
                style={{ color: 'var(--color-text-muted)' }}
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
