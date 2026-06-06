import { useState } from 'react';
import {
  Mic,
  X,
  ChevronDown,
  ChevronRight,
  AlignLeft,
  Layers,
  AlertTriangle,
  Clock,
  FileText,
} from 'lucide-react';
import type { AudioTranscriptionResult } from '../../types';
import { AudioDropZone } from './AudioDropZone';

interface Props {
  audioResult: AudioTranscriptionResult | null;
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  stage: 'idle' | 'uploading' | 'transcribing' | 'summarizing';
  onUpload: (file: File) => Promise<void>;
  onClear: () => void;
}



function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function SummaryTab({
  label,
  active,
  onClick,
}: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="text-[10px] font-semibold px-2.5 py-1 rounded-lg transition-all"
      style={{
        background: active ? 'rgba(245,158,11,0.15)' : 'transparent',
        color: active ? '#fbbf24' : 'var(--color-text-muted)',
        border: active ? '1px solid rgba(245,158,11,0.2)' : '1px solid transparent',
      }}
    >
      {label}
    </button>
  );
}



export function AudioPanel({
  audioResult, isUploading, uploadProgress, uploadError, stage, onUpload, onClear,
}: Props) {
  const [activeTab, setActiveTab] = useState<'one_line' | 'bullets' | 'paragraph'>('one_line');
  const [transcriptExpanded, setTranscriptExpanded] = useState(false);

  return (
    <div className="panel h-full flex flex-col">
      { }
      <div className="panel-header">
        <Mic size={14} style={{ color: '#fbbf24' }} />
        <span>Audio Transcription</span>
        {audioResult && (
          <span
            className="text-[10px] rounded-full px-2 py-0.5 ml-1"
            style={{ background: 'rgba(245,158,11,0.1)', color: '#fbbf24' }}
          >
            {formatDuration(audioResult.duration_seconds)}
          </span>
        )}
        {audioResult && (
          <button
            onClick={onClear}
            className="ml-auto p-1 rounded-lg"
            style={{ color: 'var(--color-text-muted)' }}
            title="Remove audio"
          >
            <X size={13} />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        { }
        <AudioDropZone
          onUpload={onUpload}
          isUploading={isUploading}
          uploadProgress={uploadProgress}
          uploadError={uploadError}
          stage={stage}
          hasResult={!!audioResult}
        />

        { }
        {audioResult && (
          <div className="space-y-2.5 animate-fade-up">
            { }
            <p
              className="text-xs font-medium truncate"
              style={{ color: 'var(--color-text-secondary)' }}
              title={audioResult.original_name}
            >
              {audioResult.original_name}
            </p>

            { }
            <div
              className="flex items-center gap-3 text-[10px] flex-wrap"
              style={{ color: 'var(--color-text-muted)' }}
            >
              <span className="flex items-center gap-1">
                <Clock size={9} />
                {formatDuration(audioResult.duration_seconds)}
              </span>
              <span className="flex items-center gap-1">
                <AlignLeft size={9} />
                {audioResult.word_count.toLocaleString()} words
              </span>
              {audioResult.language && (
                <span
                  className="rounded-full px-1.5 py-0.5 font-semibold text-[9px]"
                  style={{
                    background: 'rgba(96,165,250,0.12)',
                    color: '#60a5fa',
                    border: '1px solid rgba(96,165,250,0.2)',
                  }}
                >
                  {audioResult.language}
                </span>
              )}
              <span
                className="rounded-full px-1.5 py-0.5 font-semibold text-[9px]"
                style={{
                  background: 'rgba(245,158,11,0.1)',
                  color: '#fbbf24',
                  border: '1px solid rgba(245,158,11,0.15)',
                }}
              >
                whisper/{audioResult.whisper_model}
              </span>
            </div>

            { }
            {audioResult.warning && (
              <div
                className="flex items-start gap-1.5 rounded-lg px-2.5 py-2 text-[10px]"
                style={{
                  background: 'rgba(245,158,11,0.08)',
                  border: '1px solid rgba(245,158,11,0.2)',
                  color: '#fbbf24',
                }}
              >
                <AlertTriangle size={10} className="mt-0.5 shrink-0" />
                {audioResult.warning}
              </div>
            )}

            { }
            {audioResult.word_count > 0 && (
              <div
                className="flex items-center gap-2 rounded-xl px-3 py-2 text-[11px] font-medium"
                style={{
                  background: 'linear-gradient(135deg, rgba(245,158,11,0.08), rgba(239,68,68,0.08))',
                  border: '1px solid rgba(245,158,11,0.15)',
                  color: '#fbbf24',
                }}
              >
                <span
                  className="w-1.5 h-1.5 rounded-full animate-pulse"
                  style={{ background: '#fbbf24' }}
                />
                Audio context active — ask anything about this recording
              </div>
            )}

            { }
            {audioResult.summaries && (
              <div>
                <div
                  className="flex items-center gap-1 mb-2"
                  style={{ borderBottom: '1px solid var(--color-border)' }}
                >
                  <Layers size={10} style={{ color: 'var(--color-text-muted)' }} />
                  <span className="text-[10px] font-medium mr-2" style={{ color: 'var(--color-text-muted)' }}>
                    Summaries
                  </span>
                  <SummaryTab label="1-line" active={activeTab === 'one_line'} onClick={() => setActiveTab('one_line')} />
                  <SummaryTab label="Bullets" active={activeTab === 'bullets'} onClick={() => setActiveTab('bullets')} />
                  <SummaryTab label="Paragraph" active={activeTab === 'paragraph'} onClick={() => setActiveTab('paragraph')} />
                </div>

                <div
                  className="rounded-xl p-3 text-xs leading-relaxed"
                  style={{
                    background: 'var(--color-bg-card)',
                    border: '1px solid var(--color-border)',
                    color: 'var(--color-text-secondary)',
                    minHeight: '64px',
                  }}
                >
                  {activeTab === 'one_line' && (
                    <p className="italic">&ldquo;{audioResult.summaries.one_line}&rdquo;</p>
                  )}
                  {activeTab === 'bullets' && (
                    <ul className="space-y-1.5">
                      {audioResult.summaries.bullets.map((b, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span style={{ color: '#fbbf24', flexShrink: 0 }}>•</span>
                          <span>{b}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {activeTab === 'paragraph' && (
                    <p>{audioResult.summaries.paragraph}</p>
                  )}
                </div>
              </div>
            )}

            { }
            {audioResult.preview && (
              <div>
                <button
                  className="flex items-center gap-1.5 text-[10px] font-medium mb-1.5 w-full"
                  style={{ color: 'var(--color-text-secondary)' }}
                  onClick={() => setTranscriptExpanded((v) => !v)}
                >
                  {transcriptExpanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                  <FileText size={10} />
                  Transcript
                </button>
                {transcriptExpanded && (
                  <div
                    className="rounded-xl p-3 text-[11px] leading-relaxed overflow-y-auto animate-fade-in"
                    style={{
                      background: 'var(--color-bg-card)',
                      border: '1px solid var(--color-border)',
                      color: 'var(--color-text-muted)',
                      whiteSpace: 'pre-wrap',
                      maxHeight: '180px',
                      wordBreak: 'break-word',
                    }}
                  >
                    {audioResult.preview}
                    {audioResult.char_count > 400 && (
                      <span style={{ opacity: 0.5 }}>
                        {'\n\n'}…{(audioResult.char_count - 400).toLocaleString()} more chars
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
