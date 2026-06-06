import { useState } from 'react';
import {
  Image as ImageIcon,
  X,
  ChevronDown,
  ChevronRight,
  Code2,
  FileText,
  Layers,
  AlertTriangle,
  ZoomIn,
} from 'lucide-react';
import type { ImageContentType, ImageExtractionResult } from '../../types';
import { ImageDropZone } from './ImageDropZone';

interface Props {
  imageResult: ImageExtractionResult | null;
  previewUrl: string | null;
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  onUpload: (file: File) => Promise<void>;
  onClear: () => void;
}



const CONTENT_CONFIG: Record<ImageContentType, { label: string; color: string; bg: string; icon: React.ReactNode }> = {
  code: {
    label: 'Source Code',
    color: '#10b981',
    bg: 'rgba(16,185,129,0.12)',
    icon: <Code2 size={11} />,
  },
  text: {
    label: 'Plain Text',
    color: '#60a5fa',
    bg: 'rgba(96,165,250,0.12)',
    icon: <FileText size={11} />,
  },
  mixed: {
    label: 'Code + Text',
    color: '#a78bfa',
    bg: 'rgba(167,139,250,0.12)',
    icon: <Layers size={11} />,
  },
  empty: {
    label: 'No Text Found',
    color: '#94a3b8',
    bg: 'rgba(148,163,184,0.12)',
    icon: <ImageIcon size={11} />,
  },
};

