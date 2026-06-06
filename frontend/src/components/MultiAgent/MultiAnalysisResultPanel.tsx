import { useState } from 'react';
import {
  BarChart3, Copy, Check, GitBranch, ChevronDown, ChevronRight,
  Clock, AlertCircle, CheckCircle2, Loader, HelpCircle, FileText
} from 'lucide-react';
import type { MultiAnalysisResult, MultiIntentType } from '../../types';

interface Props {
  result: MultiAnalysisResult | null;
}

const MULTI_INTENT_CONFIG: Record<
  MultiIntentType,
  { label: string; color: string; bg: string; emoji: string }
> = {
  summarize: {
    label: 'Summarize',
    color: '#60a5fa',
    bg: 'rgba(59,130,246,0.12)',
    emoji: '📝',
  },
  sentiment: {
    label: 'Sentiment',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.12)',
    emoji: '🎭',
  },
  question_answering: {
    label: 'Q&A',
    color: '#10b981',
    bg: 'rgba(16,185,129,0.12)',
    emoji: '❓',
  },
  code_explanation: {
    label: 'Code Explain',
    color: '#a78bfa',
    bg: 'rgba(167,139,250,0.12)',
    emoji: '💻',
  },
  comparison: {
    label: 'Comparison',
    color: '#ec4899',
    bg: 'rgba(236,72,153,0.12)',
    emoji: '⚖️',
  },
  general_chat: {
    label: 'General Chat',
    color: '#14b8a6',
    bg: 'rgba(20,184,166,0.12)',
    emoji: '💬',
  },
  followup: {
    label: 'Follow-up',
    color: '#f43f5e',
    bg: 'rgba(244,63,94,0.12)',
    emoji: '🔄',
  },
  unknown: {
    label: 'Unknown',
    color: '#6b7280',
    bg: 'rgba(107,114,128,0.12)',
    emoji: '❔',
  },
};

const STATUS_CONFIG: Record<
  'pending' | 'running' | 'success' | 'failed',
  { icon: React.ReactNode; color: string; bg: string }
> = {
  pending: {
    icon: <Clock size={13} />,
    color: 'var(--color-text-muted)',
    bg: 'rgba(75,85,99,0.15)',
  },
  running: {
    icon: <Loader size={13} className="animate-spin-slow" />,
    color: 'var(--color-brand-400)',
    bg: 'rgba(59,130,246,0.12)',
  },
  success: {
    icon: <CheckCircle2 size={13} />,
    color: 'var(--color-accent-emerald)',
    bg: 'rgba(16,185,129,0.12)',
  },
  failed: {
    icon: <AlertCircle size={13} />,
    color: 'var(--color-accent-rose)',
    bg: 'rgba(244,63,94,0.12)',
  },
};

