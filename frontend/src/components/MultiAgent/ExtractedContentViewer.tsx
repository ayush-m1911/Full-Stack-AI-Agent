import { useState } from 'react';
import {
  FileText, Image, Mic, ChevronDown, ChevronRight,
  AlertTriangle, CheckCircle, XCircle, Eye, Globe
} from 'lucide-react';
import type { ExtractedSource } from '../../types';

interface Props {
  sources: ExtractedSource[];
}



const TYPE_CONFIG = {
  pdf:   { icon: FileText, color: '#f87171', label: 'PDF' },
  image: { icon: Image,    color: '#a78bfa', label: 'Image OCR' },
  audio: { icon: Mic,      color: '#fbbf24', label: 'Transcript' },
  text:  { icon: Eye,      color: '#60a5fa', label: 'Query' },
  url:   { icon: Globe,    color: '#34d399', label: 'Web Content' },
};



function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? '#34d399' : pct >= 50 ? '#fbbf24' : '#f87171';
  return (
    <span
      className="text-[9px] font-bold rounded-full px-1.5 py-0.5"
      style={{ background: `${color}18`, color, border: `1px solid ${color}30` }}
    >
      {pct}%
    </span>
  );
}



function SourceSection({ source }: { source: ExtractedSource }) {
  const [expanded, setExpanded] = useState(false);
  const cfg = TYPE_CONFIG[source.source_type] ?? TYPE_CONFIG.text;
  const Icon = cfg.icon;

  const hasContent = source.extracted_text.trim().length > 0;
  const preview = source.extracted_text.slice(0, 600);
  const hasMore = source.extracted_text.length > 600;

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{
        background: 'var(--color-bg-card)',
        border: `1px solid ${cfg.color}25`,
      }}
    >
      { }
      <button
        className="w-full flex items-center gap-2 px-3 py-2.5 text-left"
        onClick={() => hasContent && setExpanded((v) => !v)}
        style={{ cursor: hasContent ? 'pointer' : 'default' }}
      >
        <Icon size={11} style={{ color: cfg.color, flexShrink: 0 }} />
        <span
          className="flex-1 text-[11px] font-semibold truncate"
          style={{ color: 'var(--color-text-primary)' }}
          title={source.filename}
        >
          {source.filename || cfg.label}
        </span>

        { }
        {source.status === 'success' && <CheckCircle size={11} style={{ color: '#34d399' }} />}
        {source.status === 'empty'   && <AlertTriangle size={11} style={{ color: '#fbbf24' }} />}
        {source.status === 'failed'  && <XCircle size={11} style={{ color: '#f87171' }} />}

        { }
        {source.status === 'success' && source.confidence > 0 && (
          <ConfidenceBadge value={source.confidence} />
        )}

        { }
        {hasContent && (
          <span style={{ color: 'var(--color-text-muted)' }}>
            {expanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
          </span>
        )}
      </button>

      { }
      {source.metadata && Object.keys(source.metadata).length > 0 && (
        <div
          className="flex flex-wrap items-center gap-3 px-3 pb-1.5 text-[10px]"
          style={{ color: 'var(--color-text-muted)' }}
        >
          {source.source_type === 'pdf' && source.metadata.page_count != null && (
            <span>{String(source.metadata.page_count)} pages</span>
          )}
          {source.metadata.char_count != null && (
            <span>{Number(source.metadata.char_count).toLocaleString()} chars</span>
          )}
          {source.metadata.content_type != null && (
            <span
              className="rounded-full px-1.5 py-0.5 font-semibold text-[9px]"
              style={{ background: 'rgba(167,139,250,0.1)', color: '#a78bfa' }}
            >
              {String(source.metadata.content_type)}
            </span>
          )}
          {source.metadata.detected_language != null && (
            <span
              className="rounded-full px-1.5 py-0.5 font-semibold text-[9px]"
              style={{ background: 'rgba(96,165,250,0.1)', color: '#60a5fa' }}
            >
              {String(source.metadata.detected_language)}
            </span>
          )}
          {source.metadata.duration_seconds != null && (
            <span>{Math.round(Number(source.metadata.duration_seconds))}s</span>
          )}
          {source.metadata.language != null && source.source_type === 'audio' && (
            <span
              className="rounded-full px-1.5 py-0.5 font-semibold text-[9px]"
              style={{ background: 'rgba(251,191,36,0.1)', color: '#fbbf24' }}
            >
              {String(source.metadata.language)}
            </span>
          )}
          {source.metadata.duration_ms != null && (
            <span className="ml-auto">{Number(source.metadata.duration_ms)}ms</span>
          )}
        </div>
      )}

      { }
      {source.warning && (
        <div
          className="mx-3 mb-2 flex items-start gap-1.5 rounded-lg px-2.5 py-1.5 text-[10px]"
          style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)', color: '#fbbf24' }}
        >
          <AlertTriangle size={9} className="mt-0.5 shrink-0" />
          {source.warning}
        </div>
      )}

      { }
      {expanded && hasContent && (
        <div
          className="mx-3 mb-3 rounded-lg p-3 text-[11px] leading-relaxed overflow-y-auto animate-fade-in"
          style={{
            background: 'var(--color-bg-elevated)',
            border: '1px solid var(--color-border)',
            color: 'var(--color-text-secondary)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            maxHeight: '200px',
          }}
        >
          {preview}
          {hasMore && (
            <span style={{ opacity: 0.5 }}>
              {'\n…'}
              {(source.extracted_text.length - 600).toLocaleString()} more chars
            </span>
          )}
        </div>
      )}
    </div>
  );
}



export function ExtractedContentViewer({ sources }: Props) {
  
  const displaySources = sources.filter(
    (s) => s.source_type !== 'text' || s.status === 'failed',
  );

  if (displaySources.length === 0) return null;

  const successCount = displaySources.filter((s) => s.status === 'success').length;
  const failedCount  = displaySources.filter((s) => s.status === 'failed').length;

  return (
    <div className="panel h-full flex flex-col">
      <div className="panel-header">
        <Eye size={14} style={{ color: '#60a5fa' }} />
        <span>Extracted Content</span>
        <span
          className="text-[10px] rounded-full px-2 py-0.5"
          style={{ background: 'rgba(52,211,153,0.12)', color: '#34d399' }}
        >
          {successCount} ok
        </span>
        {failedCount > 0 && (
          <span
            className="text-[10px] rounded-full px-2 py-0.5"
            style={{ background: 'rgba(244,63,94,0.12)', color: '#f87171' }}
          >
            {failedCount} failed
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {displaySources.map((source, i) => (
          <SourceSection key={`${source.source_type}-${source.filename}-${i}`} source={source} />
        ))}
      </div>
    </div>
  );
}