function ContentBadge({ type }: { type: ImageContentType }) {
  const cfg = CONTENT_CONFIG[type];
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full text-[10px] font-semibold px-2 py-0.5"
      style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}22` }}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

function LangBadge({ lang }: { lang: string }) {
  return (
    <span
      className="inline-flex items-center rounded-full text-[10px] font-mono font-semibold px-2 py-0.5"
      style={{
        background: 'rgba(59,130,246,0.1)',
        color: '#93c5fd',
        border: '1px solid rgba(59,130,246,0.2)',
      }}
    >
      {lang}
    </span>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 75 ? '#10b981' : pct >= 50 ? '#f59e0b' : '#f43f5e';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--color-border)' }}>
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-[10px] font-semibold tabular-nums" style={{ color, minWidth: '30px', textAlign: 'right' }}>
        {pct}%
      </span>
    </div>
  );
}



function Lightbox({ url, onClose }: { url: string; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center animate-fade-in"
      style={{ background: 'rgba(0,0,0,0.85)' }}
      onClick={onClose}
    >
      <img
        src={url}
        alt="Full preview"
        className="max-w-[90vw] max-h-[90vh] rounded-xl object-contain shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      />
      <button
        className="absolute top-4 right-4 p-2 rounded-xl"
        style={{ background: 'rgba(255,255,255,0.1)', color: '#fff' }}
        onClick={onClose}
      >
        <X size={18} />
      </button>
    </div>
  );
}



export function ImagePanel({
  imageResult, previewUrl, isUploading, uploadProgress, uploadError, onUpload, onClear,
}: Props) {
  const [textExpanded, setTextExpanded] = useState(false);
  const [lightboxOpen, setLightboxOpen] = useState(false);

  return (
    <>
      {lightboxOpen && previewUrl && (
        <Lightbox url={previewUrl} onClose={() => setLightboxOpen(false)} />
      )}

      <div className="panel h-full flex flex-col">
        { }
        <div className="panel-header">
          <ImageIcon size={14} style={{ color: '#a78bfa' }} />
          <span>Image Analysis</span>
          {imageResult && (
            <span
              className="text-[10px] rounded-full px-2 py-0.5 ml-1"
              style={{ background: 'rgba(139,92,246,0.1)', color: '#a78bfa' }}
            >
              {imageResult.width}×{imageResult.height}
            </span>
          )}
          {imageResult && (
            <button
              onClick={onClear}
              className="ml-auto p-1 rounded-lg transition-colors"
              style={{ color: 'var(--color-text-muted)' }}
              title="Remove image"
            >
              <X size={13} />
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          { }
          <ImageDropZone
            onUpload={onUpload}
            isUploading={isUploading}
            uploadProgress={uploadProgress}
            uploadError={uploadError}
            hasResult={!!imageResult}
          />

          { }
          {imageResult && (
            <div className="space-y-2.5 animate-fade-up">
              { }
              {previewUrl && (
                <div className="relative group rounded-xl overflow-hidden cursor-pointer"
                  style={{ border: '1px solid var(--color-border)' }}
                  onClick={() => setLightboxOpen(true)}
                >
                  <img
                    src={previewUrl}
                    alt={imageResult.original_name}
                    className="w-full object-cover"
                    style={{ maxHeight: '120px', objectFit: 'cover' }}
                  />
                  <div
                    className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    style={{ background: 'rgba(0,0,0,0.45)' }}
                  >
                    <ZoomIn size={20} color="#fff" />
                  </div>
                </div>
              )}

              { }
              <p
                className="text-xs font-medium truncate"
                style={{ color: 'var(--color-text-secondary)' }}
                title={imageResult.original_name}
              >
                {imageResult.original_name}
              </p>

              { }
              <div className="flex items-center gap-1.5 flex-wrap">
                <ContentBadge type={imageResult.content_type} />
                {imageResult.detected_language && (
                  <LangBadge lang={imageResult.detected_language} />
                )}
              </div>

              { }
              {imageResult.content_type !== 'empty' && (
                <div className="space-y-1">
                  <p className="text-[10px] font-medium" style={{ color: 'var(--color-text-muted)' }}>
                    OCR confidence
                  </p>
                  <ConfidenceBar value={imageResult.ocr_confidence} />
                </div>
              )}

              { }
              <div className="flex items-center gap-3 text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                <span>{imageResult.char_count.toLocaleString()} chars</span>
                <span>{imageResult.width}×{imageResult.height}px</span>
              </div>

              { }
              {imageResult.warning && (
                <div
                  className="flex items-start gap-1.5 rounded-lg px-2.5 py-2 text-[10px]"
                  style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)', color: '#fbbf24' }}
                >
                  <AlertTriangle size={10} className="mt-0.5 shrink-0" />
                  {imageResult.warning}
                </div>
              )}

              { }
              {imageResult.content_type !== 'empty' && (
                <div
                  className="flex items-center gap-2 rounded-xl px-3 py-2 text-[11px] font-medium"
                  style={{
                    background: 'linear-gradient(135deg, rgba(139,92,246,0.08), rgba(236,72,153,0.08))',
                    border: '1px solid rgba(139,92,246,0.15)',
                    color: '#a78bfa',
                  }}
                >
                  <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: '#a78bfa' }} />
                  {imageResult.content_type === 'code' || imageResult.content_type === 'mixed'
                    ? 'Code analysis active — ask about logic, bugs, complexity'
                    : 'Image context active — ask anything about this image'}
                </div>
              )}

              { }
              {imageResult.preview && (
                <div>
                  <button
                    className="flex items-center gap-1.5 text-[10px] font-medium mb-1.5 w-full"
                    style={{ color: 'var(--color-text-secondary)' }}
                    onClick={() => setTextExpanded((v) => !v)}
                  >
                    {textExpanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                    OCR extracted text
                  </button>
                  {textExpanded && (
                    <div
                      className="rounded-xl p-3 text-[11px] leading-relaxed overflow-y-auto animate-fade-in"
                      style={{
                        background: 'var(--color-bg-card)',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-text-muted)',
                        fontFamily: imageResult.content_type === 'code' ? 'monospace' : 'inherit',
                        whiteSpace: 'pre-wrap',
                        maxHeight: '180px',
                        wordBreak: 'break-word',
                      }}
                    >
                      {imageResult.preview}
                      {imageResult.char_count > 500 && (
                        <span style={{ opacity: 0.5 }}>
                          {'\n\n'}…{(imageResult.char_count - 500).toLocaleString()} more chars
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
