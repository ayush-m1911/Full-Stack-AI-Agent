import { useRef, useState } from 'react';
import { FileText, Image, Mic, X, Upload, Loader, AlertCircle, Layers } from 'lucide-react';
import type { AnalysisStage } from '../../hooks/useMultiAnalysis';

interface Props {
  pdfFiles: File[];
  imageFiles: File[];
  audioFiles: File[];
  isLoading: boolean;
  stage: AnalysisStage;
  progress: number;
  error: string | null;
  onAddFiles: (files: File[]) => void;
  onRemovePdf: (idx: number) => void;
  onRemoveImage: (idx: number) => void;
  onRemoveAudio: (idx: number) => void;
  onClearAll: () => void;
  onAnalyze: (query: string) => void;
}

const STAGE_LABELS: Record<AnalysisStage, string> = {
  idle: '',
  uploading: 'Uploading files…',
  extracting: 'Extracting content (PDF / OCR / Whisper)…',
  building_context: 'Building unified context…',
  detecting_intent: 'Detecting intent…',
  generating: 'Generating response…',
  done: 'Done',
  error: 'Error',
};

function FileChip({ name, color, onRemove }: { name: string; color: string; onRemove: () => void }) {
  return (
    <div
      className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-[11px] max-w-full"
      style={{ background: `${color}18`, border: `1px solid ${color}30`, color }}
    >
      <span className="truncate max-w-[120px]">{name}</span>
      <button onClick={onRemove} className="shrink-0 opacity-70 hover:opacity-100">
        <X size={10} />
      </button>
    </div>
  );
}

export function MultiInputPanel({
  pdfFiles, imageFiles, audioFiles,
  isLoading, stage, progress, error,
  onAddFiles, onRemovePdf, onRemoveImage, onRemoveAudio, onClearAll, onAnalyze,
}: Props) {
  const [query, setQuery] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const ACCEPTED = '.pdf,.png,.jpg,.jpeg,.webp,.mp3,.wav,.m4a,.ogg,.flac';
  const totalFiles = pdfFiles.length + imageFiles.length + audioFiles.length;

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    onAddFiles(Array.from(files));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleSubmit = () => {
    if (!query.trim() && totalFiles === 0) return;
    onAnalyze(query);
    setQuery('');
  };

  return (
    <div className="panel h-full flex flex-col">
      { }
      <div className="panel-header">
        <Layers size={14} style={{ color: '#818cf8' }} />
        <span>Multi-Input Analyzer</span>
        {totalFiles > 0 && (
          <span
            className="text-[10px] rounded-full px-2 py-0.5"
            style={{ background: 'rgba(129,140,248,0.12)', color: '#818cf8' }}
          >
            {totalFiles} file{totalFiles > 1 ? 's' : ''}
          </span>
        )}
        {(totalFiles > 0 || query) && !isLoading && (
          <button
            onClick={onClearAll}
            className="ml-auto p-1 rounded-lg text-xs"
            style={{ color: 'var(--color-text-muted)' }}
          >
            <X size={12} />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        { }
        <div
          className="relative rounded-2xl cursor-pointer transition-all duration-200"
          style={{
            border: `2px dashed ${isDragging ? '#818cf8' : 'var(--color-border)'}`,
            background: isDragging ? 'rgba(129,140,248,0.06)' : 'var(--color-bg-elevated)',
            padding: '16px 12px',
          }}
          onClick={() => !isLoading && inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            accept={ACCEPTED}
            className="sr-only"
            onChange={(e) => handleFiles(e.target.files)}
          />
          <div className="flex flex-col items-center gap-2 text-center">
            <div
              className="flex items-center justify-center w-10 h-10 rounded-xl"
              style={{
                background: 'linear-gradient(135deg, rgba(129,140,248,0.15), rgba(129,140,248,0.05))',
                border: '1px solid rgba(129,140,248,0.2)',
              }}
            >
              <Upload size={16} style={{ color: '#818cf8' }} />
            </div>
            <p className="text-xs font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              Drop any files here
            </p>
            <div className="flex items-center gap-3 text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
              <span className="flex items-center gap-1"><FileText size={9} /> PDFs</span>
              <span className="flex items-center gap-1"><Image size={9} /> Images</span>
              <span className="flex items-center gap-1"><Mic size={9} /> Audio</span>
            </div>
          </div>
        </div>

        { }
        {totalFiles > 0 && (
          <div className="space-y-2">
            {pdfFiles.length > 0 && (
              <div>
                <p className="text-[10px] font-medium mb-1 flex items-center gap-1"
                  style={{ color: '#f87171' }}>
                  <FileText size={9} /> PDFs ({pdfFiles.length})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {pdfFiles.map((f, i) => (
                    <FileChip key={i} name={f.name} color="#f87171"
                      onRemove={() => onRemovePdf(i)} />
                  ))}
                </div>
              </div>
            )}
            {imageFiles.length > 0 && (
              <div>
                <p className="text-[10px] font-medium mb-1 flex items-center gap-1"
                  style={{ color: '#a78bfa' }}>
                  <Image size={9} /> Images ({imageFiles.length})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {imageFiles.map((f, i) => (
                    <FileChip key={i} name={f.name} color="#a78bfa"
                      onRemove={() => onRemoveImage(i)} />
                  ))}
                </div>
              </div>
            )}
            {audioFiles.length > 0 && (
              <div>
                <p className="text-[10px] font-medium mb-1 flex items-center gap-1"
                  style={{ color: '#fbbf24' }}>
                  <Mic size={9} /> Audio ({audioFiles.length})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {audioFiles.map((f, i) => (
                    <FileChip key={i} name={f.name} color="#fbbf24"
                      onRemove={() => onRemoveAudio(i)} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        { }
        <div
          className="rounded-xl p-2.5"
          style={{
            background: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)',
          }}
        >
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              totalFiles > 0
                ? 'Ask anything about these files…'
                : 'Enter your query (attach files above for multi-modal analysis)…'
            }
            disabled={isLoading}
            rows={3}
            className="w-full resize-none outline-none text-xs leading-relaxed bg-transparent"
            style={{ color: 'var(--color-text-primary)', caretColor: '#818cf8' }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
            }}
          />
          <div className="flex justify-end mt-1.5">
            <button
              onClick={handleSubmit}
              disabled={isLoading || (!query.trim() && totalFiles === 0)}
              className="btn-primary"
              style={{ padding: '6px 14px', fontSize: '11px',
                background: isLoading || (!query.trim() && totalFiles === 0)
                  ? undefined
                  : 'linear-gradient(135deg, #818cf8, #6366f1)' }}
            >
              {isLoading ? <Loader size={12} className="animate-spin" /> : <Layers size={12} />}
              <span>{isLoading ? 'Analyzing…' : 'Analyze'}</span>
            </button>
          </div>
        </div>

        { }
        {isLoading && (
          <div className="space-y-1.5 animate-fade-up">
            <p className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
              {STAGE_LABELS[stage]}
            </p>
            <div className="w-full h-1.5 rounded-full overflow-hidden"
              style={{ background: 'var(--color-border)' }}>
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${progress}%`,
                  background: 'linear-gradient(90deg, #818cf8, #6366f1)',
                }}
              />
            </div>
          </div>
        )}

        { }
        {error && (
          <div
            className="flex items-start gap-2 rounded-xl px-3 py-2 text-xs animate-fade-up"
            style={{
              background: 'rgba(244,63,94,0.08)',
              border: '1px solid rgba(244,63,94,0.2)',
              color: '#fda4af',
            }}
          >
            <AlertCircle size={12} className="mt-0.5 shrink-0" />
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
