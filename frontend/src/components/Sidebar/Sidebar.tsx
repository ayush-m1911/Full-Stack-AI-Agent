import { Bot, Zap, Sparkles } from 'lucide-react';

export function Sidebar() {
  return (
    <aside
      className="w-64 flex-shrink-0 flex flex-col"
      style={{
        background: 'var(--color-bg-surface)',
        borderRight: '1px solid var(--color-border-subtle)',
      }}
    >
      { }
      <div
        className="flex items-center gap-3 px-5 py-5"
        style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
      >
        <div
          className="flex items-center justify-center w-9 h-9 rounded-xl"
          style={{
            background: 'linear-gradient(135deg, var(--color-brand-500), var(--color-accent-purple))',
            boxShadow: '0 0 20px var(--color-brand-glow)',
          }}
        >
          <Bot size={18} color="white" />
        </div>
        <div>
          <div className="font-bold text-sm" style={{ color: 'var(--color-text-primary)' }}>
            Datasmith
          </div>
          <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            AI Agent
          </div>
        </div>
      </div>

      { }
      <nav className="flex-1 p-3 space-y-1">
        <NavItem icon={<Zap size={15} />} label="Chat" active />
        <NavItem icon={<Sparkles size={15} />} label="Traces" />
      </nav>

      { }
      <div className="p-4" style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
        <div className="flex items-center gap-2">
          <div className="status-dot" />
          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            Backend connected
          </span>
        </div>
      </div>
    </aside>
  );
}

function NavItem({
  icon,
  label,
  active = false,
}: {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
}) {
  return (
    <button
      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
      style={{
        background: active ? 'rgba(59,130,246,0.12)' : 'transparent',
        color: active ? 'var(--color-brand-400)' : 'var(--color-text-secondary)',
        border: active ? '1px solid rgba(59,130,246,0.2)' : '1px solid transparent',
      }}
      onMouseEnter={(e) => {
        if (!active) {
          (e.currentTarget as HTMLElement).style.background = 'var(--color-bg-elevated)';
          (e.currentTarget as HTMLElement).style.color = 'var(--color-text-primary)';
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          (e.currentTarget as HTMLElement).style.background = 'transparent';
          (e.currentTarget as HTMLElement).style.color = 'var(--color-text-secondary)';
        }
      }}
    >
      {icon}
      {label}
    </button>
  );
}
