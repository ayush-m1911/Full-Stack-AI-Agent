import { useState } from 'react';
import {
  FileText,
  X,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Eye,
} from 'lucide-react';
import type { PDFExtractionResult, PDFMethod } from '../../types';
import { PDFDropZone } from './PDFDropZone';

interface Props {
  pdfResult: PDFExtractionResult | null;
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  onUpload: (file: File) => Promise<void>;
  onClear: () => void;
}



const METHOD_CONFIG: Record<PDFMethod, { label: string; color: string; bg: string; icon: React.ReactNode }> = {
  pymupdf: {
    label: 'PyMuPDF',
    color: '#10b981',
    bg: 'rgba(16,185,129,0.12)',
    icon: <CheckCircle2 size={11} />,
  },
  ocr: {
    label: 'OCR (Tesseract)',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.12)',
    icon: <Eye size={11} />,
  },
  failed: {
    label: 'Extraction Failed',
    color: '#f43f5e',
    bg: 'rgba(244,63,94,0.12)',
    icon: <XCircle size={11} />,
  },
};

function MethodBadge({ method }: { method: PDFMethod }) {
  const cfg = METHOD_CONFIG[method];
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full text-[10px] font-semibold px-2 py-0.5"
      style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}25` }}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}



function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80 ? '#10b981' :
    pct >= 55 ? '#f59e0b' :
    '#f43f5e';

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



export function PDFPanel({ pdfResult, isUploading, uploadProgress, uploadError, onUpload, onClear }: Props) {
  const [textExpanded, setTextExpanded] = useState(false);

  return (
    <div className="panel h-full flex flex-col">
      { }
      <div className="panel-header">
        <FileText size={14} style={{ color: '#f87171' }} />
        <span>PDF Document</span>
        {pdfResult && (
          <span
            className="text-[10px] rounded-full px-2 py-0.5 ml-1"
            style={{ background: 'rgba(239,68,68,0.1)', color: '#f87171' }}
          >
            {pdfResult.page_count}p
          </span>
        )}
        {pdfResult && (
          <button
            onClick={onClear}
            className="ml-auto p-1 rounded-lg transition-colors"
            style={{ color: 'var(--color-text-muted)' }}
            title="Remove PDF"
          >
            <X size={13} />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        { }
        <PDFDropZone
          onUpload={onUpload}
          isUploading={isUploading}
          uploadProgress={uploadProgress}
          uploadError={uploadError}
          hasResult={!!pdfResult}
        />

        { }
        {pdfResult && (
          <div className="space-y-2.5 animate-fade-up">
            { }
            <div
              className="flex items-center gap-2 rounded-xl px-3 py-2"
              style={{ background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)' }}
            >
              <FileText size={14} style={{ color: '#f87171', flexShrink: 0 }} />
              <span
                className="text-xs font-medium truncate"
                style={{ color: 'var(--color-text-primary)' }}
                title={pdfResult.original_name}
              >
                {pdfResult.original_name}
              </span>
            </div>

            { }
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <MethodBadge method={pdfResult.method} />
              <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                {pdfResult.char_count.toLocaleString()} chars
              </span>
            </div>

            { }
            {pdfResult.method !== 'failed' && (
              <div className="space-y-1">
                <p className="text-[10px] font-medium" style={{ color: 'var(--color-text-muted)' }}>
                  Extraction confidence
                </p>
                <ConfidenceBar value={pdfResult.confidence} />
              </div>
            )}

            { }
            {pdfResult.warning && (
              <div
                className="flex items-start gap-1.5 rounded-lg px-2.5 py-2 text-[10px]"
                style={{
                  background: 'rgba(245,158,11,0.08)',
                  border: '1px solid rgba(245,158,11,0.2)',
                  color: '#fbbf24',
                }}
              >
                <AlertTriangle size={10} className="mt-0.5 shrink-0" />
                {pdfResult.warning}
              </div>
            )}

            { }
            {pdfResult.method !== 'failed' && (
              <div
                className="flex items-center gap-2 rounded-xl px-3 py-2 text-[11px] font-medium"
                style={{
                  background: 'linear-gradient(135deg, rgba(59,130,246,0.08), rgba(139,92,246,0.08))',
                  border: '1px solid rgba(59,130,246,0.15)',
                  color: 'var(--color-brand-400)',
                }}
              >
                <span
                  className="w-1.5 h-1.5 rounded-full animate-pulse"
                  style={{ background: 'var(--color-brand-400)' }}
                />
                PDF context active — ask anything about this document
              </div>
            )}

            { }
            {pdfResult.preview && (
              <div>
                <button
                  className="flex items-center gap-1.5 text-[10px] font-medium mb-1.5 w-full"
                  style={{ color: 'var(--color-text-secondary)' }}
                  onClick={() => setTextExpanded((v) => !v)}
                >
                  {textExpanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                  Extracted text preview
                </button>
                {textExpanded && (
                  <div
                    className="rounded-xl p-3 text-[11px] leading-relaxed font-mono overflow-y-auto animate-fade-in"
                    style={{
                      background: 'var(--color-bg-card)',
                      border: '1px solid var(--color-border)',
                      color: 'var(--color-text-muted)',
                      whiteSpace: 'pre-wrap',
                      maxHeight: '200px',
                      wordBreak: 'break-word',
                    }}
                  >
                    {pdfResult.preview}
                    {pdfResult.char_count > 600 && (
                      <span style={{ color: 'var(--color-text-muted)', opacity: 0.6 }}>
                        {'\n\n'}…{(pdfResult.char_count - 600).toLocaleString()} more characters
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
  );
}
