import { useState } from 'react';
import { GitBranch, ChevronDown, ChevronRight, CheckCircle2, XCircle, Loader, Clock } from 'lucide-react';
import type { TraceStep, TraceStatus, IntentType } from '../../types';
import { IntentBadge } from '../Chat/IntentBadge';

interface Props {
  trace: TraceStep[];
  detectedIntent?: IntentType | null;
}

const STATUS_CONFIG: Record<
  TraceStatus,
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
  done: {
    icon: <CheckCircle2 size={13} />,
    color: 'var(--color-accent-emerald)',
    bg: 'rgba(16,185,129,0.12)',
  },
  error: {
    icon: <XCircle size={13} />,
    color: 'var(--color-accent-rose)',
    bg: 'rgba(244,63,94,0.12)',
  },
};

export function AgentTrace({ trace, detectedIntent }: Props) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggle = (step: number) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(step) ? next.delete(step) : next.add(step);
      return next;
    });

  if (!trace || !Array.isArray(trace)) {
    return (
      <div className="panel h-full flex flex-col items-center justify-center p-4">
        <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
          No trace available.
        </p>
      </div>
    );
  }

  const stepsCount = trace?.length || 0;

  return (
    <div className="panel h-full flex flex-col">
      <div className="panel-header">
        <GitBranch size={14} style={{ color: 'var(--color-accent-purple)' }} />
        <span>Agent Trace</span>
        {stepsCount > 0 && (
          <span
            className="text-xs rounded-full px-2 py-0.5"
            style={{
              background: 'rgba(139,92,246,0.15)',
              color: 'var(--color-accent-purple)',
            }}
          >
            {stepsCount} steps
          </span>
        )}
        { }
        {detectedIntent && (
          <span className="ml-auto">
            <IntentBadge intent={detectedIntent} />
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {stepsCount === 0 ? (
          <div className="flex items-center justify-center h-24">
            <p className="text-sm text-center" style={{ color: 'var(--color-text-muted)' }}>
              Trace will appear here after sending a message.
            </p>
          </div>
        ) : (
          trace.map((step, idx) => {
            if (!step) return null;
            const status = step?.status || 'pending';
            const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
            const stepNum = step?.step ?? idx + 1;
            const isOpen = expanded.has(stepNum);

            return (
              <div
                key={`${stepNum}-${status}-${idx}`}
                className="rounded-xl overflow-hidden animate-fade-up"
                style={{
                  background: cfg.bg,
                  border: `1px solid ${cfg.color}30`,
                  animationDelay: `${idx * 50}ms`,
                }}
              >
                <button
                  className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left"
                  onClick={() => step?.detail && toggle(stepNum)}
                  disabled={!step?.detail}
                >
                  <span style={{ color: cfg.color }}>{cfg.icon}</span>
                  <span
                    className="flex-1 text-xs font-semibold"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    {stepNum}. {step?.name || 'Step'}
                  </span>
                  {step?.duration_ms != null && (
                    <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                      {step?.duration_ms}ms
                    </span>
                  )}
                  {step?.detail && (
                    <span style={{ color: 'var(--color-text-muted)' }}>
                      {isOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    </span>
                  )}
                </button>
                {isOpen && step?.detail && (
                  <div
                    className="px-3 pb-2.5 text-xs animate-fade-in"
                    style={{ color: 'var(--color-text-secondary)' }}
                  >
                    {step?.detail}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
