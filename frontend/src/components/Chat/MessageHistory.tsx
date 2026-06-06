import { useRef, useEffect } from 'react';
import { MessageSquare, Bot, User, HelpCircle } from 'lucide-react';
import type { LocalMessage } from '../../types';
import { IntentBadge } from './IntentBadge';
import { clsx } from 'clsx';

interface Props {
  messages: LocalMessage[];
}

export function MessageHistory({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, messages[messages.length - 1]?.streamedContent]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8">
        <div
          className="flex items-center justify-center w-16 h-16 rounded-2xl"
          style={{
            background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15))',
            border: '1px solid rgba(59,130,246,0.2)',
          }}
        >
          <MessageSquare size={28} style={{ color: 'var(--color-brand-400)' }} />
        </div>
        <div className="text-center">
          <p className="font-semibold text-base mb-1" style={{ color: 'var(--color-text-primary)' }}>
            Start a conversation
          </p>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Ask the agent to <strong style={{ color: 'var(--color-brand-400)' }}>summarize</strong>,{' '}
            <strong style={{ color: '#f59e0b' }}>analyse sentiment</strong>,{' '}
            <strong style={{ color: '#10b981' }}>answer questions</strong>, or{' '}
            <strong style={{ color: '#8b5cf6' }}>explain</strong> any text.
          </p>
        </div>

        { }
        <div className="flex flex-wrap gap-2 justify-center mt-2">
          {[
            'Summarize this article for me',
            'What is the sentiment of this text?',
            'Explain this concept to me',
            'Answer my question about this',
          ].map((prompt) => (
            <span
              key={prompt}
              className="text-xs px-3 py-1.5 rounded-full cursor-default"
              style={{
                background: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border)',
                color: 'var(--color-text-secondary)',
              }}
            >
              {prompt}
            </span>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}



function MessageBubble({ message }: { message: LocalMessage }) {
  const isUser = message.role === 'user';
  const displayContent = message.isStreaming
    ? (message.streamedContent ?? '')
    : message.content;

  return (
    <div
      className={clsx(
        'flex gap-3 animate-fade-up',
        isUser ? 'flex-row-reverse' : 'flex-row',
      )}
    >
      { }
      <div
        className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full"
        style={{
          background: isUser
            ? 'linear-gradient(135deg, var(--color-accent-purple), var(--color-brand-500))'
            : message.isFollowup
            ? 'linear-gradient(135deg, #f43f5e, #f59e0b)'
            : 'linear-gradient(135deg, var(--color-accent-cyan), var(--color-accent-emerald))',
          boxShadow: isUser
            ? '0 0 12px rgba(139,92,246,0.4)'
            : '0 0 12px rgba(6,182,212,0.35)',
        }}
      >
        {isUser ? (
          <User size={14} color="white" />
        ) : message.isFollowup ? (
          <HelpCircle size={14} color="white" />
        ) : (
          <Bot size={14} color="white" />
        )}
      </div>

      { }
      <div className="max-w-[78%] flex flex-col gap-1.5">
        { }
        {!isUser && message.detectedIntent && message.detectedIntent !== 'followup' && (
          <div className={clsx('flex', isUser ? 'justify-end' : 'justify-start')}>
            <IntentBadge intent={message.detectedIntent} />
          </div>
        )}

        <div
          className="rounded-2xl px-4 py-3"
          style={
            isUser
              ? {
                  background: 'linear-gradient(135deg, var(--color-brand-600), var(--color-accent-purple))',
                  color: 'white',
                  borderBottomRightRadius: '4px',
                }
              : message.isFollowup
              ? {
                  background: 'rgba(244,63,94,0.08)',
                  border: '1px solid rgba(244,63,94,0.2)',
                  color: 'var(--color-text-primary)',
                  borderBottomLeftRadius: '4px',
                }
              : {
                  background: 'var(--color-bg-elevated)',
                  border: '1px solid var(--color-border-subtle)',
                  color: 'var(--color-text-primary)',
                  borderBottomLeftRadius: '4px',
                }
          }
        >
          {message.isStreaming && displayContent === '' ? (
             
            <span className="shimmer-text text-sm">Thinking…</span>
          ) : (
            <div className="text-sm leading-relaxed whitespace-pre-wrap">
              <MarkdownLite content={displayContent} />
              { }
              {message.isStreaming && displayContent.length > 0 && (
                <span
                  className="animate-blink inline-block w-0.5 h-3.5 ml-0.5 rounded-sm align-middle"
                  style={{ background: 'var(--color-brand-400)' }}
                />
              )}
            </div>
          )}

          <p
            className="text-xs mt-1.5"
            style={{ color: isUser ? 'rgba(255,255,255,0.6)' : 'var(--color-text-muted)' }}
          >
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        </div>
      </div>
    </div>
  );
}



function MarkdownLite({ content }: { content: string }) {
  if (!content) return null;

  
  const parts = content.split(/(\*\*[^*]+\*\*)/g);

  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={i} style={{ fontWeight: 700, color: 'inherit' }}>
              {part.slice(2, -2)}
            </strong>
          );
        }
        
        if (part.includes('\n•')) {
          const lines = part.split('\n');
          return (
            <span key={i}>
              {lines.map((line, j) =>
                line.startsWith('•') ? (
                  <span key={j} className="flex gap-2 mt-1">
                    <span style={{ color: 'var(--color-brand-400)' }}>•</span>
                    <span>{line.slice(1).trim()}</span>
                  </span>
                ) : (
                  <span key={j}>{line}{j < lines.length - 1 ? '\n' : ''}</span>
                ),
              )}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}