function countWords(text: string): number {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

export function MultiAnalysisResultPanel({ result }: Props) {
  const [copied, setCopied] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  const handleCopy = async () => {
    if (!result?.result) return;
    await navigator.clipboard.writeText(result.result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleStep = (stepNumber: number) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(stepNumber)) {
        next.delete(stepNumber);
      } else {
        next.add(stepNumber);
      }
      return next;
    });
  };

  if (!result) {
    return (
      <div className="panel h-full flex flex-col">
        <div className="panel-header">
          <BarChart3 size={14} style={{ color: 'var(--color-accent-purple)' }} />
          <span>Multi-Agent Result</span>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center gap-3 py-10 px-4 text-center">
          <div
            className="flex items-center justify-center w-10 h-10 rounded-xl"
            style={{
              background: 'rgba(129,140,248,0.08)',
              border: '1px solid rgba(129,140,248,0.15)',
            }}
          >
            <FileText size={18} style={{ color: '#818cf8' }} />
          </div>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            Submit query and files using the Multi-Input Analyzer to see structured plan details and analysis output.
          </p>
        </div>
      </div>
    );
  }

  const wordCount = countWords(result.result || '');
  const intentConfig = MULTI_INTENT_CONFIG[result.detected_intent] || MULTI_INTENT_CONFIG.unknown;

  return (
    <div className="panel h-full flex flex-col">
      { }
      <div className="panel-header">
        <BarChart3 size={14} style={{ color: 'var(--color-accent-purple)' }} />
        <span>Multi-Agent Output</span>
        {wordCount > 0 && (
          <span
            className="text-[10px] rounded-full px-2 py-0.5 ml-1"
            style={{
              background: 'rgba(129,140,248,0.12)',
              color: '#818cf8',
            }}
          >
            {wordCount} words
          </span>
        )}

        { }
        {result.detected_intent && (
          <span
            className="inline-flex items-center gap-1 rounded-full font-semibold select-none ml-2"
            style={{
              background: intentConfig.bg,
              color: intentConfig.color,
              border: `1px solid ${intentConfig.color}30`,
              padding: '3px 8px',
              fontSize: '10px',
              letterSpacing: '0.04em',
            }}
          >
            <span>{intentConfig.emoji}</span>
            <span>{intentConfig.label}</span>
          </span>
        )}

        { }
        {result.result && (
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
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        { }
        {result.requires_clarification && result.clarification_question && (
          <div
            className="flex items-start gap-2.5 rounded-xl px-3 py-3 text-xs animate-fade-up"
            style={{
              background: 'rgba(245,158,11,0.08)',
              border: '1px solid rgba(245,158,11,0.2)',
              color: '#fbbf24',
            }}
          >
            <HelpCircle size={15} className="shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold">Clarification Needed:</span>
              <p className="leading-relaxed">{result.clarification_question}</p>
            </div>
          </div>
        )}

        { }
        {result.plan_trace && result.plan_trace.length > 0 && (
          <div className="space-y-2">
            <h4
              className="text-[10px] font-bold tracking-wider uppercase flex items-center gap-1.5"
              style={{ color: 'var(--color-text-muted)' }}
            >
              <GitBranch size={10} style={{ color: 'var(--color-accent-purple)' }} />
              Agent Execution Steps
            </h4>
            <div className="space-y-1.5">
              {result.plan_trace.map((step, idx) => {
                const cfg = STATUS_CONFIG[step.status];
                const isOpen = expandedSteps.has(step.step);

                return (
                  <div
                    key={`${step.step}-${step.status}-${idx}`}
                    className="rounded-xl overflow-hidden animate-fade-up"
                    style={{
                      background: cfg.bg,
                      border: `1px solid ${cfg.color}30`,
                      animationDelay: `${idx * 40}ms`,
                    }}
                  >
                    <button
                      className="w-full flex items-center gap-2 px-3 py-2 text-left"
                      onClick={() => step.detail && toggleStep(step.step)}
                      disabled={!step.detail}
                      style={{ cursor: step.detail ? 'pointer' : 'default' }}
                    >
                      <span style={{ color: cfg.color }}>{cfg.icon}</span>
                      <span
                        className="flex-1 text-[11px] font-semibold"
                        style={{ color: 'var(--color-text-primary)' }}
                      >
                        {step.step}. {step.tool}
                      </span>
                      {step.duration_ms != null && (
                        <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                          {step.duration_ms}ms
                        </span>
                      )}
                      {step.detail && (
                        <span style={{ color: 'var(--color-text-muted)' }} className="ml-1">
                          {isOpen ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                        </span>
                      )}
                    </button>
                    {isOpen && step.detail && (
                      <div
                        className="px-3 pb-2.5 text-[11px] leading-relaxed border-t border-dashed border-opacity-10 animate-fade-in pt-1.5"
                        style={{
                          color: 'var(--color-text-secondary)',
                          borderColor: cfg.color,
                        }}
                      >
                        {step.detail}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        { }
        {result.result && (
          <div className="space-y-2">
            <h4
              className="text-[10px] font-bold tracking-wider uppercase"
              style={{ color: 'var(--color-text-muted)' }}
            >
              Analysis Output
            </h4>
            <div
              className="rounded-xl p-3 text-xs leading-relaxed animate-fade-up"
              style={{
                background: 'var(--color-bg-card)',
                border: '1px solid var(--color-border)',
                color: 'var(--color-text-secondary)',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                fontFamily: 'var(--font-sans)',
              }}
            >
              {result.result}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
