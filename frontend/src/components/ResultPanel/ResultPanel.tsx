import { BarChart3, Copy, Check, FileText } from 'lucide-react';
import { useState } from 'react';

interface Props {
  result: string | null;
}

function countWords(text: any): number {
  if (typeof text !== 'string') return 0;
  return text.trim().split(/\s+/).filter(Boolean).length;
}

export function ResultPanel({ result }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!result || typeof result !== 'string') return;
    await navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const hasResult = result != null && typeof result === 'string' && result.trim().length > 0;

  return (
    <div className="panel h-full flex flex-col">
      <div className="panel-header">
        <BarChart3 size={14} style={{ color: 'var(--color-accent-cyan)' }} />
        <span>Final Response</span>
        {hasResult && (
          <>
            <span
              className="text-[10px] rounded-full px-2 py-0.5 ml-1"
              style={{
                background: 'rgba(6,182,212,0.12)',
                color: 'var(--color-accent-cyan)',
              }}
            >
              {countWords(result)} words
            </span>
            <button
              onClick={handleCopy}
              className="ml-auto btn-ghost"
              style={{ padding: '4px 10px', fontSize: '11px' }}
              title="Copy result"
            >
              {copied ? (
                <>
                  <Check size={11} style={{ color: 'var(--color-accent-emerald)' }} />
                  Copied
                </>
              ) : (
                <>
                  <Copy size={11} />
                  Copy
                </>
              )}
            </button>
          </>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        {!hasResult ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 py-6">
            <div
              className="flex items-center justify-center w-10 h-10 rounded-xl"
              style={{
                background: 'rgba(6,182,212,0.08)',
                border: '1px solid rgba(6,182,212,0.15)',
              }}
            >
              <FileText size={18} style={{ color: 'var(--color-accent-cyan)' }} />
            </div>
            <p className="text-xs text-center" style={{ color: 'var(--color-text-muted)' }}>
              No response available.
            </p>
          </div>
        ) : (
          <div
            className="rounded-xl p-3 text-sm leading-relaxed animate-fade-up"
            style={{
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-secondary)',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: 'var(--font-sans)',
            }}
          >
            {result}
          </div>
        )}
      </div>
    </div>
  );
}
