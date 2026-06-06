import type { IntentType } from '../../types';

const INTENT_CONFIG: Record<
  IntentType,
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
  qa: {
    label: 'Q&A',
    color: '#10b981',
    bg: 'rgba(16,185,129,0.12)',
    emoji: '❓',
  },
  explain: {
    label: 'Explain',
    color: '#8b5cf6',
    bg: 'rgba(139,92,246,0.12)',
    emoji: '💡',
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

interface Props {
  intent: IntentType;
  size?: 'sm' | 'md';
}

export function IntentBadge({ intent, size = 'sm' }: Props) {
  const cfg = INTENT_CONFIG[intent] ?? INTENT_CONFIG.unknown;
  const padding = size === 'md' ? '5px 12px' : '3px 8px';
  const fontSize = size === 'md' ? '12px' : '10px';

  return (
    <span
      className="inline-flex items-center gap-1 rounded-full font-semibold select-none"
      style={{
        background: cfg.bg,
        color: cfg.color,
        border: `1px solid ${cfg.color}30`,
        padding,
        fontSize,
        letterSpacing: '0.04em',
      }}
    >
      <span>{cfg.emoji}</span>
      <span>{cfg.label}</span>
    </span>
  );
}
